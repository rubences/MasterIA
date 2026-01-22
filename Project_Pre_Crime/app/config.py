"""
Configuración de la aplicación Pre-Crime API.
Carga variables de entorno y define constantes globales.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuración global de la aplicación."""
    
    # Neo4j Database
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # AI Models
    MODEL_PATH: str = os.getenv("MODEL_PATH", "data/precrime_models.pt")
    DEVICE: str = os.getenv("DEVICE", "cpu")  # 'cpu' o 'cuda'
    
    # API Configuration
    API_TITLE: str = "Pre-Crime Department API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Sistema de predicción de crímenes usando Graph Neural Networks"
    
    # Risk Thresholds
    RISK_THRESHOLD_WATCHLIST: float = float(os.getenv("RISK_THRESHOLD_WATCHLIST", "0.60"))
    RISK_THRESHOLD_INTERVENE: float = float(os.getenv("RISK_THRESHOLD_INTERVENE", "0.85"))
    
    # Feature Engineering
    CURRENT_YEAR: int = int(os.getenv("CURRENT_YEAR", "2026"))

settings = Settings()
