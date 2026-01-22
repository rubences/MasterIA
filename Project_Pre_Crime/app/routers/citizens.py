"""
Router de Ciudadanos: Endpoints para consultar y buscar ciudadanos.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.core.database import db_manager
from app.models.schemas import CitizenSearchResult

router = APIRouter(
    prefix="/citizens",
    tags=["Citizens"]
)

@router.get("/", response_model=List[CitizenSearchResult])
async def list_citizens(
    limit: int = Query(50, ge=1, le=1000, description="Número máximo de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación")
):
    """
    Lista todos los ciudadanos registrados en el sistema.
    Incluye información básica y grado criminal.
    """
    cypher_query = """
    MATCH (c:Citizen)
    OPTIONAL MATCH (c)-[:KNOWS]-(friend)-[:COMMITTED_CRIME]->()
    WITH c, count(distinct friend) as criminal_contacts
    RETURN c.id as id,
           c.name as name,
           c.born as born,
           c.job as job,
           c.risk_seed as risk_seed,
           criminal_contacts as criminal_degree
    ORDER BY c.id
    SKIP $offset
    LIMIT $limit
    """
    
    results = await db_manager.query(cypher_query, {"limit": limit, "offset": offset})
    
    if not results:
        return []
    
    return [
        CitizenSearchResult(
            id=r['id'],
            name=r['name'],
            born=r.get('born'),
            job=r.get('job'),
            criminal_degree=r.get('criminal_degree', 0),
            risk_seed=r.get('risk_seed', 0.0)
        )
        for r in results
    ]

@router.get("/{citizen_id}", response_model=CitizenSearchResult)
async def get_citizen(citizen_id: int):
    """
    Obtiene información detallada de un ciudadano específico.
    """
    cypher_query = """
    MATCH (c:Citizen {id: $cid})
    OPTIONAL MATCH (c)-[:KNOWS]-(friend)-[:COMMITTED_CRIME]->()
    WITH c, count(distinct friend) as criminal_contacts
    RETURN c.id as id,
           c.name as name,
           c.born as born,
           c.job as job,
           c.risk_seed as risk_seed,
           criminal_contacts as criminal_degree
    """
    
    results = await db_manager.query(cypher_query, {"cid": citizen_id})
    
    if not results:
        raise HTTPException(
            status_code=404, 
            detail=f"Ciudadano con ID {citizen_id} no encontrado"
        )
    
    r = results[0]
    return CitizenSearchResult(
        id=r['id'],
        name=r['name'],
        born=r.get('born'),
        job=r.get('job'),
        criminal_degree=r.get('criminal_degree', 0),
        risk_seed=r.get('risk_seed', 0.0)
    )

@router.get("/search/by-name")
async def search_citizens_by_name(
    query: str = Query(..., min_length=2, description="Término de búsqueda"),
    limit: int = Query(20, ge=1, le=100)
) -> List[CitizenSearchResult]:
    """
    Busca ciudadanos por nombre (búsqueda parcial case-insensitive).
    """
    cypher_query = """
    MATCH (c:Citizen)
    WHERE toLower(c.name) CONTAINS toLower($query)
    OPTIONAL MATCH (c)-[:KNOWS]-(friend)-[:COMMITTED_CRIME]->()
    WITH c, count(distinct friend) as criminal_contacts
    RETURN c.id as id,
           c.name as name,
           c.born as born,
           c.job as job,
           c.risk_seed as risk_seed,
           criminal_contacts as criminal_degree
    ORDER BY c.name
    LIMIT $limit
    """
    
    results = await db_manager.query(cypher_query, {"query": query, "limit": limit})
    
    return [
        CitizenSearchResult(
            id=r['id'],
            name=r['name'],
            born=r.get('born'),
            job=r.get('job'),
            criminal_degree=r.get('criminal_degree', 0),
            risk_seed=r.get('risk_seed', 0.0)
        )
        for r in results
    ]

@router.get("/{citizen_id}/network")
async def get_citizen_network(citizen_id: int):
    """
    Obtiene la red social de un ciudadano (sus conexiones KNOWS).
    """
    cypher_query = """
    MATCH (c:Citizen {id: $cid})
    OPTIONAL MATCH (c)-[:KNOWS]-(friend:Citizen)
    OPTIONAL MATCH (friend)-[cr:COMMITTED_CRIME]->()
    RETURN friend.id as friend_id,
           friend.name as friend_name,
           count(cr) > 0 as is_criminal
    ORDER BY is_criminal DESC, friend.name
    LIMIT 50
    """
    
    results = await db_manager.query(cypher_query, {"cid": citizen_id})
    
    if not results:
        # Verificar si el ciudadano existe
        check_query = "MATCH (c:Citizen {id: $cid}) RETURN c.id as id"
        check = await db_manager.query(check_query, {"cid": citizen_id})
        if not check:
            raise HTTPException(
                status_code=404,
                detail=f"Ciudadano con ID {citizen_id} no encontrado"
            )
        return {"citizen_id": citizen_id, "connections": [], "total": 0}
    
    connections = [
        {
            "friend_id": r['friend_id'],
            "friend_name": r['friend_name'],
            "is_criminal": r['is_criminal']
        }
        for r in results if r.get('friend_id')
    ]
    
    return {
        "citizen_id": citizen_id,
        "connections": connections,
        "total": len(connections)
    }
