"""
CrimeRepository - Capa de acceso a datos para Eventos Criminales.

Responsabilidades:
  - Ejecutar queries Cypher para CRUD de Crime
  - Buscar crímenes por período, tipo, ubicación
  - Calcular estadísticas y tendencias criminales
  - Registrar relaciones entre crímenes y perpetradores
"""
from typing import List, Optional, Dict, Any
from app.core.database import db_manager
from datetime import datetime, date, timedelta


class CrimeRepository:
    """
    Repository para acceso a datos de Eventos Criminales en Neo4j.
    Implementa patrón de acceso a datos con queries explícitas.
    """

    @staticmethod
    async def find_all(limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene todos los crímenes registrados.
        
        Args:
            limit: Número máximo de registros
            
        Returns:
            Lista de crímenes ordenados por fecha descendente
        """
        query = """
        MATCH (crime:Crime)
        OPTIONAL MATCH (crime)-[:PERPETRATOR_OF]-(perp:Citizen)
        OPTIONAL MATCH (crime)-[:LOCATION_OF]-(loc:Location)
        RETURN {
            id: crime.id,
            date: crime.date,
            crime_type: crime.crime_type,
            severity: crime.severity,
            description: crime.description,
            perpetrator_name: perp.name,
            location_name: loc.name,
            location_type: loc.location_type,
            created_at: crime.created_at
        } as crime
        ORDER BY crime.date DESC
        LIMIT $limit
        """
        records = await db_manager.query(query, {"limit": limit})
        return [record.data()["crime"] for record in records]

    @staticmethod
    async def find_by_id(crime_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un crimen específico por ID.
        
        Args:
            crime_id: ID del crimen
            
        Returns:
            Detalle completo del crimen, o None si no existe
        """
        query = """
        MATCH (crime:Crime {id: $crime_id})
        OPTIONAL MATCH (crime)-[:PERPETRATOR_OF]-(perp:Citizen)
        OPTIONAL MATCH (crime)-[:LOCATION_OF]-(loc:Location)
        RETURN {
            id: crime.id,
            date: crime.date,
            crime_type: crime.crime_type,
            severity: crime.severity,
            description: crime.description,
            perpetrator_name: perp.name,
            location_name: loc.name,
            location_type: loc.location_type,
            created_at: crime.created_at
        } as crime
        """
        result = await db_manager.query(query, {"crime_id": crime_id})
        if result:
            return result[0].data()["crime"]
        return None

    @staticmethod
    async def find_recent_activity(days: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene actividad criminal reciente.
        
        Args:
            days: Número de días hacia atrás
            limit: Número máximo de registros
            
        Returns:
            Lista de crímenes recientes ordenados por fecha
        """
        query = """
        MATCH (crime:Crime)
        WHERE crime.date >= date() - duration('P' + $days + 'D')
        OPTIONAL MATCH (crime)-[:PERPETRATOR_OF]-(perp:Citizen)
        OPTIONAL MATCH (crime)-[:LOCATION_OF]-(loc:Location)
        RETURN {
            id: crime.id,
            date: crime.date,
            crime_type: crime.crime_type,
            severity: crime.severity,
            description: crime.description,
            perpetrator_name: perp.name,
            location_name: loc.name,
            location_type: loc.location_type,
            created_at: crime.created_at
        } as crime
        ORDER BY crime.date DESC
        LIMIT $limit
        """
        records = await db_manager.query(query, {"days": days, "limit": limit})
        return [record.data()["crime"] for record in records]

    @staticmethod
    async def find_by_type(crime_type: str, days: int = 90) -> List[Dict[str, Any]]:
        """
        Encuentra crímenes de un tipo específico.
        
        Args:
            crime_type: Tipo de crimen (Robbery, Assault, etc.)
            days: Período de búsqueda
            
        Returns:
            Lista de crímenes del tipo especificado
        """
        query = """
        MATCH (crime:Crime {crime_type: $crime_type})
        WHERE crime.date >= date() - duration('P' + $days + 'D')
        OPTIONAL MATCH (crime)-[:PERPETRATOR_OF]-(perp:Citizen)
        OPTIONAL MATCH (crime)-[:LOCATION_OF]-(loc:Location)
        RETURN {
            id: crime.id,
            date: crime.date,
            crime_type: crime.crime_type,
            severity: crime.severity,
            perpetrator_name: perp.name,
            location_name: loc.name
        } as crime
        ORDER BY crime.date DESC
        """
        records = await db_manager.query(query, {"crime_type": crime_type, "days": days})
        return [record.data()["crime"] for record in records]

    @staticmethod
    async def find_by_location(location_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene crímenes ocurridos en una ubicación específica.
        
        Args:
            location_id: ID de la ubicación
            limit: Número máximo de registros
            
        Returns:
            Lista de crímenes en la ubicación
        """
        query = """
        MATCH (loc:Location {id: $location_id})-[:LOCATION_OF]-(crime:Crime)
        OPTIONAL MATCH (crime)-[:PERPETRATOR_OF]-(perp:Citizen)
        RETURN {
            id: crime.id,
            date: crime.date,
            crime_type: crime.crime_type,
            severity: crime.severity,
            description: crime.description,
            perpetrator_name: perp.name
        } as crime
        ORDER BY crime.date DESC
        LIMIT $limit
        """
        records = await db_manager.query(query, {"location_id": location_id, "limit": limit})
        return [record.data()["crime"] for record in records]

    @staticmethod
    async def find_by_perpetrator(perpetrator_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene crímenes cometidos por un perpetrador específico.
        
        Args:
            perpetrator_id: ID del ciudadano/perpetrador
            limit: Número máximo de registros
            
        Returns:
            Historial criminal del perpetrador
        """
        query = """
        MATCH (perp:Citizen {id: $perpetrator_id})-[:PERPETRATOR_OF]-(crime:Crime)
        OPTIONAL MATCH (crime)-[:LOCATION_OF]-(loc:Location)
        RETURN {
            id: crime.id,
            date: crime.date,
            crime_type: crime.crime_type,
            severity: crime.severity,
            location_name: loc.name
        } as crime
        ORDER BY crime.date DESC
        LIMIT $limit
        """
        records = await db_manager.query(query, {"perpetrator_id": perpetrator_id, "limit": limit})
        return [record.data()["crime"] for record in records]

    @staticmethod
    async def create(crime_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registra un nuevo crimen en el sistema.
        
        Args:
            crime_data: Diccionario con id, date, crime_type, severity, description, 
                       location_id, perpetrator_id (opcional)
            
        Returns:
            Crimen creado
        """
        query = """
        MATCH (loc:Location {id: $location_id})
        CREATE (crime:Crime {
            id: $id,
            date: $date,
            crime_type: $crime_type,
            severity: $severity,
            description: $description,
            created_at: timestamp()
        })
        CREATE (loc)-[:LOCATION_OF]->(crime)
        WITH crime
        OPTIONAL MATCH (perp:Citizen {id: $perpetrator_id})
        CREATE (perp)-[:PERPETRATOR_OF]->(crime)
        RETURN {
            id: crime.id,
            date: crime.date,
            crime_type: crime.crime_type,
            severity: crime.severity,
            created_at: crime.created_at
        } as crime
        """
        result = await db_manager.execute_write(query, crime_data)
        if result:
            return result[0].data()["crime"]
        raise Exception("Failed to create crime record")

    @staticmethod
    async def count_all() -> int:
        """Cuenta el total de crímenes registrados."""
        query = "MATCH (crime:Crime) RETURN COUNT(crime) as total"
        result = await db_manager.query(query)
        return result[0].data()["total"]

    @staticmethod
    async def count_by_type() -> Dict[str, int]:
        """
        Cuenta crímenes agrupados por tipo.
        
        Returns:
            Diccionario {crime_type: count}
        """
        query = """
        MATCH (crime:Crime)
        RETURN crime.crime_type as crime_type, COUNT(crime) as count
        ORDER BY count DESC
        """
        records = await db_manager.query(query)
        return {record.data()["crime_type"]: record.data()["count"] for record in records}

    @staticmethod
    async def get_statistics(days: int = 365) -> Dict[str, Any]:
        """
        Calcula estadísticas agregadas de crímenes.
        
        Args:
            days: Período de análisis
            
        Returns:
            Diccionario con estadísticas globales
        """
        query = """
        MATCH (crime:Crime)
        WHERE crime.date >= date() - duration('P' + $days + 'D')
        WITH COUNT(crime) as total_crimes,
             AVG(crime.severity) as avg_severity,
             MAX(crime.severity) as highest_severity,
             COUNT(DISTINCT crime.crime_type) as unique_types
        RETURN {
            total_crimes: total_crimes,
            average_severity: ROUND(avg_severity, 2),
            highest_severity: highest_severity,
            unique_types: unique_types,
            total_suspects: 0  # Será enriquecido en servicio
        } as statistics
        """
        result = await db_manager.query(query, {"days": days})
        if result:
            return result[0].data()["statistics"]
        return {
            "total_crimes": 0,
            "average_severity": 0.0,
            "highest_severity": 0,
            "unique_types": 0,
            "total_suspects": 0
        }

    @staticmethod
    async def get_timeline(period_days: int = 30) -> List[Dict[str, Any]]:
        """
        Obtiene línea temporal de crímenes por día.
        
        Args:
            period_days: Número de días para el análisis
            
        Returns:
            Lista de estadísticas por día
        """
        query = """
        MATCH (crime:Crime)
        WHERE crime.date >= date() - duration('P' + $period_days + 'D')
        WITH crime.date as date, COUNT(crime) as crimes_count,
             SUM(crime.severity) as total_severity,
             COUNT(DISTINCT crime.crime_type) as unique_types
        RETURN {
            date: date,
            crimes_count: crimes_count,
            total_severity: total_severity,
            affected_locations: unique_types
        } as timeline_entry
        ORDER BY date DESC
        """
        records = await db_manager.query(query, {"period_days": period_days})
        return [record.data()["timeline_entry"] for record in records]

    @staticmethod
    async def mark_investigated(crime_id: str) -> bool:
        """
        Marca un crimen como investigado.
        
        Args:
            crime_id: ID del crimen
            
        Returns:
            True si se actualizó exitosamente
        """
        query = """
        MATCH (crime:Crime {id: $crime_id})
        SET crime.investigated = true, crime.investigated_at = timestamp()
        RETURN crime.id
        """
        result = await db_manager.execute_write(query, {"crime_id": crime_id})
        return bool(result)

    @staticmethod
    async def find_related_citizens(crime_id: str) -> List[Dict[str, Any]]:
        """
        Encuentra ciudadanos relacionados a un crimen.
        Incluye perpetrador, testigos y víctimas si existen.
        
        Args:
            crime_id: ID del crimen
            
        Returns:
            Lista de ciudadanos relacionados
        """
        query = """
        MATCH (crime:Crime {id: $crime_id})
        OPTIONAL MATCH (perp:Citizen)-[:PERPETRATOR_OF]->(crime)
        OPTIONAL MATCH (crime)-[:HAS_VICTIM]->(victim:Citizen)
        OPTIONAL MATCH (crime)-[:HAS_WITNESS]->(witness:Citizen)
        WITH DISTINCT crime, perp, victim, witness
        RETURN {
            perpetrator: CASE WHEN perp IS NOT NULL THEN {id: perp.id, name: perp.name} ELSE null END,
            victim: CASE WHEN victim IS NOT NULL THEN {id: victim.id, name: victim.name} ELSE null END,
            witnesses: COLLECT(DISTINCT CASE WHEN witness IS NOT NULL THEN {id: witness.id, name: witness.name} END)
        } as related_citizens
        """
        result = await db_manager.query(query, {"crime_id": crime_id})
        if result:
            return result[0].data()["related_citizens"]
        return {"perpetrator": None, "victim": None, "witnesses": []}
