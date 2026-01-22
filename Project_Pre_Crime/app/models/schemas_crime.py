"""
Schemas para Crimes (Eventos Criminales).
Define estructura de datos para crímenes registrados en la ciudad.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from enum import Enum

class CrimeType(str, Enum):
    """Tipos de crímenes."""
    ROBBERY = "Robbery"
    ASSAULT = "Assault"
    THEFT = "Theft"
    MURDER = "Murder"
    FRAUD = "Fraud"
    VANDALISM = "Vandalism"
    ARSON = "Arson"
    BURGLARY = "Burglary"
    DUI = "DUI"
    HOMICIDE = "Homicide"
    OTHER = "Other"

class CrimeBase(BaseModel):
    """Definición base de un evento criminal."""
    crime_type: CrimeType = Field(..., description="Tipo de crimen")
    severity: int = Field(
        ..., 
        ge=1, 
        le=10, 
        description="Severidad del crimen [1-10]"
    )
    description: Optional[str] = Field(
        None, 
        max_length=1000, 
        description="Descripción detallada del incidente"
    )
    
    model_config = ConfigDict(use_enum_values=True)

class CrimeCreate(CrimeBase):
    """Schema para CREAR un crimen."""
    date: date = Field(..., description="Fecha del incidente")
    perpetrator_id: Optional[int] = Field(None, description="ID del perpetrador")
    location_id: str = Field(..., description="ID de la ubicación")
    witnesses_count: Optional[int] = Field(None, ge=0, description="Número de testigos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-01-22",
                "crime_type": "Robbery",
                "severity": 8,
                "description": "Armed robbery at First National Bank",
                "perpetrator_id": 42,
                "location_id": "loc_001",
                "witnesses_count": 5
            }
        }

class Crime(CrimeBase):
    """
    Schema para LEER un crimen.
    Incluye datos enriquecidos del grafo.
    """
    id: str = Field(..., description="ID único del crimen")
    date: date = Field(..., description="Fecha del incidente")
    perpetrator_name: Optional[str] = Field(None, description="Nombre del perpetrador")
    location_name: str = Field(..., description="Nombre de la ubicación")
    location_type: str = Field(..., description="Tipo de ubicación")
    created_at: Optional[datetime] = Field(None, description="Timestamp de registro")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "crime_001",
                "date": "2026-01-22",
                "crime_type": "Robbery",
                "severity": 8,
                "description": "Armed robbery at First National Bank",
                "perpetrator_name": "John Anderton",
                "location_name": "First National Bank",
                "location_type": "Bank",
                "created_at": "2026-01-22T14:30:00"
            }
        }

class CrimeReport(BaseModel):
    """Reporte de actividad criminal."""
    crime: Crime
    risk_impact: float = Field(description="Impacto en el riesgo local [0.0-1.0]")
    related_citizens_count: int = Field(description="Ciudadanos conectados al crimen")
    investigation_status: str = Field(
        default="OPEN",
        description="Estado de la investigación: OPEN | CLOSED | PENDING"
    )

class CrimeStatistics(BaseModel):
    """Estadísticas agregadas de crímenes."""
    total_crimes: int
    crimes_by_type: dict
    average_severity: float
    highest_severity: int
    locations_with_crimes: int
    total_suspects: int
    date_range: str = Field(description="Rango de fechas de análisis")

class CrimeTimeline(BaseModel):
    """Línea temporal de crímenes para análisis histórico."""
    date: date
    crimes_count: int
    total_severity: int
    affected_locations: int
    primary_crime_type: str
    trend: str = Field(
        description="Tendencia: UP (↑) | DOWN (↓) | STABLE (→)"
    )
