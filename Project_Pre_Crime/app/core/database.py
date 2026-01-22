"""
Gestor de conexión a Neo4j con soporte asíncrono.
Patrón Singleton para compartir pool de conexiones.
"""
import logging
from neo4j import AsyncGraphDatabase
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PreCrimeDB")

class Neo4jManager:
    """Gestor singleton de conexión a Neo4j."""
    
    def __init__(self):
        self._driver = None
        self._uri = settings.NEO4J_URI
        self._user = settings.NEO4J_USER
        self._password = settings.NEO4J_PASSWORD

    def connect(self):
        """Inicializa el driver asíncrono de Neo4j."""
        if self._driver is None:
            try:
                self._driver = AsyncGraphDatabase.driver(
                    self._uri, 
                    auth=(self._user, self._password)
                )
                logger.info(f"🔌 Conectado a Neo4j en {self._uri}")
            except Exception as e:
                logger.error(f"❌ Fallo al conectar con Neo4j: {e}")
                raise e

    async def close(self):
        """Cierra el pool de conexiones de manera limpia."""
        if self._driver:
            await self._driver.close()
            logger.info("🔌 Conexión a Neo4j cerrada.")

    async def check_connection(self) -> bool:
        """Verifica que la base de datos responde (Health check)."""
        if self._driver:
            try:
                await self._driver.verify_connectivity()
                return True
            except Exception as e:
                logger.error(f"❌ Error de conectividad Neo4j: {e}")
                return False
        return False

    async def query(self, cypher_query: str, parameters: dict = None):
        """
        Ejecuta una consulta Cypher y devuelve resultados como lista de diccionarios.
        Maneja la sesión automáticamente.
        
        Args:
            cypher_query: Consulta Cypher a ejecutar
            parameters: Parámetros de la consulta
            
        Returns:
            Lista de diccionarios con los resultados
        """
        if self._driver is None:
            raise ConnectionError("El driver de Neo4j no está inicializado. Llama a connect() primero.")

        async with self._driver.session() as session:
            result = await session.run(cypher_query, parameters or {})
            records = await result.data()
            return records

    async def execute_write(self, cypher_query: str, parameters: dict = None):
        """
        Ejecuta una transacción de escritura (CREATE, MERGE, SET, DELETE).
        
        Args:
            cypher_query: Consulta Cypher de escritura
            parameters: Parámetros de la consulta
            
        Returns:
            Resultado de la operación
        """
        if self._driver is None:
            raise ConnectionError("El driver de Neo4j no está inicializado.")

        async with self._driver.session() as session:
            result = await session.run(cypher_query, parameters or {})
            summary = await result.consume()
            return summary

# Instancia global única (Singleton pattern)
db_manager = Neo4jManager()
