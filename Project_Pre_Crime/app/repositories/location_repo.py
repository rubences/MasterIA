"""
LocationRepository - Capa de acceso a datos para Ubicaciones.

Responsabilidades:
  - Ejecutar queries Cypher para CRUD de Location
  - Encontrar hotspots de crimen
  - Calcular estadísticas de ubicaciones
  - Enriquecer datos de ubicaciones con información de crímenes
"""
from typing import List, Optional, Dict, Any
from app.core.database import db_manager
from datetime import datetime, timedelta


class LocationRepository:
    """
    Repository para acceso a datos de Ubicaciones en Neo4j.
    Implementa patrón de acceso a datos con queries explícitas.
    """

    @staticmethod
    async def find_all() -> List[Dict[str, Any]]:
        """
        Obtiene todas las ubicaciones de la ciudad.
        
        Returns:
            Lista de ubicaciones con estadísticas de crímenes
        """
        query = """
        MATCH (loc:Location)
        OPTIONAL MATCH (loc)-[:LOCATION_OF]-(crime:Crime)
        WITH loc, COUNT(DISTINCT crime) as crime_count
        RETURN {
            id: loc.id,
            name: loc.name,
            location_type: loc.location_type,
            env_risk: loc.env_risk,
            latitude: loc.latitude,
            longitude: loc.longitude,
            historical_crime_count: crime_count,
            recent_crime_count: 0  # Será calculado en servicio
        } as location
        ORDER BY crime_count DESC
        """
        records = await db_manager.query(query)
        return [record.data()["location"] for record in records]

    @staticmethod
    async def find_by_id(location_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene una ubicación por su ID.
        
        Args:
            location_id: ID de la ubicación
            
        Returns:
            Ubicación con detalles completos, o None si no existe
        """
        query = """
        MATCH (loc:Location {id: $location_id})
        OPTIONAL MATCH (loc)-[:LOCATION_OF]-(crime:Crime)
        WITH loc, COUNT(DISTINCT crime) as crime_count
        OPTIONAL MATCH (loc)-[:LOCATION_OF]-(recent_crime:Crime)
        WHERE recent_crime.date >= date() - duration('P30D')
        WITH loc, crime_count, COUNT(DISTINCT recent_crime) as recent_count
        RETURN {
            id: loc.id,
            name: loc.name,
            location_type: loc.location_type,
            env_risk: loc.env_risk,
            latitude: loc.latitude,
            longitude: loc.longitude,
            historical_crime_count: crime_count,
            recent_crime_count: recent_count,
            risk_level: CASE 
                WHEN (crime_count + loc.env_risk * 10) >= 15 THEN 'CRITICAL'
                WHEN (crime_count + loc.env_risk * 10) >= 10 THEN 'HIGH'
                WHEN (crime_count + loc.env_risk * 10) >= 5 THEN 'MEDIUM'
                ELSE 'LOW'
            END
        } as location
        """
        result = await db_manager.query(query, {"location_id": location_id})
        if result:
            return result[0].data()["location"]
        return None

    @staticmethod
    async def find_hotspots(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Encuentra las ubicaciones con mayor actividad criminal (hotspots).
        
        Args:
            limit: Número máximo de hotspots a retornar
            
        Returns:
            Lista de ubicaciones ordenadas por riesgo/actividad
        """
        query = """
        MATCH (loc:Location)
        OPTIONAL MATCH (loc)-[:LOCATION_OF]-(crime:Crime)
        WITH loc, COUNT(DISTINCT crime) as crime_count,
             SUM(CASE WHEN crime.severity IS NOT NULL THEN crime.severity ELSE 0 END) as total_severity
        WITH loc, crime_count, 
             CASE WHEN crime_count > 0 THEN total_severity / crime_count ELSE 0 END as avg_severity
        WITH loc, crime_count, avg_severity,
             ((crime_count * 0.6) + (avg_severity * 0.3) + (loc.env_risk * 10 * 0.1)) as risk_score
        OPTIONAL MATCH (loc)-[:LOCATION_OF]-(last_crime:Crime)
        WITH loc, crime_count, avg_severity, risk_score, 
             MAX(last_crime.date) as last_crime_date
        ORDER BY risk_score DESC
        LIMIT $limit
        RETURN {
            id: loc.id,
            name: loc.name,
            location_type: loc.location_type,
            crime_count: crime_count,
            severity_total: COALESCE(SUM(DISTINCT last_crime.severity), 0),
            average_severity: avg_severity,
            risk_score: ROUND(risk_score, 3),
            last_crime_date: COALESCE(last_crime_date, null)
        } as hotspot
        """
        records = await db_manager.query(query, {"limit": limit})
        return [record.data()["hotspot"] for record in records]

    @staticmethod
    async def find_by_name(name: str) -> Optional[Dict[str, Any]]:
        """
        Encuentra una ubicación por nombre (búsqueda parcial).
        
        Args:
            name: Parte del nombre de la ubicación
            
        Returns:
            Primera ubicación que coincida con el nombre
        """
        query = """
        MATCH (loc:Location)
        WHERE loc.name CONTAINS $name
        OPTIONAL MATCH (loc)-[:LOCATION_OF]-(crime:Crime)
        WITH loc, COUNT(DISTINCT crime) as crime_count
        RETURN {
            id: loc.id,
            name: loc.name,
            location_type: loc.location_type,
            env_risk: loc.env_risk,
            latitude: loc.latitude,
            longitude: loc.longitude,
            historical_crime_count: crime_count,
            recent_crime_count: 0
        } as location
        LIMIT 1
        """
        result = await db_manager.query(query, {"name": name})
        if result:
            return result[0].data()["location"]
        return None

    @staticmethod
    async def create(location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una nueva ubicación en Neo4j.
        
        Args:
            location_data: Diccionario con id, name, location_type, env_risk, latitude, longitude
            
        Returns:
            Ubicación creada
        """
        query = """
        CREATE (loc:Location {
            id: $id,
            name: $name,
            location_type: $location_type,
            env_risk: $env_risk,
            latitude: $latitude,
            longitude: $longitude,
            created_at: timestamp()
        })
        RETURN {
            id: loc.id,
            name: loc.name,
            location_type: loc.location_type,
            env_risk: loc.env_risk,
            latitude: loc.latitude,
            longitude: loc.longitude,
            historical_crime_count: 0,
            recent_crime_count: 0,
            risk_level: 'LOW'
        } as location
        """
        result = await db_manager.execute_write(query, location_data)
        if result:
            return result[0].data()["location"]
        raise Exception("Failed to create location")

    @staticmethod
    async def count_all() -> int:
        """Cuenta el total de ubicaciones en la ciudad."""
        query = "MATCH (loc:Location) RETURN COUNT(loc) as total"
        result = await db_manager.query(query)
        return result[0].data()["total"]

    @staticmethod
    async def get_statistics() -> Dict[str, Any]:
        """
        Obtiene estadísticas agregadas de todas las ubicaciones.
        
        Returns:
            Diccionario con estadísticas globales
        """
        query = """
        MATCH (loc:Location)
        OPTIONAL MATCH (loc)-[:LOCATION_OF]-(crime:Crime)
        WITH COUNT(DISTINCT loc) as total_locations,
             COUNT(DISTINCT crime) as total_crimes,
             COUNT(DISTINCT CASE WHEN crime IS NOT NULL THEN loc END) as locations_with_crimes,
             AVG(loc.env_risk) as avg_env_risk
        OPTIONAL MATCH (crime:Crime)
        WITH total_locations, total_crimes, locations_with_crimes, avg_env_risk,
             crime.crime_type as crime_type
        RETURN {
            total_locations: total_locations,
            locations_with_crimes: locations_with_crimes,
            average_env_risk: ROUND(avg_env_risk, 3),
            total_crime_incidents: total_crimes,
            highest_risk_location: null  # Será enriquecido en servicio
        } as statistics
        """
        result = await db_manager.query(query)
        if result:
            return result[0].data()["statistics"]
        return {
            "total_locations": 0,
            "locations_with_crimes": 0,
            "average_env_risk": 0.0,
            "total_crime_incidents": 0,
            "highest_risk_location": None
        }

    @staticmethod
    async def find_nearby_crimes(location_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Obtiene crímenes recientes en una ubicación.
        
        Args:
            location_id: ID de la ubicación
            days: Número de días hacia atrás para buscar
            
        Returns:
            Lista de crímenes recientes
        """
        query = """
        MATCH (loc:Location {id: $location_id})-[:LOCATION_OF]-(crime:Crime)
        WHERE crime.date >= date() - duration('P' + $days + 'D')
        RETURN {
            id: crime.id,
            date: crime.date,
            crime_type: crime.crime_type,
            severity: crime.severity,
            description: crime.description
        } as crime
        ORDER BY crime.date DESC
        """
        records = await db_manager.query(query, {"location_id": location_id, "days": days})
        return [record.data()["crime"] for record in records]
