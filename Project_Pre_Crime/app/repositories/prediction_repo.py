"""
PredictionRepository: Patrón Repositorio para acceso a datos de Predicciones.
Encapsula queries para historial de predicciones y análisis.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.database import db_manager

logger = logging.getLogger("PredictionRepository")

class PredictionRepository:
    """
    Maneja persistencia de predicciones en Neo4j.
    Registra todas las predicciones para auditoría y análisis histórico.
    """

    async def record_prediction(
        self, 
        citizen_id: int, 
        probability: float, 
        confidence: float,
        verdict: str
    ) -> Dict[str, Any]:
        """
        Registra una predicción en el grafo.
        Crea relación RED_BALL_PREDICTED con metadata.
        
        Args:
            citizen_id: ID del ciudadano analizado
            probability: Probabilidad predicha
            confidence: Confianza del modelo
            verdict: Veredicto (SAFE | WATCHLIST | INTERVENE)
            
        Returns:
            Datos de la predicción registrada
        """
        query = """
        MATCH (c:Citizen {id: $cid})
        CREATE (c)-[pred:RED_BALL_PREDICTED]->(c)
        SET pred.probability = $prob,
            pred.confidence = $conf,
            pred.verdict = $verdict,
            pred.timestamp = datetime(),
            pred.status = 'ACTIVE'
        RETURN pred.timestamp as timestamp,
               pred.probability as probability,
               pred.verdict as verdict
        """
        result = await db_manager.query(query, {
            "cid": citizen_id,
            "prob": probability,
            "conf": confidence,
            "verdict": verdict
        })
        
        if result:
            logger.info(f"🔴 Predicción registrada: Ciudadano #{citizen_id} → {verdict}")
            return result[0]
        return {}

    async def get_prediction_history(
        self, 
        citizen_id: int, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Obtiene historial de predicciones para un ciudadano.
        
        Args:
            citizen_id: ID del ciudadano
            limit: Máximo de registros
            
        Returns:
            Lista de predicciones previas
        """
        query = """
        MATCH (c:Citizen {id: $cid})-[pred:RED_BALL_PREDICTED]->(c)
        RETURN pred.timestamp as timestamp,
               pred.probability as probability,
               pred.confidence as confidence,
               pred.verdict as verdict,
               pred.status as status
        ORDER BY pred.timestamp DESC
        LIMIT $limit
        """
        return await db_manager.query(query, {"cid": citizen_id, "limit": limit})

    async def get_average_risk_by_period(
        self, 
        citizen_id: int,
        days: int = 30
    ) -> Optional[float]:
        """
        Calcula riesgo promedio para un ciudadano en un período.
        
        Args:
            citizen_id: ID del ciudadano
            days: Número de días retrospectivos
            
        Returns:
            Promedio de probabilidad o None
        """
        query = """
        MATCH (c:Citizen {id: $cid})-[pred:RED_BALL_PREDICTED]->(c)
        WHERE pred.timestamp > datetime() - duration({days: $days})
        RETURN avg(pred.probability) as avg_prob
        """
        result = await db_manager.query(query, {"cid": citizen_id, "days": days})
        if result and result[0].get("avg_prob"):
            return round(result[0]["avg_prob"], 3)
        return None

    async def get_interventions(
        self, 
        status: str = "ACTIVE",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las predicciones INTERVENE (Bolas Rojas) activas.
        
        Args:
            status: Estado de la predicción (ACTIVE | ARCHIVED)
            limit: Máximo de resultados
            
        Returns:
            Lista de intervenciones requeridas
        """
        query = """
        MATCH (c:Citizen)-[pred:RED_BALL_PREDICTED]->(c)
        WHERE pred.verdict = 'INTERVENE' AND pred.status = $status
        RETURN c.id as citizen_id,
               c.name as citizen_name,
               pred.probability as probability,
               pred.timestamp as predicted_at,
               pred.confidence as confidence
        ORDER BY pred.probability DESC, pred.timestamp DESC
        LIMIT $limit
        """
        return await db_manager.query(query, {"status": status, "limit": limit})

    async def count_verdicts_by_type(self, days: int = 7) -> Dict[str, int]:
        """
        Cuenta predicciones por veredicto en un período.
        
        Args:
            days: Número de días retrospectivos
            
        Returns:
            Diccionario con conteos {SAFE, WATCHLIST, INTERVENE}
        """
        query = """
        MATCH (c:Citizen)-[pred:RED_BALL_PREDICTED]->(c)
        WHERE pred.timestamp > datetime() - duration({days: $days})
        WITH pred.verdict as verdict, count(*) as count
        RETURN verdict, count
        """
        results = await db_manager.query(query, {"days": days})
        
        counts = {"SAFE": 0, "WATCHLIST": 0, "INTERVENE": 0}
        for r in results:
            verdict = r.get("verdict")
            if verdict in counts:
                counts[verdict] = r.get("count", 0)
        
        return counts

    async def mark_intervention_resolved(self, citizen_id: int) -> bool:
        """
        Marca una intervención como resuelta.
        
        Args:
            citizen_id: ID del ciudadano
            
        Returns:
            True si fue exitoso
        """
        query = """
        MATCH (c:Citizen {id: $cid})-[pred:RED_BALL_PREDICTED]->(c)
        WHERE pred.verdict = 'INTERVENE' AND pred.status = 'ACTIVE'
        SET pred.status = 'RESOLVED',
            pred.resolved_at = datetime()
        RETURN pred
        """
        result = await db_manager.execute_write(query, {"cid": citizen_id})
        logger.info(f"Intervención para ciudadano #{citizen_id} marcada como RESOLVED")
        return result is not None

    async def get_prediction_accuracy(
        self, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calcula precisión del modelo (predicciones vs crímenes reales).
        
        Args:
            days: Período para análisis
            
        Returns:
            Diccionario con métricas de precisión
        """
        query = """
        MATCH (c:Citizen)-[pred:RED_BALL_PREDICTED]->(c)
        WHERE pred.timestamp > datetime() - duration({days: $days})
        OPTIONAL MATCH (c)-[crime:COMMITTED_CRIME]->()
        WHERE crime.date > pred.timestamp AND 
              crime.date < pred.timestamp + duration({days: 30})
        WITH pred.verdict as verdict,
             pred.probability as probability,
             count(crime) > 0 as actual_crime
        RETURN verdict,
               avg(probability) as avg_prob,
               sum(CASE WHEN actual_crime THEN 1 ELSE 0 END) as true_positives,
               count(*) as total_predictions
        """
        result = await db_manager.query(query, {"days": days})
        
        summary = {
            "accuracy": 0.0,
            "precision": 0.0,
            "verdicts": {}
        }
        
        for r in result:
            verdict = r.get("verdict")
            if verdict:
                summary["verdicts"][verdict] = {
                    "average_probability": round(r.get("avg_prob", 0), 3),
                    "true_positives": r.get("true_positives", 0),
                    "total_predictions": r.get("total_predictions", 0)
                }
        
        return summary

# Instancia Singleton
prediction_repository = PredictionRepository()
