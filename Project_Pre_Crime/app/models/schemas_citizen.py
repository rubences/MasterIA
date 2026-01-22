"""
Schemas Pydantic para Ciudadanos (Citizens).
Validación de datos para la entidad Citizens en Neo4j.

Arquitectura:
  CitizenBase: Definición base reutilizable
  Citizen: Lectura (GET) - Datos completos
  CitizenCreate: Escritura (POST) - Solo campos editables
  CitizenFeatureVector: Para inferencia con IA
  PredictionOutput: Resultado de análisis
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum

# ==================== ENUMERACIONES ====================

class CitizenStatus(str, Enum):
    """Estados posibles de un ciudadano."""
    ACTIVE = "ACTIVE"
    WATCHLIST = "WATCHLIST"
    DETAINED = "DETAINED"
    CLEARED = "CLEARED"

class VerdictType(str, Enum):
    """Tipos de veredictos Pre-Crime."""
    SAFE = "SAFE"
    WATCHLIST = "WATCHLIST"
    INTERVENE = "INTERVENE"

class JobType(str, Enum):
    """Categorías de trabajo."""
    DOCTOR = "Doctor"
    ENGINEER = "Engineer"
    TEACHER = "Teacher"
    POLICE = "Police"
    ARTIST = "Artist"
    DRIVER = "Driver"
    CLERK = "Clerk"
    MANAGER = "Manager"
    SCIENTIST = "Scientist"
    OTHER = "Other"

# ==================== DOMAIN MODELS ====================

class CitizenBase(BaseModel):
    """
    Definición base de un ciudadano.
    Campos comunes entre todas las variantes.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Nombre completo")
    status: CitizenStatus = Field(CitizenStatus.ACTIVE, description="Estado actual")
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True
    )

class CitizenCreate(CitizenBase):
    """
    Schema para CREAR un ciudadano.
    Equivalente a POST /citizens
    """
    born: int = Field(..., ge=1900, le=2025, description="Año de nacimiento")
    job: Optional[JobType] = Field(None, description="Profesión")
    risk_seed: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Riesgo inicial")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Anderton",
                "status": "ACTIVE",
                "born": 1985,
                "job": "Police",
                "risk_seed": 0.3
            }
        }

class Citizen(CitizenBase):
    """
    Schema para LEER un ciudadano.
    Equivalente a GET /citizens/{id}
    Incluye datos de Neo4j y métricas calculadas.
    """
    id: int = Field(..., description="ID único en Neo4j")
    born: int = Field(..., description="Año de nacimiento")
    job: Optional[str] = Field(None, description="Profesión")
    criminal_degree: int = Field(0, ge=0, description="Número de contactos criminales")
    risk_seed: float = Field(0.0, ge=0.0, le=1.0, description="Riesgo base del perfil")
    social_network_size: int = Field(0, ge=0, description="Número de conocidos")
    
    class Config:
        from_attributes = True  # Permite mapear desde ORM objects si fuera necesario
        json_schema_extra = {
            "example": {
                "id": 42,
                "name": "John Anderton",
                "status": "ACTIVE",
                "born": 1985,
                "job": "Police",
                "criminal_degree": 2,
                "risk_seed": 0.45,
                "social_network_size": 15
            }
        }

class CitizenUpdate(BaseModel):
    """
    Schema para ACTUALIZAR un ciudadano.
    Solo campos que se pueden editar tras creación.
    """
    status: Optional[CitizenStatus] = None
    risk_seed: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "WATCHLIST",
                "risk_seed": 0.75
            }
        }

class CitizenFeatureVector(Citizen):
    """
    Ciudadano enriquecido con vector de características para IA.
    Incluye normalizaciones y encodings para modelos PyTorch.
    """
    job_vector: List[float] = Field(default_factory=list, description="Vector one-hot del trabajo")
    age_normalized: Optional[float] = Field(None, ge=0.0, le=1.0, description="Edad normalizada")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 42,
                "name": "John Anderton",
                "status": "ACTIVE",
                "born": 1985,
                "job": "Police",
                "criminal_degree": 3,
                "risk_seed": 0.45,
                "social_network_size": 15,
                "job_vector": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "age_normalized": 0.41
            }
        }

# ==================== PREDICTION MODELS ====================

class PredictionOutput(BaseModel):
    """
    Resultado de una predicción Pre-Crime.
    Equivalente a una "Bola Roja" emitida por los Precogs.
    """
    subject_id: int = Field(..., description="ID del ciudadano analizado")
    subject_name: str = Field(..., description="Nombre del ciudadano")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probabilidad de cometer crimen")
    verdict: VerdictType = Field(..., description="Veredicto: SAFE | WATCHLIST | INTERVENE")
    confidence: float = Field(..., description="Nivel de confianza del modelo")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="Timestamp del análisis")
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "subject_id": 42,
                "subject_name": "John Anderton",
                "probability": 0.92,
                "verdict": "INTERVENE",
                "confidence": 0.88,
                "analyzed_at": "2026-01-22T16:30:00.123456"
            }
        }

class PredictionHistory(BaseModel):
    """Histórico de predicciones para un ciudadano."""
    citizen_id: int
    citizen_name: str
    total_predictions: int
    average_risk: float
    latest_verdict: VerdictType
    last_analyzed: datetime
