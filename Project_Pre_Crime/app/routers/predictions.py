"""
Router de Predicciones: "La Sala de los Precogs"
Endpoints para análisis de riesgo criminal en tiempo real.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
from app.core.database import db_manager
from app.core.ai_engine import precog_system
from app.models.schemas import PredictionOutput, CitizenFeatureVector
from app.config import settings
import logging

logger = logging.getLogger("PredictionsRouter")

router = APIRouter(
    prefix="/precogs",
    tags=["Predictions"]
)

@router.get("/scan/{citizen_id}", response_model=PredictionOutput)
async def scan_citizen(citizen_id: int, background_tasks: BackgroundTasks):
    """
    ENDPOINT PRINCIPAL: Análisis Pre-Crime de un ciudadano.
    
    Proceso:
    1. Extrae contexto del ciudadano desde Neo4j (subgrafo social)
    2. Prepara vector de características
    3. Ejecuta inferencia con modelo GNN
    4. Devuelve veredicto con nivel de riesgo
    
    Umbrales:
    - SAFE: < 60%
    - WATCHLIST: 60-85%
    - INTERVENE: > 85% (Bola Roja)
    """
    
    # 1. FETCH: Obtener contexto del ciudadano desde Neo4j
    cypher_query = """
    MATCH (c:Citizen {id: $cid})
    OPTIONAL MATCH (c)-[:KNOWS]-(friend:Citizen)
    OPTIONAL MATCH (friend)-[r:COMMITTED_CRIME]->()
    WITH c, 
         count(distinct friend) as total_contacts,
         count(distinct r) as criminal_contacts
    
    RETURN c.id as id, 
           c.name as name, 
           c.risk_seed as risk_seed,
           c.job as job,
           c.born as born,
           criminal_contacts as criminal_degree,
           total_contacts as social_network_size
    """
    
    results = await db_manager.query(cypher_query, {"cid": citizen_id})
    
    if not results:
        raise HTTPException(
            status_code=404, 
            detail=f"Ciudadano ID {citizen_id} no encontrado en el sistema"
        )
    
    raw_data = results[0]
    
    # 2. TRANSFORM: Preparar datos para el modelo
    # Normalizar edad
    age_normalized = None
    if raw_data.get('born'):
        age = settings.CURRENT_YEAR - raw_data['born']
        age_normalized = min(age / 100.0, 1.0)
    
    # Mock de job_vector (en producción vendría de feature_engineering)
    job_vector = _encode_job(raw_data.get('job'))
    
    features = CitizenFeatureVector(
        id=raw_data['id'],
        name=raw_data['name'],
        status="ACTIVE",
        criminal_degree=raw_data.get('criminal_degree', 0),
        risk_seed=raw_data.get('risk_seed', 0.0),
        job_vector=job_vector,
        age_normalized=age_normalized
    )
    
    # 3. INFERENCE: Ejecutar modelo Pre-Crime
    ai_verdict = precog_system.predict(features)
    probability = ai_verdict["probability"]
    confidence = ai_verdict["confidence"]
    
    # 4. VERDICT: Clasificar según umbrales
    if probability >= settings.RISK_THRESHOLD_INTERVENE:
        verdict_label = "INTERVENE"
        # Registrar "Bola Roja" en background
        background_tasks.add_task(
            _register_red_ball, 
            citizen_id, 
            probability, 
            confidence
        )
    elif probability >= settings.RISK_THRESHOLD_WATCHLIST:
        verdict_label = "WATCHLIST"
    else:
        verdict_label = "SAFE"
    
    logger.info(
        f"🔮 Análisis completado: Ciudadano #{citizen_id} "
        f"({raw_data['name']}) → {verdict_label} ({probability:.2%})"
    )
    
    return PredictionOutput(
        subject_id=citizen_id,
        subject_name=raw_data['name'],
        probability=probability,
        verdict=verdict_label,
        confidence=confidence,
        analyzed_at=datetime.now()
    )

@router.post("/batch-scan")
async def batch_scan(citizen_ids: list[int]):
    """
    Análisis masivo de múltiples ciudadanos.
    Útil para escaneo de zonas de alto riesgo.
    """
    if len(citizen_ids) > 100:
        raise HTTPException(
            status_code=400,
            detail="Máximo 100 ciudadanos por batch"
        )
    
    results = []
    for cid in citizen_ids:
        try:
            # Reutilizar lógica de scan_citizen sin background tasks
            cypher_query = """
            MATCH (c:Citizen {id: $cid})
            OPTIONAL MATCH (c)-[:KNOWS]-(friend)-[r:COMMITTED_CRIME]->()
            WITH c, count(distinct r) as criminal_contacts
            RETURN c.id as id, c.name as name, c.risk_seed as risk_seed,
                   c.job as job, c.born as born, criminal_contacts as criminal_degree
            """
            data = await db_manager.query(cypher_query, {"cid": cid})
            
            if not data:
                continue
            
            raw = data[0]
            age_norm = None
            if raw.get('born'):
                age_norm = min((settings.CURRENT_YEAR - raw['born']) / 100.0, 1.0)
            
            features = CitizenFeatureVector(
                id=raw['id'],
                name=raw['name'],
                status="ACTIVE",
                criminal_degree=raw.get('criminal_degree', 0),
                risk_seed=raw.get('risk_seed', 0.0),
                job_vector=_encode_job(raw.get('job')),
                age_normalized=age_norm
            )
            
            verdict = precog_system.predict(features)
            prob = verdict["probability"]
            
            results.append({
                "citizen_id": cid,
                "name": raw['name'],
                "probability": prob,
                "verdict": _get_verdict_label(prob)
            })
            
        except Exception as e:
            logger.error(f"Error procesando ciudadano {cid}: {e}")
            continue
    
    return {
        "total_scanned": len(results),
        "high_risk_count": sum(1 for r in results if r['probability'] >= settings.RISK_THRESHOLD_INTERVENE),
        "results": results
    }

@router.get("/high-risk")
async def get_high_risk_citizens(threshold: float = None):
    """
    Lista ciudadanos de alto riesgo basándose en su risk_seed.
    Útil para priorizar análisis detallados.
    """
    if threshold is None:
        threshold = settings.RISK_THRESHOLD_WATCHLIST
    
    cypher_query = """
    MATCH (c:Citizen)
    WHERE c.risk_seed >= $threshold
    OPTIONAL MATCH (c)-[:KNOWS]-(friend)-[:COMMITTED_CRIME]->()
    WITH c, count(distinct friend) as criminal_contacts
    RETURN c.id as id,
           c.name as name,
           c.risk_seed as risk_seed,
           criminal_contacts as criminal_degree
    ORDER BY c.risk_seed DESC
    LIMIT 50
    """
    
    results = await db_manager.query(cypher_query, {"threshold": threshold})
    
    return {
        "threshold": threshold,
        "count": len(results),
        "citizens": [
            {
                "id": r['id'],
                "name": r['name'],
                "risk_seed": r['risk_seed'],
                "criminal_contacts": r['criminal_degree']
            }
            for r in results
        ]
    }

# ==================== Funciones auxiliares ====================

def _encode_job(job: str | None) -> list[float]:
    """Codifica trabajo a vector one-hot (mock simplificado)."""
    jobs = ["Doctor", "Engineer", "Teacher", "Police", "Artist", 
            "Driver", "Clerk", "Manager", "Scientist", "Other"]
    if not job:
        return [0.0] * len(jobs)
    
    try:
        idx = jobs.index(job)
        vector = [0.0] * len(jobs)
        vector[idx] = 1.0
        return vector
    except ValueError:
        # Job desconocido → categoría "Other"
        vector = [0.0] * len(jobs)
        vector[-1] = 1.0
        return vector

def _get_verdict_label(probability: float) -> str:
    """Determina veredicto basándose en probabilidad."""
    if probability >= settings.RISK_THRESHOLD_INTERVENE:
        return "INTERVENE"
    elif probability >= settings.RISK_THRESHOLD_WATCHLIST:
        return "WATCHLIST"
    return "SAFE"

async def _register_red_ball(citizen_id: int, probability: float, confidence: float):
    """
    Registra una predicción de "Bola Roja" en Neo4j.
    Se ejecuta en background para no bloquear la respuesta.
    """
    try:
        query = """
        MATCH (c:Citizen {id: $cid})
        MERGE (c)-[r:RED_BALL_PREDICTED]->(c)
        SET r.probability = $prob,
            r.confidence = $conf,
            r.timestamp = datetime(),
            r.status = 'ACTIVE'
        """
        await db_manager.execute_write(query, {
            "cid": citizen_id,
            "prob": probability,
            "conf": confidence
        })
        logger.info(f"🔴 Bola Roja registrada para ciudadano #{citizen_id}")
    except Exception as e:
        logger.error(f"Error registrando Bola Roja: {e}")
