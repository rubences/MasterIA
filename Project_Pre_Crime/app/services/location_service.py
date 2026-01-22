"""
LocationService - Capa de lógica de negocio para Ubicaciones.

Responsabilidades:
  - Enriquecer datos de ubicaciones con contexto criminal
  - Calcular niveles de riesgo
  - Validar datos antes de persistencia
  - Orquestar operaciones complejas
"""
from typing import List, Optional, Dict, Any
from app.repositories.location_repo import LocationRepository
from app.repositories.crime_repo import CrimeRepository
from app.models.schemas_location import LocationCreate, Location, LocationHotspot


class LocationService:
    """
    Servicio de lógica de negocio para Ubicaciones.
    Implementa reglas de negocio y transformaciones de datos.
    """

    @staticmethod
    async def get_all_locations() -> List[Location]:
        """
        Obtiene todas las ubicaciones de la ciudad.
        
        Returns:
            Lista de ubicaciones con estadísticas enriquecidas
        """
        locations_data = await LocationRepository.find_all()
        locations = []
        
        for loc_data in locations_data:
            # Enriquecer con crímenes recientes
            recent_crimes = await LocationRepository.find_nearby_crimes(loc_data["id"], days=30)
            loc_data["recent_crime_count"] = len(recent_crimes)
            
            # Calcular nivel de riesgo
            loc_data["risk_level"] = LocationService._calculate_risk_level(
                loc_data["historical_crime_count"],
                loc_data["recent_crime_count"],
                loc_data["env_risk"]
            )
            
            locations.append(Location(**loc_data))
        
        return locations

    @staticmethod
    async def get_location(location_id: str) -> Optional[Location]:
        """
        Obtiene una ubicación específica con detalles completos.
        
        Args:
            location_id: ID de la ubicación
            
        Returns:
            Ubicación enriquecida, o None si no existe
        """
        loc_data = await LocationRepository.find_by_id(location_id)
        if not loc_data:
            return None
        
        # Enriquecer con datos de crímenes recientes
        recent_crimes = await LocationRepository.find_nearby_crimes(location_id, days=30)
        loc_data["recent_crime_count"] = len(recent_crimes)
        
        # Calcular riesgo
        loc_data["risk_level"] = LocationService._calculate_risk_level(
            loc_data["historical_crime_count"],
            loc_data["recent_crime_count"],
            loc_data["env_risk"]
        )
        
        return Location(**loc_data)

    @staticmethod
    async def search_locations(name: str) -> Optional[Location]:
        """
        Busca una ubicación por nombre.
        
        Args:
            name: Parte del nombre de la ubicación
            
        Returns:
            Primera ubicación que coincida
        """
        loc_data = await LocationRepository.find_by_name(name)
        if not loc_data:
            return None
        
        recent_crimes = await LocationRepository.find_nearby_crimes(loc_data["id"], days=30)
        loc_data["recent_crime_count"] = len(recent_crimes)
        loc_data["risk_level"] = LocationService._calculate_risk_level(
            loc_data["historical_crime_count"],
            loc_data["recent_crime_count"],
            loc_data["env_risk"]
        )
        
        return Location(**loc_data)

    @staticmethod
    async def get_hotspots(limit: int = 10) -> List[LocationHotspot]:
        """
        Obtiene las ubicaciones de mayor riesgo criminal.
        
        Args:
            limit: Número máximo de hotspots
            
        Returns:
            Lista de hotspots ordenados por riesgo
        """
        hotspots_data = await LocationRepository.find_hotspots(limit)
        hotspots = []
        
        for hotspot in hotspots_data:
            # Asegurar que risk_score está normalizado
            if not 0.0 <= hotspot.get("risk_score", 0) <= 1.0:
                hotspot["risk_score"] = min(1.0, max(0.0, hotspot.get("risk_score", 0.5) / 100))
            
            hotspots.append(LocationHotspot(**hotspot))
        
        return hotspots

    @staticmethod
    async def get_location_crimes(location_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Obtiene histórico de crímenes en una ubicación.
        
        Args:
            location_id: ID de la ubicación
            days: Número de días hacia atrás
            
        Returns:
            Lista de crímenes recientes
        """
        return await LocationRepository.find_nearby_crimes(location_id, days)

    @staticmethod
    async def create_location(location_create: LocationCreate) -> Location:
        """
        Crea una nueva ubicación en el sistema.
        
        Args:
            location_create: Datos de la nueva ubicación
            
        Returns:
            Ubicación creada
        """
        import uuid
        
        location_data = {
            "id": f"loc_{uuid.uuid4().hex[:8]}",
            "name": location_create.name,
            "location_type": location_create.location_type,
            "env_risk": location_create.env_risk,
            "latitude": location_create.coordinates.latitude,
            "longitude": location_create.coordinates.longitude,
        }
        
        loc_data = await LocationRepository.create(location_data)
        return Location(
            **loc_data,
            risk_level=LocationService._calculate_risk_level(0, 0, location_create.env_risk)
        )

    @staticmethod
    async def get_statistics() -> Dict[str, Any]:
        """
        Obtiene estadísticas globales de ubicaciones.
        
        Returns:
            Diccionario con estadísticas agregadas
        """
        stats = await LocationRepository.get_statistics()
        
        # Enriquecer con información de hotspots
        hotspots = await LocationRepository.find_hotspots(limit=1)
        if hotspots:
            stats["highest_risk_location"] = hotspots[0]["name"]
        
        # Obtener tipos de crímenes más comunes
        crime_types = await CrimeRepository.count_by_type()
        if crime_types:
            stats["top_crime_type"] = max(crime_types.items(), key=lambda x: x[1])[0]
        
        return stats

    @staticmethod
    def _calculate_risk_level(crime_count: int, recent_count: int, env_risk: float) -> str:
        """
        Calcula el nivel de riesgo de una ubicación.
        
        Args:
            crime_count: Número total de crímenes históricos
            recent_count: Número de crímenes recientes (30 días)
            env_risk: Factor de riesgo ambiental [0.0-1.0]
            
        Returns:
            Nivel de riesgo: LOW | MEDIUM | HIGH | CRITICAL
        """
        # Score ponderado: 60% histórico, 30% reciente, 10% ambiental
        score = (crime_count * 0.6) + (recent_count * 0.3) + (env_risk * 10 * 0.1)
        
        if score >= 15:
            return "CRITICAL"
        elif score >= 10:
            return "HIGH"
        elif score >= 5:
            return "MEDIUM"
        else:
            return "LOW"
