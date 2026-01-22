"""
Schemas para Locations (Ubicaciones).
Define estructura de datos para lugares en la ciudad donde ocurren crímenes.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum

class LocationType(str, Enum):
    """Tipos de ubicaciones en la ciudad."""
    BANK = "Bank"
    ALLEY = "Alley"
    PARK = "Park"
    STREET = "Street"
    STORE = "Store"
    PARKING = "Parking"
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"
    INDUSTRIAL = "Industrial"
    OTHER = "Other"

class CoordinateBase(BaseModel):
    """Coordenadas geográficas de una ubicación."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitud")
    longitude: float = Field(..., ge=-180, le=180, description="Longitud")

class LocationBase(BaseModel):
    """Definición base de una ubicación."""
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del lugar")
    location_type: LocationType = Field(..., description="Tipo de ubicación")
    env_risk: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0, 
        description="Factor de riesgo ambiental [0.0-1.0]"
    )
    
    model_config = ConfigDict(use_enum_values=True)

class LocationCreate(LocationBase):
    """Schema para CREAR una ubicación."""
    coordinates: CoordinateBase
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "First National Bank",
                "location_type": "Bank",
                "env_risk": 0.75,
                "coordinates": {
                    "latitude": 40.7128,
                    "longitude": -74.0060
                }
            }
        }

class Location(LocationBase):
    """
    Schema para LEER una ubicación.
    Incluye datos calculados del grafo.
    """
    id: str = Field(..., description="ID único de la ubicación")
    latitude: float = Field(..., description="Latitud")
    longitude: float = Field(..., description="Longitud")
    historical_crime_count: int = Field(
        default=0, 
        ge=0, 
        description="Número de crímenes históricos en este lugar"
    )
    recent_crime_count: int = Field(
        default=0,
        ge=0,
        description="Crímenes en los últimos 30 días"
    )
    risk_level: Optional[str] = Field(
        None,
        description="Nivel de riesgo calculado: LOW | MEDIUM | HIGH | CRITICAL"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "loc_001",
                "name": "First National Bank",
                "location_type": "Bank",
                "env_risk": 0.75,
                "latitude": 40.7128,
                "longitude": -74.0060,
                "historical_crime_count": 12,
                "recent_crime_count": 2,
                "risk_level": "HIGH"
            }
        }

class LocationHotspot(BaseModel):
    """Resultado de análisis de hotspots."""
    id: str
    name: str
    location_type: str
    crime_count: int
    severity_total: int = Field(description="Suma de severidades de crímenes")
    average_severity: float = Field(description="Severidad promedio")
    risk_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Score de riesgo calculado [0.0-1.0]"
    )
    last_crime_date: Optional[str] = Field(None, description="Fecha del último crimen")

class LocationStatistics(BaseModel):
    """Estadísticas agregadas de ubicaciones."""
    total_locations: int
    locations_with_crimes: int
    average_env_risk: float
    highest_risk_location: Optional[str]
    total_crime_incidents: int
    top_crime_type: Optional[str]
