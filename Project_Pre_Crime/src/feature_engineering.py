"""
Feature Engineering para Project Pre-Crime (Parte 3):
- Calcula influencia criminal por vecindario en Neo4j
- Extrae y vectoriza atributos (edad normalizada, one-hot de trabajos)
- Construye objeto Data de PyTorch Geometric con x, edge_index, y
"""

from typing import Tuple

import os
import pandas as pd
import numpy as np
import torch
from neo4j import GraphDatabase
from dotenv import load_dotenv
from torch_geometric.data import Data


def _get_driver_from_env():
    """Inicializa el driver de Neo4j leyendo variables desde .env."""
    load_dotenv()
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(user, password))


def calculate_criminal_influence(driver) -> None:
    """
    Calcula, por cada ciudadano, cuántos vecinos tienen relación COMMITTED_CRIME
    y persiste la propiedad c.criminal_degree.
    """
    print("💧 Hidratando: Calculando influencia criminal del entorno...")
    query = """
    MATCH (c:Citizen)
    OPTIONAL MATCH (c)-[:KNOWS]-(friend)-[:COMMITTED_CRIME]->()
    WITH c, count(distinct friend) as criminal_friends
    SET c.criminal_degree = criminal_friends
    RETURN count(c) as updated
    """
    with driver.session() as session:
        res = session.run(query)
        updated = res.single()["updated"] if res.peek() else 0
        print(f"✅ Nodos actualizados con 'criminal_degree': {updated}")


def extract_features_to_pandas(driver) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extrae atributos de ciudadanos, normaliza edad y aplica one-hot encoding a job.
    Retorna (df_original, df_features_numericas).
    """
    print("📊 Extrayendo datos para vectorización...")
    query = """
    MATCH (c:Citizen)
    RETURN c.id as id, c.born as born, c.job as job, c.criminal_degree as crim_deg, c.risk_seed as target
    ORDER BY c.id
    """
    with driver.session() as session:
        result = session.run(query)
        rows = [r.data() for r in result]

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No se encontraron ciudadanos en Neo4j para hidratar.")

    # Tipado y limpieza básica
    df["id"] = df["id"].astype(int)
    # born puede venir como string; convertir y manejar faltantes
    df["born"] = pd.to_numeric(df["born"], errors="coerce")
    current_year = int(os.getenv("CURRENT_YEAR", "2026"))
    # Normalización de edad en rango aproximado [0,1]
    df["age"] = ((current_year - df["born"]).fillna(0).clip(lower=0)) / 100.0

    # criminal_degree: rellenar faltantes con 0
    df["crim_deg"] = pd.to_numeric(df["crim_deg"], errors="coerce").fillna(0)

    # One-Hot Encoding de Trabajos
    job_dummies = pd.get_dummies(df["job"].fillna("Unknown"), prefix="job")
    df = pd.concat([df, job_dummies], axis=1)

    # Etiqueta/objetivo
    df["target"] = pd.to_numeric(df["target"], errors="coerce").fillna(0.0)

    # Selección de features numéricas (mantiene orden por id ya que hicimos ORDER BY)
    features = df.drop(columns=["born", "job"] + ["id", "target"]).copy()
    features = features.fillna(0.0).astype(np.float32)

    print(f"✅ Features procesadas. Dimensiones del tensor: {features.shape}")
    return df, features


def load_graph_to_pyg(driver, features_df: pd.DataFrame, full_df: pd.DataFrame) -> Data:
    """
    Construye Data de PyTorch Geometric:
      - x: matriz de características (float32)
      - edge_index: topología del grafo KNOWS (mapeada a índices 0..N-1)
      - y: etiquetas (risk_seed), shape [N, 1]
    """
    print("🚀 Construyendo el objeto PyTorch Geometric...")

    # 1) X (features) -> torch.float32
    x = torch.tensor(features_df.values, dtype=torch.float32)

    # 2) Y (labels) -> risk_seed como proxy
    y = torch.tensor(full_df["target"].values, dtype=torch.float32).view(-1, 1)

    # 3) Mapeo de IDs (c.id) a índices de fila (0..N-1)
    id_to_idx = {cid: i for i, cid in enumerate(full_df["id"].tolist())}

    # 4) Extraer aristas y mapear a índices
    edge_query = """
    MATCH (c1:Citizen)-[:KNOWS]->(c2:Citizen)
    RETURN c1.id as source, c2.id as target
    ORDER BY source, target
    """
    with driver.session() as session:
        result = session.run(edge_query)
        edges = []
        for r in result:
            s_id, t_id = r["source"], r["target"]
            # Filtrar cualquier id que no esté en el df
            if s_id in id_to_idx and t_id in id_to_idx:
                edges.append((id_to_idx[s_id], id_to_idx[t_id]))

    if len(edges) == 0:
        # Grafo vacío: construir tensor sin aristas
        edge_index = torch.empty((2, 0), dtype=torch.long)
    else:
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()

    data = Data(x=x, edge_index=edge_index, y=y)
    print(
        "✨ Grafo cargado en memoria GPU/CPU:\n"
        f"   - Nodos: {data.num_nodes}\n"
        f"   - Aristas: {data.num_edges}\n"
        f"   - Features por nodo: {data.num_node_features}"
    )
    return data


def hydrate_graph_data() -> Data:
    """Pipeline completo: calcula influencia, extrae features y arma Data (PyG)."""
    driver = _get_driver_from_env()
    try:
        calculate_criminal_influence(driver)
        df_full, df_feats = extract_features_to_pandas(driver)
        return load_graph_to_pyg(driver, df_feats, df_full)
    finally:
        driver.close()
