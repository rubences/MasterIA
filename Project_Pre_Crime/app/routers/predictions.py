"""
Router de Predicciones: "La Sala de los Precogs"
Endpoints para análisis de riesgo criminal en tiempo real.

Arquit arquitectura:
  Router (HTTP) → Service (Lógica Pre-Crime) → Repository (Persistencia)
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, status
from datetime import datetime
from app.services.prediction_service import prediction_service
from app.services.citizen_service import citizen_service
from app.models.schemas import PredictionOutput
from app.config import settings

logger = logging.getLogger("PredictionsRouter")

router = APIRouter(
    prefix="/precogs",
    tags=["Predictions"]
)

# ==================== MAIN PREDICTION ENDPOINTS ====================

@router.get("/scan/{citizen_id}", response_model=PredictionOutput)
async def scan_citizen(citizen_id: int):
    """
    🔮 ENDPOINT PRINCIPAL: Análisis Pre-Crime de un ciudadano.
    
    Pipeline:
    1. Enriquecer datos del ciudadano desde Neo4j
    2. Construir vector de características para IA
    3. Ejecutar modelo GraphSAGE/GAT
    4. Determinar veredicto según umbrales
    5. Registrar predicción para auditoría
    
    Verdicts:
    - SAFE: < 60% - Sin riesgo detectado
    - WATCHLIST: 60-85% - Monitoreo recomendado
    - INTERVENE: > 85% - 🔴 BOLA ROJA - Acción Pre-Crime
    """
    try:
        # 1. Enriquecer características
        citizen_features = await citizen_service.enrich_citizen_for_inference(citizen_id)
        
        if not citizen_features:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ciudadano #{citizen_id} no encontrado en el sistema"
            )
        
        # 2. INFERENCE + CLASSIFICATION + RECORDING (todo en el Service)
        prediction = await prediction_service.predict_citizen_risk(citizen_features)
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en predicción: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error durante análisis Pre-Crime"
        )

@router.post("/batch-scan")
async def batch_scan(
    citizen_ids: list[int] = Query(..., description="IDs de ciudadanos a analizar"),
    max_batch: int = Query(100, ge=1, le=100, description="Máximo de ciudadanos")
):
    """
    Análisis masivo de múltiples ciudadanos.
    Útil para escaneo de zonas de alto riesgo.
    
    Retorna resumen con estadísticas de verdicts.
    """
    if len(citizen_ids) > max_batch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Máximo {max_batch} ciudadanos por batch"
        )
    
    results = []
    
    for cid in citizen_ids:
        try:
            citizen_features = await citizen_service.enrich_citizen_for_inference(cid)
            if citizen_features:
                prediction = await prediction_service.predict_citizen_risk(citizen_features)
                results.append({
                    "citizen_id": cid,
                    "verdict": prediction.verdict,
                    "probability": prediction.probability
                })
        except Exception as e:
            logger.warning(f"Saltando ciudadano {cid}: {e}")
            continue
    
    # Estadísticas
    intervene_count = sum(1 for r in results if r["verdict"] == "INTERVENE")
    watchlist_count = sum(1 for r in results if r["verdict"] == "WATCHLIST")
    safe_count = sum(1 for r in results if r["verdict"] == "SAFE")
    
    return {
        "total_scanned": len(results),
        "verdicts": {
            "intervene": intervene_count,
            "watchlist": watchlist_count,
            "safe": safe_count
        },
        "results": results
    }

# ==================== ANALYSIS ENDPOINTS ====================

@router.get("/high-risk")
async def get_high_risk_citizens(
    threshold: float = Query(None, ge=0.0, le=1.0, description="Umbral de riesgo")
):
    """
    Lista ciudadanos de alto riesgo basándose en su risk_seed.
    Útil para priorizar análisis detallados.
    """
    if threshold is None:
        threshold = settings.RISK_THRESHOLD_WATCHLIST
    
    suspects = await citizen_service.get_high_risk_suspects(threshold)
    
    return {
        "threshold": threshold,
        "count": len(suspects),
        "suspects": suspects
    }

@router.get("/{citizen_id}/history")
async def get_prediction_history(
    citizen_id: int,
    limit: int = Query(20, ge=1, le=100, description="Máximo de registros")
):
    """
    Obtiene historial completo de predicciones para un ciudadano.
    Incluye análisis de tendencia de riesgo.
    """
    # Verificar que el ciudadano existe
    citizen = await citizen_service.get_citizen(citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ciudadano #{citizen_id} no encontrado"
        )
    
    history = await prediction_service.get_prediction_history(citizen_id, limit)
    
    return {
        "citizen_id": citizen_id,
        "citizen_name": citizen.get("name"),
        **history
    }

@router.get("/admin/interventions")
async def get_active_interventions():
    """
    Obtiene todas las intervenciones activas (Bolas Rojas).
    Dashboard para jefe de policía.
    
    ⚠️ ENDPOINT SENSIBLE - Debería requerir autenticación
    """
    interventions = await prediction_service.get_active_interventions()
    
    return {
        "timestamp": datetime.now(),
        "critical_alert": interventions["critical_count"] > 0,
        **interventions
    }

@router.get("/admin/statistics")
async def get_prediction_statistics(
    days: int = Query(7, ge=1, le=365, description="Período en días")
):
    """
    Estadísticas de predicciones: volumen, precisión, tendencias.
    
    ⚠️ ENDPOINT SENSIBLE - Debería requerir autenticación
    """
    stats = await prediction_service.get_prediction_statistics(days)
    
    return {
        "generated_at": datetime.now(),
        **stats
    }

# ==================== ADMINISTRATIVE ENDPOINTS ====================

@router.post("/{citizen_id}/resolve")
async def resolve_intervention(citizen_id: int):
    """
    Marca una intervención Pre-Crime como resuelta.
    
    Se ejecuta cuando la acción está completada.
    
    ⚠️ ENDPOINT SENSIBLE - Requiere autenticación de oficial
    """
    citizen = await citizen_service.get_citizen(citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ciudadano #{citizen_id} no encontrado"
        )
    
    success = await prediction_service.mark_intervention_resolved(citizen_id)
    
    if success:
        logger.info(f"Intervención para #{citizen_id} marcada como RESUELTA")
        return {
            "citizen_id": citizen_id,
            "status": "RESOLVED",
            "timestamp": datetime.now()
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay intervención activa para este ciudadano"
        )

# ==================== HELPER FUNCTIONS ====================

async def _background_register_prediction(
    citizen_id: int,
    probability: float,
    verdict: str
):
    """Registra predicción en background (no bloquea respuesta)."""
    try:
        logger.info(f"📝 Registrando predicción en background: #{citizen_id}")
        # Aquí iría la persistencia si no se hizo en el Service
    except Exception as e:
        logger.error(f"Error en background task: {e}")
