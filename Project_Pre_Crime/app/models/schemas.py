"""
Schemas Pydantic - Punto de entrada central para validación de datos (Domain Models).
Equivalentes a DTOs en Spring Boot / Entidades de dominio en Java.

NOTA: A partir de Parte 6, los schemas se organizan en archivos especializados:
  - schemas_citizen.py: Ciudadanos
  - schemas_location.py: Ubicaciones
  - schemas_crime.py: Eventos criminales

Este archivo re-exporta todos los schemas para compatibilidad retroactiva.
"""
from pydantic import BaseModel, Field
from typing import List, Dict

# ==================== RE-EXPORTAR DESDE MÓDULOS ESPECIALIZADOS ====================

# Ciudadanos
from app.models.schemas_citizen import (
    CitizenStatus,
    VerdictType,
    JobType,
    CitizenBase,
    CitizenCreate,
    Citizen,
    CitizenUpdate,
    CitizenFeatureVector,
    PredictionOutput,
    PredictionHistory,
)

# Ubicaciones
from app.models.schemas_location import (
    LocationType,
    Location,
    LocationCreate,
    LocationHotspot,
    LocationStatistics,
)

# Crímenes
from app.models.schemas_crime import (
    CrimeType,
    Crime,
    CrimeCreate,
    CrimeReport,
    CrimeStatistics,
    CrimeTimeline,
)

# ==================== SYSTEM MODELS ====================

class HealthCheck(BaseModel):
    """Estado integral del sistema."""
    status: str = Field(..., description="ONLINE | DEGRADED | OFFLINE")
    precogs: str = Field(..., description="LOADED | NOT_LOADED")
    database: str = Field(..., description="CONNECTED | DISCONNECTED")
    models_loaded: bool = Field(..., description="¿Modelos de IA cargados?")

class SystemInfo(BaseModel):
    """Información general del sistema."""
    version: str
    ai_device: str
    total_citizens: int
    high_risk_count: int
    thresholds: dict

class CitizenNetwork(BaseModel):
    """Red social de un ciudadano."""
    citizen_id: int
    citizen_name: str
    connections: List[Dict] = Field(description="Lista de amigos/conexiones")
    total_connections: int
    criminal_contacts: int

# ==================== CENTRAL EXPORTS ====================

__all__ = [
    # Citizens
    "CitizenStatus",
    "VerdictType",
    "JobType",
    "CitizenBase",
    "CitizenCreate",
    "Citizen",
    "CitizenUpdate",
    "CitizenFeatureVector",
    "PredictionOutput",
    "PredictionHistory",
    # Locations
    "LocationType",
    "Location",
    "LocationCreate",
    "LocationHotspot",
    "LocationStatistics",
    # Crimes
    "CrimeType",
    "Crime",
    "CrimeCreate",
    "CrimeReport",
    "CrimeStatistics",
    "CrimeTimeline",
    # System
    "HealthCheck",
    "SystemInfo",
    "CitizenNetwork",
]
