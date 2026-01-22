"""
API Router para Ubicaciones (Locations).

Endpoints:
  GET  /locations              - Listar todas las ubicaciones
  GET  /locations/{id}         - Obtener ubicación específica
  GET  /locations/search       - Buscar ubicación por nombre
  GET  /locations/hotspots     - Obtener zonas de alto riesgo
  POST /locations              - Crear nueva ubicación
  GET  /locations/admin/stats  - Estadísticas de ubicaciones
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.services.location_service import LocationService
from app.models.schemas_location import Location, LocationCreate, LocationHotspot, LocationStatistics

router = APIRouter(
    prefix="/locations",
    tags=["locations"],
    responses={404: {"description": "Ubicación no encontrada"}}
)


@router.get("", response_model=List[Location])
async def list_locations():
    """
    Obtiene todas las ubicaciones de la ciudad.
    
    Returns:
        Lista de ubicaciones con estadísticas de crímenes
    """
    try:
        locations = await LocationService.get_all_locations()
        return locations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo ubicaciones: {str(e)}")


@router.get("/hotspots", response_model=List[LocationHotspot])
async def get_hotspots(limit: int = Query(10, ge=1, le=100)):
    """
    Obtiene las ubicaciones con mayor actividad criminal.
    
    Args:
        limit: Número máximo de hotspots a retornar (1-100)
        
    Returns:
        Lista de hotspots ordenados por riesgo
    """
    try:
        hotspots = await LocationService.get_hotspots(limit)
        if not hotspots:
            raise HTTPException(status_code=404, detail="No hotspots encontrados")
        return hotspots
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo hotspots: {str(e)}")


@router.get("/search", response_model=Location)
async def search_location(q: str = Query(..., min_length=1)):
    """
    Busca una ubicación por nombre.
    
    Args:
        q: Término de búsqueda (parte del nombre)
        
    Returns:
        Ubicación que coincide con la búsqueda
    """
    try:
        location = await LocationService.search_locations(q)
        if not location:
            raise HTTPException(status_code=404, detail=f"No se encontró ubicación para '{q}'")
        return location
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")


@router.get("/{location_id}", response_model=Location)
async def get_location(location_id: str):
    """
    Obtiene una ubicación específica con detalles completos.
    
    Args:
        location_id: ID de la ubicación
        
    Returns:
        Detalle de la ubicación con estadísticas
    """
    try:
        location = await LocationService.get_location(location_id)
        if not location:
            raise HTTPException(status_code=404, detail=f"Ubicación {location_id} no encontrada")
        return location
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo ubicación: {str(e)}")


@router.get("/{location_id}/crimes")
async def get_location_crimes(location_id: str, days: int = Query(30, ge=1, le=365)):
    """
    Obtiene histórico de crímenes en una ubicación.
    
    Args:
        location_id: ID de la ubicación
        days: Número de días hacia atrás
        
    Returns:
        Lista de crímenes recientes en la ubicación
    """
    try:
        crimes = await LocationService.get_location_crimes(location_id, days)
        return {
            "location_id": location_id,
            "period_days": days,
            "crime_count": len(crimes),
            "crimes": crimes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo crímenes: {str(e)}")


@router.post("", response_model=Location, status_code=201)
async def create_location(location: LocationCreate):
    """
    Crea una nueva ubicación en la ciudad.
    
    Args:
        location: Datos de la nueva ubicación
        
    Returns:
        Ubicación creada
    """
    try:
        new_location = await LocationService.create_location(location)
        return new_location
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creando ubicación: {str(e)}")


@router.get("/admin/statistics", response_model=LocationStatistics)
async def get_location_statistics():
    """
    Obtiene estadísticas agregadas de todas las ubicaciones.
    
    Returns:
        Estadísticas globales del sistema
    """
    try:
        stats = await LocationService.get_statistics()
        return LocationStatistics(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")
