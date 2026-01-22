"""
PredictionService: Servicios de negocio para predicciones.
Orquesta el flujo de inferencia y persistencia.
"""
import logging
from typing import Dict, Any, Optional
from app.repositories.prediction_repo import prediction_repository
from app.core.ai_engine import precog_system
from app.models.schemas import CitizenFeatureVector, PredictionOutput, VerdictType
from app.config import settings
from datetime import datetime

logger = logging.getLogger("PredictionService")

class PredictionService:
    """
    Servicios de negocio para predicciones Pre-Crime.
    
    Responsabilidades:
    - Orquestar AI + BD
    - Determinar veredictos
    - Registrar predicciones
    - Generar análisis
    """

    async def predict_citizen_risk(
        self, 
        citizen_features: CitizenFeatureVector
    ) -> PredictionOutput:
        """
        Pipeline completo de predicción.
        
        1. Ejecutar modelo de IA
        2. Determinar veredicto según umbral
        3. Registrar en BD
        4. Retornar resultado
        
        Args:
            citizen_features: Vector de características enriquecido
            
        Returns:
            PredictionOutput con veredicto
        """
        # 1. INFERENCE: Ejecutar modelo
        ai_verdict = precog_system.predict(citizen_features)
        probability = ai_verdict["probability"]
        confidence = ai_verdict["confidence"]
        
        # 2. CLASSIFY: Determinar veredicto
        verdict = self._classify_verdict(probability)
        
        # 3. RECORD: Persistir predicción (en background idealmente)
        await prediction_repository.record_prediction(
            citizen_id=citizen_features.id,
            probability=probability,
            confidence=confidence,
            verdict=verdict.value
        )
        
        # 4. LOG: Registrar en logs
        logger.info(
            f"🔮 Predicción completada: #{citizen_features.id} ({citizen_features.name}) "
            f"→ {verdict.value} ({probability:.1%})"
        )
        
        # 5. RETURN
        return PredictionOutput(
            subject_id=citizen_features.id,
            subject_name=citizen_features.name,
            probability=probability,
            verdict=verdict,
            confidence=confidence,
            analyzed_at=datetime.now()
        )

    async def get_prediction_history(
        self, 
        citizen_id: int,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Obtiene historial de predicciones para un ciudadano.
        
        Args:
            citizen_id: ID del ciudadano
            limit: Máximo de registros
            
        Returns:
            Historial con análisis
        """
        history = await prediction_repository.get_prediction_history(citizen_id, limit)
        
        if not history:
            return {
                "citizen_id": citizen_id,
                "total_predictions": 0,
                "history": []
            }
        
        # Calcular tendencia
        avg_probability = sum(h.get("probability", 0) for h in history) / len(history)
        
        return {
            "citizen_id": citizen_id,
            "total_predictions": len(history),
            "average_risk": round(avg_probability, 3),
            "trend": self._calculate_trend(history),
            "history": history
        }

    async def get_active_interventions(self) -> Dict[str, Any]:
        """
        Obtiene todas las intervenciones activas (Bolas Rojas).
        Útil para dashboard de jefe de policía.
        
        Returns:
            Resumen de intervenciones requeridas
        """
        interventions = await prediction_repository.get_interventions("ACTIVE")
        
        return {
            "total_interventions": len(interventions),
            "interventions": interventions,
            "critical_count": sum(1 for i in interventions if i.get("probability", 0) > 0.9)
        }

    async def mark_intervention_resolved(self, citizen_id: int) -> bool:
        """Marca una intervención Pre-Crime como resuelta."""
        return await prediction_repository.mark_intervention_resolved(citizen_id)

    async def get_prediction_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Estadísticas de predicciones en un período.
        
        Args:
            days: Número de días retrospectivos
            
        Returns:
            Diccionario con métricas
        """
        verdict_counts = await prediction_repository.count_verdicts_by_type(days)
        accuracy = await prediction_repository.get_prediction_accuracy(days)
        
        total = sum(verdict_counts.values())
        
        return {
            "period_days": days,
            "total_predictions": total,
            "verdict_distribution": {
                "safe": verdict_counts["SAFE"],
                "watchlist": verdict_counts["WATCHLIST"],
                "intervene": verdict_counts["INTERVENE"]
            },
            "accuracy_metrics": accuracy
        }

    # ==================== MÉTODOS AUXILIARES PRIVADOS ====================

    @staticmethod
    def _classify_verdict(probability: float) -> VerdictType:
        """
        Clasifica la probabilidad en veredicto.
        
        Args:
            probability: Probabilidad predicha [0.0-1.0]
            
        Returns:
            VerdictType apropiado
        """
        if probability >= settings.RISK_THRESHOLD_INTERVENE:
            return VerdictType.INTERVENE
        elif probability >= settings.RISK_THRESHOLD_WATCHLIST:
            return VerdictType.WATCHLIST
        else:
            return VerdictType.SAFE

    @staticmethod
    def _calculate_trend(history: list) -> str:
        """
        Calcula tendencia de riesgo en historial.
        
        Args:
            history: Lista de predicciones ordenadas por fecha
            
        Returns:
            Descripción de tendencia
        """
        if len(history) < 2:
            return "Datos insuficientes"
        
        # Comparar primeras 50% vs últimas 50%
        mid = len(history) // 2
        recent_avg = sum(h.get("probability", 0) for h in history[:mid]) / mid
        older_avg = sum(h.get("probability", 0) for h in history[mid:]) / (len(history) - mid)
        
        diff = recent_avg - older_avg
        
        if diff > 0.1:
            return "📈 Riesgo AUMENTANDO"
        elif diff < -0.1:
            return "📉 Riesgo DISMINUYENDO"
        else:
            return "➡️ Riesgo ESTABLE"

# Instancia Singleton
prediction_service = PredictionService()
