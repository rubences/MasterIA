"""
CrimeService - Capa de lógica de negocio para Eventos Criminales.

Responsabilidades:
  - Enriquecer datos de crímenes con contexto de ciudadanos y ubicaciones
  - Calcular impacto en el riesgo local
  - Analizar patrones criminales
  - Validar datos antes de persistencia
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from app.repositories.crime_repo import CrimeRepository
from app.repositories.location_repo import LocationRepository
from app.models.schemas_crime import CrimeCreate, Crime, CrimeReport, CrimeStatistics, CrimeTimeline


class CrimeService:
    """
    Servicio de lógica de negocio para Eventos Criminales.
    Implementa reglas de negocio, análisis y transformaciones de datos.
    """

    @staticmethod
    async def get_all_crimes(limit: int = 100) -> List[Crime]:
        """
        Obtiene todos los crímenes registrados.
        
        Args:
            limit: Número máximo de registros
            
        Returns:
            Lista de crímenes con detalles enriquecidos
        """
        crimes_data = await CrimeRepository.find_all(limit)
        return [Crime(**crime) for crime in crimes_data]

    @staticmethod
    async def get_crime(crime_id: str) -> Optional[Crime]:
        """
        Obtiene un crimen específico.
        
        Args:
            crime_id: ID del crimen
            
        Returns:
            Detalle del crimen, o None si no existe
        """
        crime_data = await CrimeRepository.find_by_id(crime_id)
        if crime_data:
            return Crime(**crime_data)
        return None

    @staticmethod
    async def get_recent_activity(days: int = 30, limit: int = 50) -> List[Crime]:
        """
        Obtiene actividad criminal reciente (últimas semanas/meses).
        
        Args:
            days: Número de días hacia atrás
            limit: Número máximo de registros
            
        Returns:
            Lista de crímenes recientes
        """
        crimes_data = await CrimeRepository.find_recent_activity(days, limit)
        return [Crime(**crime) for crime in crimes_data]

    @staticmethod
    async def get_crimes_by_type(crime_type: str, days: int = 90) -> List[Crime]:
        """
        Busca crímenes de un tipo específico.
        
        Args:
            crime_type: Tipo de crimen
            days: Período de búsqueda
            
        Returns:
            Lista de crímenes del tipo especificado
        """
        crimes_data = await CrimeRepository.find_by_type(crime_type, days)
        return [Crime(**crime) for crime in crimes_data]

    @staticmethod
    async def get_crimes_at_location(location_id: str, limit: int = 50) -> List[Crime]:
        """
        Obtiene crímenes ocurridos en una ubicación.
        
        Args:
            location_id: ID de la ubicación
            limit: Número máximo de registros
            
        Returns:
            Historial criminal de la ubicación
        """
        crimes_data = await CrimeRepository.find_by_location(location_id, limit)
        return [Crime(**crime) for crime in crimes_data]

    @staticmethod
    async def get_perpetrator_history(perpetrator_id: int, limit: int = 50) -> List[Crime]:
        """
        Obtiene histórico criminal de un ciudadano.
        
        Args:
            perpetrator_id: ID del ciudadano
            limit: Número máximo de registros
            
        Returns:
            Historial criminal del ciudadano
        """
        crimes_data = await CrimeRepository.find_by_perpetrator(perpetrator_id, limit)
        return [Crime(**crime) for crime in crimes_data]

    @staticmethod
    async def report_crime(crime_create: CrimeCreate) -> CrimeReport:
        """
        Registra un nuevo crimen en el sistema.
        
        Args:
            crime_create: Datos del nuevo crimen
            
        Returns:
            Reporte del crimen registrado con análisis
        """
        import uuid
        
        crime_data = {
            "id": f"crime_{uuid.uuid4().hex[:8]}",
            "date": crime_create.date,
            "crime_type": crime_create.crime_type,
            "severity": crime_create.severity,
            "description": crime_create.description or "",
            "location_id": crime_create.location_id,
            "perpetrator_id": crime_create.perpetrator_id,
        }
        
        # Registrar en base de datos
        crime_result = await CrimeRepository.create(crime_data)
        crime = Crime(**crime_result)
        
        # Calcular impacto en riesgo local
        location = await LocationRepository.find_by_id(crime_create.location_id)
        risk_impact = CrimeService._calculate_risk_impact(crime_create.severity, location)
        
        # Obtener ciudadanos relacionados
        related = await CrimeRepository.find_related_citizens(crime_result["id"])
        
        return CrimeReport(
            crime=crime,
            risk_impact=risk_impact,
            related_citizens_count=len([c for c in related.values() if c]) if related else 0,
            investigation_status="OPEN"
        )

    @staticmethod
    async def get_crime_statistics(days: int = 365) -> CrimeStatistics:
        """
        Obtiene estadísticas agregadas de crímenes.
        
        Args:
            days: Período de análisis
            
        Returns:
            Estadísticas completas de crímenes
        """
        stats = await CrimeRepository.get_statistics(days)
        crime_counts = await CrimeRepository.count_by_type()
        
        return CrimeStatistics(
            total_crimes=stats.get("total_crimes", 0),
            crimes_by_type=crime_counts or {},
            average_severity=stats.get("average_severity", 0.0),
            highest_severity=stats.get("highest_severity", 0),
            locations_with_crimes=stats.get("unique_types", 0),
            total_suspects=0,  # Se calcularía desde Ciudadanos
            date_range=f"Last {days} days"
        )

    @staticmethod
    async def get_crime_timeline(days: int = 30) -> List[CrimeTimeline]:
        """
        Obtiene línea temporal de crímenes.
        
        Args:
            days: Número de días para el análisis
            
        Returns:
            Timeline de actividad criminal
        """
        timeline_data = await CrimeRepository.get_timeline(days)
        timeline_entries = []
        
        for entry in timeline_data:
            # Determinar tendencia (simplificado para demostración)
            trend = "STABLE"  # En producción, se compararía con período anterior
            
            timeline_entries.append(CrimeTimeline(
                date=entry["date"],
                crimes_count=entry["crimes_count"],
                total_severity=entry["total_severity"] or 0,
                affected_locations=entry["affected_locations"] or 0,
                primary_crime_type="Various",
                trend=trend
            ))
        
        return timeline_entries

    @staticmethod
    async def mark_investigated(crime_id: str) -> bool:
        """
        Marca un crimen como investigado.
        
        Args:
            crime_id: ID del crimen
            
        Returns:
            True si se actualizó exitosamente
        """
        return await CrimeRepository.mark_investigated(crime_id)

    @staticmethod
    def _calculate_risk_impact(severity: int, location: Optional[Dict[str, Any]]) -> float:
        """
        Calcula el impacto en riesgo local de un crimen.
        
        Args:
            severity: Severidad del crimen [1-10]
            location: Datos de la ubicación (opcional)
            
        Returns:
            Impacto en riesgo [0.0-1.0]
        """
        # Score base de severidad normalizado
        severity_score = severity / 10.0  # [0.0-1.0]
        
        # Factor de ubicación (más riesgo si ya hay antecedentes)
        location_factor = 1.0
        if location:
            crime_count = location.get("historical_crime_count", 0)
            if crime_count > 10:
                location_factor = 1.5  # Amplificar riesgo en hotspots
            elif crime_count > 5:
                location_factor = 1.2
        
        # Impacto final normalizado
        risk_impact = min(1.0, severity_score * location_factor)
        
        return round(risk_impact, 3)
