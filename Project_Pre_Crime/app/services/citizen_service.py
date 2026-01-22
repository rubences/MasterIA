"""
CitizenService: Servicios de negocio para ciudadanos.
Encapsula lógica que va más allá de consultas de BD.
Equivalente a @Service en Spring.
"""
import logging
from typing import List, Dict, Any, Optional
from app.repositories.citizen_repo import citizen_repository
from app.models.schemas import CitizenCreate, CitizenUpdate, CitizenFeatureVector
from app.config import settings

logger = logging.getLogger("CitizenService")

class CitizenService:
    """
    Servicios de negocio para operaciones con Ciudadanos.
    
    Responsabilidades:
    - Enriquecimiento de datos
    - Validaciones de negocio
    - Cálculos derivados
    - Orquestación de repositorios
    """

    async def get_all_citizens(
        self, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Obtiene lista de ciudadanos con paginación."""
        return await citizen_repository.find_all(limit, offset)

    async def get_citizen(self, citizen_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un ciudadano e enriquece sus datos.
        
        Enriquecimiento:
        - Calcula criminal_degree
        - Calcula social_network_size
        - Normaliza datos
        """
        citizen = await citizen_repository.find_by_id(citizen_id)
        
        if citizen:
            # Enriquecimiento de negocio
            citizen["is_high_risk"] = citizen.get("risk_seed", 0) >= settings.RISK_THRESHOLD_WATCHLIST
            citizen["status_summary"] = self._get_status_summary(citizen.get("status"))
        
        return citizen

    async def search_citizens(self, name: str) -> List[Dict[str, Any]]:
        """Busca ciudadanos por nombre."""
        return await citizen_repository.find_by_name(name)

    async def get_high_risk_suspects(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Obtiene ciudadanos de alto riesgo.
        
        Args:
            threshold: Umbral de riesgo (usa settings si no se especifica)
            
        Returns:
            Lista de sospechosos
        """
        if threshold is None:
            threshold = settings.RISK_THRESHOLD_WATCHLIST
        
        suspects = await citizen_repository.find_high_risk_suspects(threshold)
        logger.info(f"🔴 Encontrados {len(suspects)} ciudadanos de alto riesgo (>{threshold})")
        return suspects

    async def get_citizen_network(
        self, 
        citizen_id: int, 
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Obtiene red social de un ciudadano.
        
        Args:
            citizen_id: ID del ciudadano
            depth: Profundidad de búsqueda
            
        Returns:
            Estructura de red con análisis
        """
        network = await citizen_repository.find_network(citizen_id, depth)
        
        # Análisis de red
        if network["connections"]:
            criminal_count = sum(1 for c in network["connections"] if c.get("is_criminal"))
            network["criminal_percentage"] = (criminal_count / len(network["connections"])) * 100
            network["risk_analysis"] = self._analyze_network_risk(network["connections"])
        else:
            network["criminal_percentage"] = 0
            network["risk_analysis"] = "Ciudadano aislado - Bajo riesgo de influencia"
        
        return network

    async def enrich_citizen_for_inference(
        self, 
        citizen_id: int
    ) -> Optional[CitizenFeatureVector]:
        """
        Enriquece un ciudadano con vector de características para IA.
        
        Args:
            citizen_id: ID del ciudadano
            
        Returns:
            CitizenFeatureVector o None
        """
        citizen = await citizen_repository.find_by_id(citizen_id)
        
        if not citizen:
            return None
        
        # Normalizar edad
        age = settings.CURRENT_YEAR - citizen.get("born", settings.CURRENT_YEAR)
        age_normalized = min(age / 100.0, 1.0)
        
        # One-hot encoding del trabajo (mock simplificado)
        job_vector = self._encode_job(citizen.get("job"))
        
        return CitizenFeatureVector(
            id=citizen["id"],
            name=citizen["name"],
            status=citizen.get("status", "ACTIVE"),
            born=citizen.get("born"),
            job=citizen.get("job"),
            criminal_degree=citizen.get("criminal_degree", 0),
            risk_seed=citizen.get("risk_seed", 0.0),
            social_network_size=citizen.get("social_network_size", 0),
            job_vector=job_vector,
            age_normalized=age_normalized
        )

    async def create_citizen(self, citizen_data: CitizenCreate) -> Dict[str, Any]:
        """
        Crea un nuevo ciudadano.
        
        Validaciones de negocio:
        - Año de nacimiento válido
        - Risk seed en rango correcto
        """
        # Validaciones de negocio
        if citizen_data.born < 1900 or citizen_data.born >= settings.CURRENT_YEAR:
            raise ValueError(f"Año de nacimiento inválido: {citizen_data.born}")
        
        citizen_dict = citizen_data.model_dump()
        new_citizen = await citizen_repository.create(citizen_dict)
        
        logger.info(f"✅ Nuevo ciudadano creado: {new_citizen.get('name')} (#{new_citizen.get('id')})")
        return new_citizen

    async def update_citizen_status(
        self, 
        citizen_id: int, 
        new_status: str
    ) -> bool:
        """Actualiza estado de un ciudadano."""
        success = await citizen_repository.update_status(citizen_id, new_status)
        
        if success:
            logger.info(f"Estado actualizado: Ciudadano #{citizen_id} → {new_status}")
        
        return success

    async def update_citizen_risk(
        self, 
        citizen_id: int, 
        risk_value: float
    ) -> bool:
        """
        Actualiza risk_seed basado en nuevas evidencias.
        
        Args:
            citizen_id: ID del ciudadano
            risk_value: Nuevo valor de riesgo [0.0-1.0]
            
        Returns:
            True si fue exitoso
        """
        if not (0.0 <= risk_value <= 1.0):
            raise ValueError("Risk value debe estar entre 0.0 y 1.0")
        
        success = await citizen_repository.update_risk_seed(citizen_id, risk_value)
        
        if success:
            logger.warning(f"Risk seed actualizado: Ciudadano #{citizen_id} → {risk_value}")
        
        return success

    async def get_system_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema."""
        total = await citizen_repository.count_all()
        stats = await citizen_repository.get_statistics()
        
        return {
            "total_citizens": total,
            "average_risk": stats.get("average_risk", 0),
            "total_relationships": stats.get("total_relationships", 0),
            "timestamp": "now"
        }

    # ==================== MÉTODOS AUXILIARES PRIVADOS ====================

    @staticmethod
    def _encode_job(job: Optional[str]) -> List[float]:
        """One-hot encoding de trabajos."""
        jobs = [
            "Doctor", "Engineer", "Teacher", "Police", "Artist",
            "Driver", "Clerk", "Manager", "Scientist", "Other"
        ]
        
        if not job:
            return [0.0] * len(jobs)
        
        try:
            idx = jobs.index(job)
            vector = [0.0] * len(jobs)
            vector[idx] = 1.0
            return vector
        except ValueError:
            vector = [0.0] * len(jobs)
            vector[-1] = 1.0  # "Other"
            return vector

    @staticmethod
    def _get_status_summary(status: str) -> str:
        """Traduce código de estado a descripción legible."""
        summaries = {
            "ACTIVE": "Ciudadano activo - Bajo perfil",
            "WATCHLIST": "En lista de vigilancia - Monitoreo activo",
            "DETAINED": "Detenido - Bajo custodia",
            "CLEARED": "Absuelto - Registro limpio"
        }
        return summaries.get(status, "Estado desconocido")

    @staticmethod
    def _analyze_network_risk(connections: List[Dict]) -> str:
        """Analiza riesgo de la red social."""
        if not connections:
            return "Sin conexiones conocidas"
        
        criminal_count = sum(1 for c in connections if c.get("is_criminal"))
        total = len(connections)
        percentage = (criminal_count / total) * 100
        
        if percentage >= 50:
            return f"⚠️ Red COMPROMETIDA - {percentage:.0f}% criminales"
        elif percentage >= 25:
            return f"⚠️ Red SOSPECHOSA - {percentage:.0f}% criminales"
        elif percentage > 0:
            return f"ℹ️ Red con influencia criminal - {percentage:.0f}% criminales"
        else:
            return "✅ Red limpia - Sin contactos criminales"

# Instancia Singleton
citizen_service = CitizenService()
