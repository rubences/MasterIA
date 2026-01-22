"""
Router de Ciudadanos: Endpoints de la API REST para Ciudadanos.

Arquitectura de capas:
  Router (HTTP) → Service (Lógica de negocio) → Repository (Datos)

Equivalente a @RestController en Spring.
"""
import logging
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from app.services.citizen_service import citizen_service
from app.models.schemas import Citizen, CitizenCreate, CitizenUpdate

logger = logging.getLogger("CitizenRouter")

router = APIRouter(
    prefix="/citizens",
    tags=["Citizens"]
)

# ==================== GET ENDPOINTS ====================

@router.get("/", response_model=List[Citizen])
async def list_citizens(
    limit: int = Query(50, ge=1, le=1000, description="Número máximo de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación")
):
    """
    Listar todos los ciudadanos con paginación.
    
    Equivalente a @GetMapping en Spring.
    Delega al Service → Repository → Neo4j
    """
    try:
        citizens = await citizen_service.get_all_citizens(limit, offset)
        return citizens if citizens else []
    except Exception as e:
        logger.error(f"Error listando ciudadanos: {e}")
        raise HTTPException(status_code=500, detail="Error interno al listar ciudadanos")

@router.get("/{citizen_id}", response_model=Citizen)
async def get_citizen(citizen_id: int):
    """
    Obtiene información detallada de un ciudadano específico.
    
    El Service enriquece los datos con cálculos derivados.
    """
    citizen = await citizen_service.get_citizen(citizen_id)
    
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ciudadano con ID {citizen_id} no encontrado"
        )
    
    return citizen

@router.get("/search", response_model=List[Citizen])
async def search_citizens(
    name: str = Query(..., min_length=2, max_length=100, description="Término de búsqueda"),
    limit: int = Query(20, ge=1, le=100, description="Máximo de resultados")
):
    """
    Búsqueda de ciudadanos por nombre (case-insensitive).
    """
    try:
        results = await citizen_service.search_citizens(name)
        return results[:limit] if results else []
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail="Error en búsqueda de ciudadanos")

@router.get("/{citizen_id}/network")
async def get_citizen_network(
    citizen_id: int,
    depth: int = Query(1, ge=1, le=3, description="Profundidad de la red social")
):
    """
    Obtiene red social de un ciudadano con análisis de riesgo.
    
    Depth=1: Amigos directos
    Depth=2: Amigos de amigos
    """
    citizen = await citizen_service.get_citizen(citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ciudadano {citizen_id} no encontrado"
        )
    
    network = await citizen_service.get_citizen_network(citizen_id, depth)
    return network

@router.get("/risk/analysis")
async def get_high_risk_analysis(
    threshold: float = Query(0.6, ge=0.0, le=1.0, description="Umbral de riesgo")
):
    """
    Análisis de ciudadanos de alto riesgo.
    Utilitario para jefe de policía.
    """
    suspects = await citizen_service.get_high_risk_suspects(threshold)
    
    return {
        "threshold": threshold,
        "count": len(suspects),
        "suspects": suspects
    }

# ==================== POST ENDPOINTS ====================

@router.post("/", response_model=Citizen, status_code=status.HTTP_201_CREATED)
async def create_citizen(citizen_data: CitizenCreate):
    """
    Crea un nuevo ciudadano en el sistema.
    
    Equivalente a @PostMapping en Spring.
    """
    try:
        new_citizen = await citizen_service.create_citizen(citizen_data)
        return new_citizen
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creando ciudadano: {e}")
        raise HTTPException(status_code=500, detail="Error al crear ciudadano")

# ==================== PUT/PATCH ENDPOINTS ====================

@router.patch("/{citizen_id}", response_model=Citizen)
async def update_citizen(citizen_id: int, updates: CitizenUpdate):
    """
    Actualiza información de un ciudadano.
    Permite actualizar status y risk_seed.
    """
    # Verificar que existe
    citizen = await citizen_service.get_citizen(citizen_id)
    if not citizen:
        raise HTTPException(status_code=404, detail="Ciudadano no encontrado")
    
    # Aplicar actualizaciones
    if updates.status:
        await citizen_service.update_citizen_status(citizen_id, updates.status)
    
    if updates.risk_seed is not None:
        await citizen_service.update_citizen_risk(citizen_id, updates.risk_seed)
    
    # Retornar versión actualizada
    return await citizen_service.get_citizen(citizen_id)

# ==================== ADMINISTRATIVE ENDPOINTS ====================

@router.get("/admin/statistics")
async def get_statistics():
    """
    Obtiene estadísticas del sistema.
    Endpoint administrativo (idealmente protegido por autenticación).
    """
    stats = await citizen_service.get_system_statistics()
    return stats
