"""
Schemas Pydantic para validación de datos de entrada/salida.
Equivalente a DTOs en Spring Boot.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CitizenBase(BaseModel):
    """Schema base de un ciudadano."""
    id: int = Field(..., description="ID único del ciudadano")
    name: str = Field(..., description="Nombre completo")
    status: str = Field(default="ACTIVE", description="Estado del ciudadano")

class CitizenFeatureVector(CitizenBase):
    """Ciudadano con vector de características para inferencia."""
    criminal_degree: int = Field(0, description="Número de contactos criminales")
    risk_seed: float = Field(0.0, description="Riesgo base del perfil")
    job_vector: List[float] = Field(default_factory=list, description="Vector one-hot del trabajo")
    age_normalized: Optional[float] = Field(None, description="Edad normalizada [0,1]")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 42,
                "name": "John Anderton",
                "status": "ACTIVE",
                "criminal_degree": 3,
                "risk_seed": 0.45,
                "job_vector": [0.0, 1.0, 0.0],
                "age_normalized": 0.35
            }
        }

class PredictionOutput(BaseModel):
    """Salida de una predicción del sistema Pre-Crime."""
    subject_id: int = Field(..., description="ID del ciudadano analizado")
    subject_name: str = Field(..., description="Nombre del ciudadano")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probabilidad de cometer crimen")
    verdict: str = Field(..., description="Veredicto: SAFE | WATCHLIST | INTERVENE")
    confidence: float = Field(..., description="Nivel de confianza del modelo")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="Timestamp del análisis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject_id": 42,
                "subject_name": "John Anderton",
                "probability": 0.92,
                "verdict": "INTERVENE",
                "confidence": 0.88,
                "analyzed_at": "2026-01-22T16:30:00"
            }
        }

class HealthCheck(BaseModel):
    """Estado del sistema."""
    status: str
    precogs: str
    database: str
    models_loaded: bool

class CitizenSearchResult(BaseModel):
    """Resultado de búsqueda de ciudadanos."""
    id: int
    name: str
    born: Optional[int]
    job: Optional[str]
    criminal_degree: int
    risk_seed: float
