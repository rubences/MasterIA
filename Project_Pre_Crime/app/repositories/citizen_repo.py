"""
CitizenRepository: Patrón Repositorio para acceso a datos de Ciudadanos.
Encapsula toda la lógica de consultas Cypher.
Equivalente a CharacterRepository en Spring Data Neo4j.
"""
import logging
from typing import List, Optional, Dict, Any
from app.core.database import db_manager

logger = logging.getLogger("CitizenRepository")

class CitizenRepository:
    """
    Encapsula toda la lógica de acceso a datos para Ciudadanos.
    
    Principios:
    - Una consulta Cypher por método
    - Métodos descriptivos y reutilizables
    - Sin lógica de negocio (eso va en Services)
    - Transacciones explícitas
    """

    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Recupera todos los ciudadanos con paginación.
        
        Args:
            limit: Número máximo de resultados
            offset: Desplazamiento (para paginación)
            
        Returns:
            Lista de ciudadanos
        """
        query = """
        MATCH (c:Citizen)
        OPTIONAL MATCH (c)-[:KNOWS]-(friend:Citizen)
        WITH c, count(distinct friend) as social_network_size
        RETURN c.id as id, 
               c.name as name, 
               c.born as born,
               c.status as status, 
               c.job as job,
               c.risk_seed as risk_seed,
               social_network_size
        ORDER BY c.id
        SKIP $offset
        LIMIT $limit
        """
        return await db_manager.query(query, {"limit": limit, "offset": offset})

    async def find_by_id(self, citizen_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca un ciudadano específico e enriquece datos al vuelo.
        
        Args:
            citizen_id: ID del ciudadano
            
        Returns:
            Diccionario con datos del ciudadano o None
        """
        query = """
        MATCH (c:Citizen {id: $cid})
        // Calcular red social
        OPTIONAL MATCH (c)-[:KNOWS]-(friend:Citizen)
        WITH c, count(distinct friend) as social_network_size
        // Calcular grado criminal
        OPTIONAL MATCH (c)-[:KNOWS]-(criminal:Citizen)-[:COMMITTED_CRIME]->()
        WITH c, social_network_size, count(distinct criminal) as criminal_degree
        RETURN c.id as id, 
               c.name as name, 
               c.born as born,
               c.status as status, 
               c.job as job,
               c.risk_seed as risk_seed,
               social_network_size,
               criminal_degree
        """
        results = await db_manager.query(query, {"cid": citizen_id})
        return results[0] if results else None

    async def find_by_name(self, name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Búsqueda de ciudadanos por nombre (case-insensitive).
        
        Args:
            name: Término de búsqueda
            limit: Máximo de resultados
            
        Returns:
            Lista de ciudadanos que coinciden
        """
        query = """
        MATCH (c:Citizen)
        WHERE toLower(c.name) CONTAINS toLower($name)
        OPTIONAL MATCH (c)-[:KNOWS]-(friend:Citizen)
        WITH c, count(distinct friend) as social_network_size
        RETURN c.id as id,
               c.name as name,
               c.born as born,
               c.status as status,
               c.job as job,
               c.risk_seed as risk_seed,
               social_network_size
        ORDER BY c.name
        LIMIT $limit
        """
        return await db_manager.query(query, {"name": name, "limit": limit})

    async def find_high_risk_suspects(self, threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Ciudadanos de alto riesgo conectados a criminales.
        
        Esta es la query que Spring Data tendría dificultades generando automáticamente.
        Buscamos ciudadanos con high risk_seed Y contactos criminales.
        
        Args:
            threshold: Umbral mínimo de risk_seed
            
        Returns:
            Lista de ciudadanos sospechosos
        """
        query = """
        MATCH (c:Citizen)
        WHERE c.risk_seed > $threshold
        // Encontrar criminales conocidos
        MATCH (c)-[:KNOWS]-(associate:Citizen)-[*1..2]-(:Location)<-[:COMMITTED_CRIME]-(criminal)
        WITH DISTINCT c, 
             count(distinct criminal) as associated_criminals,
             count(distinct associate) as criminal_contacts
        WHERE associated_criminals > 0
        RETURN c.id as id,
               c.name as name,
               c.risk_seed as risk_seed,
               associated_criminals,
               criminal_contacts
        ORDER BY c.risk_seed DESC
        LIMIT 50
        """
        return await db_manager.query(query, {"threshold": threshold})

    async def find_network(self, citizen_id: int, depth: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        Extrae la red social de un ciudadano.
        
        Args:
            citizen_id: ID del ciudadano central
            depth: Profundidad de la red (1 = amigos directos, 2 = amigos de amigos)
            limit: Máximo de nodos a retornar
            
        Returns:
            Diccionario con estructura de red
        """
        if depth == 1:
            query = """
            MATCH (c:Citizen {id: $cid})
            OPTIONAL MATCH (c)-[:KNOWS]->(friend:Citizen)
            OPTIONAL MATCH (friend)-[:COMMITTED_CRIME]->()
            WITH friend, count(DISTINCT *) > 0 as has_crime
            RETURN friend.id as id,
                   friend.name as name,
                   friend.status as status,
                   has_crime as is_criminal
            LIMIT $limit
            """
        else:
            # Para depth > 1, usar path más complejos
            query = """
            MATCH (c:Citizen {id: $cid})
            MATCH (c)-[:KNOWS*1..%d]-(contact:Citizen)
            OPTIONAL MATCH (contact)-[:COMMITTED_CRIME]->()
            WITH DISTINCT contact, count(DISTINCT *) > 0 as has_crime
            RETURN contact.id as id,
                   contact.name as name,
                   contact.status as status,
                   has_crime as is_criminal
            LIMIT $limit
            """ % depth

        results = await db_manager.query(query, {"cid": citizen_id, "limit": limit})
        
        return {
            "citizen_id": citizen_id,
            "connections": results,
            "total": len(results)
        }

    async def count_all(self) -> int:
        """Retorna el número total de ciudadanos."""
        query = "MATCH (c:Citizen) RETURN count(c) as total"
        result = await db_manager.query(query)
        return result[0]["total"] if result else 0

    async def count_by_status(self, status: str) -> int:
        """Cuenta ciudadanos con cierto estado."""
        query = "MATCH (c:Citizen {status: $status}) RETURN count(c) as total"
        result = await db_manager.query(query, {"status": status})
        return result[0]["total"] if result else 0

    # ==================== MÉTODOS DE ESCRITURA ====================

    async def create(self, citizen_data: dict) -> Dict[str, Any]:
        """
        Crea un nuevo ciudadano en la BD.
        
        Args:
            citizen_data: Diccionario con datos {name, born, status, job, risk_seed}
            
        Returns:
            El ciudadano creado con ID asignado
        """
        query = """
        CREATE (c:Citizen {
            id: apoc.cuid.showId(),
            name: $name,
            born: $born,
            status: $status,
            job: $job,
            risk_seed: $risk_seed,
            created_at: datetime()
        })
        RETURN c.id as id, c.name as name, c.born as born, 
               c.status as status, c.job as job, c.risk_seed as risk_seed
        """
        result = await db_manager.query(query, citizen_data)
        return result[0] if result else None

    async def update_status(self, citizen_id: int, new_status: str) -> bool:
        """
        Actualiza el estado de un ciudadano.
        
        Args:
            citizen_id: ID del ciudadano
            new_status: Nuevo estado
            
        Returns:
            True si fue exitoso
        """
        query = """
        MATCH (c:Citizen {id: $cid})
        SET c.status = $status,
            c.updated_at = datetime()
        RETURN c.id
        """
        result = await db_manager.execute_write(query, {
            "cid": citizen_id,
            "status": new_status
        })
        return result is not None

    async def update_risk_seed(self, citizen_id: int, risk_value: float) -> bool:
        """Actualiza el risk_seed de un ciudadano."""
        query = """
        MATCH (c:Citizen {id: $cid})
        SET c.risk_seed = $risk,
            c.updated_at = datetime()
        RETURN c.id
        """
        result = await db_manager.execute_write(query, {
            "cid": citizen_id,
            "risk": risk_value
        })
        return result is not None

    async def delete(self, citizen_id: int) -> bool:
        """
        Elimina un ciudadano de la BD.
        ADVERTENCIA: También elimina sus relaciones.
        
        Args:
            citizen_id: ID del ciudadano a eliminar
            
        Returns:
            True si fue exitoso
        """
        query = """
        MATCH (c:Citizen {id: $cid})
        DETACH DELETE c
        """
        result = await db_manager.execute_write(query, {"cid": citizen_id})
        logger.warning(f"Ciudadano #{citizen_id} eliminado de BD")
        return result is not None

    # ==================== MÉTODOS DE ANÁLISIS ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """Estadísticas globales del sistema."""
        query = """
        MATCH (c:Citizen)
        OPTIONAL MATCH (c)-[:KNOWS]-(friend)
        OPTIONAL MATCH (c)-[:COMMITTED_CRIME]->()
        WITH count(DISTINCT c) as total_citizens,
             avg(c.risk_seed) as avg_risk,
             sum(1) as total_relationships
        RETURN total_citizens,
               avg_risk,
               total_relationships
        """
        result = await db_manager.query(query)
        if result:
            r = result[0]
            return {
                "total_citizens": r.get("total_citizens", 0),
                "average_risk": round(r.get("avg_risk", 0), 3),
                "total_relationships": r.get("total_relationships", 0)
            }
        return {}

# Instancia Singleton para ser importada en toda la app
citizen_repository = CitizenRepository()
