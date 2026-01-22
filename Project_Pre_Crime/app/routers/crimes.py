"""
API Router para Eventos Criminales (Crimes).

Endpoints:
  GET  /crimes                     - Listar todos los crímenes
  GET  /crimes/{id}                - Obtener crimen específico
  GET  /crimes/recent              - Actividad criminal reciente
  GET  /crimes/type/{crime_type}   - Crímenes por tipo
  GET  /crimes/location/{loc_id}   - Crímenes en ubicación
  GET  /crimes/perpetrator/{perp}  - Crímenes de perpetrador
  POST /crimes                      - Registrar nuevo crimen
  GET  /crimes/admin/stats         - Estadísticas de crímenes
  GET  /crimes/admin/timeline      - Línea temporal de crímenes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.services.crime_service import CrimeService
from app.models.schemas_crime import Crime, CrimeCreate, CrimeReport, CrimeStatistics, CrimeTimeline

router = APIRouter(
    prefix="/crimes",
    tags=["crimes"],
    responses={404: {"description": "Crimen no encontrado"}}
)


@router.get("", response_model=List[Crime])
async def list_crimes(limit: int = Query(50, ge=1, le=500)):
    """
    Obtiene todos los crímenes registrados.
    
    Args:
        limit: Número máximo de registros
        
    Returns:
        Lista de crímenes ordenados por fecha descendente
    """
    try:
        crimes = await CrimeService.get_all_crimes(limit)
        return crimes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo crímenes: {str(e)}")


@router.get("/recent", response_model=List[Crime])
async def get_recent_activity(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Obtiene actividad criminal reciente.
    
    Args:
        days: Número de días hacia atrás
        limit: Número máximo de registros
        
    Returns:
        Lista de crímenes recientes
    """
    try:
        crimes = await CrimeService.get_recent_activity(days, limit)
        return crimes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo actividad reciente: {str(e)}")


@router.get("/type/{crime_type}", response_model=List[Crime])
async def get_crimes_by_type(
    crime_type: str,
    days: int = Query(90, ge=1, le=365)
):
    """
    Obtiene crímenes de un tipo específico.
    
    Args:
        crime_type: Tipo de crimen (Robbery, Assault, etc.)
        days: Período de búsqueda
        
    Returns:
        Lista de crímenes del tipo especificado
    """
    try:
        crimes = await CrimeService.get_crimes_by_type(crime_type, days)
        if not crimes:
            raise HTTPException(status_code=404, detail=f"No se encontraron crímenes de tipo '{crime_type}'")
        return crimes
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo crímenes: {str(e)}")


@router.get("/location/{location_id}", response_model=List[Crime])
async def get_crimes_at_location(
    location_id: str,
    limit: int = Query(50, ge=1, le=500)
):
    """
    Obtiene crímenes ocurridos en una ubicación específica.
    
    Args:
        location_id: ID de la ubicación
        limit: Número máximo de registros
        
    Returns:
        Historial criminal de la ubicación
    """
    try:
        crimes = await CrimeService.get_crimes_at_location(location_id, limit)
        return crimes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo crímenes: {str(e)}")


@router.get("/perpetrator/{perpetrator_id}", response_model=List[Crime])
async def get_perpetrator_history(
    perpetrator_id: int,
    limit: int = Query(50, ge=1, le=500)
):
    """
    Obtiene histórico criminal de un ciudadano.
    
    Args:
        perpetrator_id: ID del ciudadano
        limit: Número máximo de registros
        
    Returns:
        Crímenes cometidos por el ciudadano
    """
    try:
        crimes = await CrimeService.get_perpetrator_history(perpetrator_id, limit)
        return crimes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")


@router.get("/{crime_id}", response_model=Crime)
async def get_crime(crime_id: str):
    """
    Obtiene un crimen específico con detalles completos.
    
    Args:
        crime_id: ID del crimen
        
    Returns:
        Detalle del crimen
    """
    try:
        crime = await CrimeService.get_crime(crime_id)
        if not crime:
            raise HTTPException(status_code=404, detail=f"Crimen {crime_id} no encontrado")
        return crime
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo crimen: {str(e)}")


@router.post("", response_model=CrimeReport, status_code=201)
async def report_crime(crime: CrimeCreate):
    """
    Registra un nuevo crimen en el sistema.
    
    Args:
        crime: Datos del nuevo crimen
        
    Returns:
        Reporte del crimen registrado con análisis de impacto
    """
    try:
        report = await CrimeService.report_crime(crime)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error registrando crimen: {str(e)}")


@router.post("/{crime_id}/mark-investigated", status_code=204)
async def mark_investigated(crime_id: str):
    """
    Marca un crimen como investigado.
    
    Args:
        crime_id: ID del crimen
    """
    try:
        success = await CrimeService.mark_investigated(crime_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Crimen {crime_id} no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marcando investigado: {str(e)}")


@router.get("/admin/statistics", response_model=CrimeStatistics)
async def get_crime_statistics(days: int = Query(365, ge=1, le=1825)):
    """
    Obtiene estadísticas agregadas de crímenes.
    
    Args:
        days: Período de análisis (1-1825 días = 5 años)
        
    Returns:
        Estadísticas completas del sistema
    """
    try:
        stats = await CrimeService.get_crime_statistics(days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")


@router.get("/admin/timeline", response_model=List[CrimeTimeline])
async def get_crime_timeline(days: int = Query(30, ge=1, le=365)):
    """
    Obtiene línea temporal de actividad criminal.
    
    Args:
        days: Número de días para el análisis
        
    Returns:
        Timeline de crímenes por día
    """
    try:
        timeline = await CrimeService.get_crime_timeline(days)
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo timeline: {str(e)}")
