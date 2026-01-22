"""
Pre-Crime Department API - Punto de Entrada Principal
Sistema de predicción de crímenes usando Graph Neural Networks.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.database import db_manager
from app.core.ai_engine import precog_system
from app.routers import citizens, predictions, locations, crimes
from app.models.schemas import HealthCheck
from app.config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PreCrimeAPI")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación.
    Startup: Conecta DB y carga modelos neuronales.
    Shutdown: Cierra conexiones limpiamente.
    """
    # ===== STARTUP =====
    logger.info("🔮 Iniciando Sistema Pre-Crime...")
    
    try:
        # Conectar a Neo4j
        db_manager.connect()
        db_connected = await db_manager.check_connection()
        if db_connected:
            logger.info("✅ Conexión a Neo4j establecida")
        else:
            logger.warning("⚠️ Neo4j no responde. API funcionará en modo limitado.")
        
        # Cargar modelos de IA
        precog_system.load_models()
        
        logger.info("🚀 Sistema Pre-Crime operativo")
        
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
        # Continuamos el arranque pero en modo degradado
    
    yield
    
    # ===== SHUTDOWN =====
    logger.info("🛑 Apagando sistema Pre-Crime...")
    await db_manager.close()
    logger.info("👋 Sistema detenido correctamente")

# Inicializar aplicación FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS (permitir acceso desde frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(citizens.router)
app.include_router(predictions.router)
app.include_router(locations.router)
app.include_router(crimes.router)

# ==================== Endpoints Raíz ====================

@app.get("/", tags=["Status"])
async def root():
    """Endpoint raíz - Verifica que el sistema esté activo."""
    return {
        "message": "Pre-Crime Department API",
        "status": "ONLINE",
        "version": settings.API_VERSION,
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthCheck, tags=["Status"])
async def health_check():
    """
    Health check completo del sistema.
    Verifica estado de DB y modelos cargados.
    """
    db_status = "CONNECTED" if await db_manager.check_connection() else "DISCONNECTED"
    models_status = "LOADED" if precog_system.models_loaded else "NOT_LOADED"
    
    overall_status = "ONLINE" if (db_status == "CONNECTED" and precog_system.models_loaded) else "DEGRADED"
    
    return HealthCheck(
        status=overall_status,
        precogs=models_status,
        database=db_status,
        models_loaded=precog_system.models_loaded
    )

@app.get("/info", tags=["Status"])
async def system_info():
    """Información del sistema y configuración."""
    return {
        "system": "Pre-Crime Department",
        "version": settings.API_VERSION,
        "ai_device": settings.DEVICE,
        "thresholds": {
            "watchlist": settings.RISK_THRESHOLD_WATCHLIST,
            "intervene": settings.RISK_THRESHOLD_INTERVENE
        },
        "endpoints": {
            "citizens": "/citizens",
            "predictions": "/precogs",
            "locations": "/locations",
            "crimes": "/crimes",
            "documentation": "/docs"
        }
    }

# ==================== Manejo de Errores Global ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Captura errores no manejados y devuelve respuesta estructurada."""
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    return {
        "error": "Internal Server Error",
        "detail": str(exc),
        "path": str(request.url)
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Iniciando servidor de desarrollo...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en desarrollo
        log_level="info"
    )
