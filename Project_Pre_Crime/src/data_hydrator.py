"""
Data Hydrator - Pre-Crime System
=================================
Extrae datos de Neo4j y los transforma en tensores PyTorch listos
para entrenar GraphSAGE y GAT.

Esta es la Parte 3: Enriquecer y preparar los datos para la IA.
"""

import torch
import numpy as np
from neo4j import GraphDatabase
import logging
from typing import Dict, Tuple, List
from torch_geometric.data import Data
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class PreCrimeDataHydrator:
    """
    Extrae datos del grafo Neo4j y los convierte en tensores.
    
    El objetivo es transformar:
    - Ciudadanos → Nodos con features
    - Relaciones sociales → Edge Index
    - Crímenes → Labels para entrenamiento supervisado
    """
    
    def __init__(self, uri="bolt://localhost:7687", auth=("neo4j", "password")):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.node_features = []
        self.edge_index = []
        self.labels = []
        self.node_mapping = {}  # Neo4j ID → PyTorch index
        logger.info("Data Hydrator inicializado")
    
    def close(self):
        self.driver.close()
    
    def extract_node_features(self) -> torch.Tensor:
        """
        Extrae características de los ciudadanos.
        
        Features:
        - Edad normalizada
        - Número de conexiones sociales (degree)
        - Número de lugares visitados
        - Promedio de riesgo ambiental de lugares visitados
        - Indicador si ha cometido crimen (para entrenamiento supervisado)
        """
        print("📊 Extrayendo características de nodos...")
        
        query = """
        MATCH (c:Citizen)
        OPTIONAL MATCH (c)-[:KNOWS]-(friend)
        OPTIONAL MATCH (c)-[:VISITS]->(loc:Location)
        OPTIONAL MATCH (c)-[:COMMITTED_CRIME]->(crime_loc)
        WITH c, 
             count(DISTINCT friend) as num_friends,
             count(DISTINCT loc) as num_places,
             avg(loc.env_risk) as avg_env_risk,
             count(DISTINCT crime_loc) as num_crimes
        RETURN c.id as id,
               c.born as born,
               c.risk_seed as risk_seed,
               num_friends,
               num_places,
               coalesce(avg_env_risk, 0.0) as avg_env_risk,
               num_crimes,
               CASE WHEN num_crimes > 0 THEN 1 ELSE 0 END as is_criminal
        ORDER BY c.id
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            records = list(result)
        
        features_list = []
        current_year = 2026
        
        for idx, record in enumerate(records):
            # Mapeo de Neo4j ID a índice PyTorch
            self.node_mapping[record["id"]] = idx
            
            # Normalizar edad (0-1)
            age = current_year - int(record["born"]) if record["born"] else 30
            age_norm = min(age / 100.0, 1.0)
            
            # Normalizar grado del nodo (log scale)
            degree_norm = min(np.log1p(record["num_friends"]) / 5.0, 1.0)
            
            # Normalizar lugares visitados
            places_norm = min(record["num_places"] / 20.0, 1.0)
            
            # Riesgo ambiental promedio
            env_risk = record["avg_env_risk"]
            
            # Número de crímenes (normalizado)
            crimes_norm = min(record["num_crimes"] / 10.0, 1.0)
            
            # Feature vector: [edad, degree, lugares, riesgo_ambiental, crímenes]
            features = [
                age_norm,
                degree_norm,
                places_norm,
                env_risk,
                crimes_norm
            ]
            
            features_list.append(features)
            
            # Label: 1 si es criminal, 0 si no
            self.labels.append(record["is_criminal"])
        
        self.node_features = torch.tensor(features_list, dtype=torch.float)
        self.labels = torch.tensor(self.labels, dtype=torch.long)
        
        logger.info(f"✓ {len(features_list)} nodos con {len(features_list[0])} features cada uno")
        print(f"  Dimensión de features: {self.node_features.shape}")
        print(f"  Criminales detectados: {self.labels.sum().item()} ({self.labels.sum().item()/len(self.labels)*100:.1f}%)")
        
        return self.node_features
    
    def extract_edge_index(self) -> torch.Tensor:
        """
        Extrae el grafo de relaciones sociales.
        
        Returns:
            torch.Tensor: Edge index [2, num_edges]
        """
        print("🕸️ Extrayendo estructura del grafo...")
        
        query = """
        MATCH (a:Citizen)-[:KNOWS]->(b:Citizen)
        RETURN a.id as source, b.id as target
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            edges = list(result)
        
        edge_list = []
        for edge in edges:
            src_id = edge["source"]
            tgt_id = edge["target"]
            
            # Convertir a índices PyTorch
            if src_id in self.node_mapping and tgt_id in self.node_mapping:
                src_idx = self.node_mapping[src_id]
                tgt_idx = self.node_mapping[tgt_id]
                edge_list.append([src_idx, tgt_idx])
        
        # Convertir a formato PyTorch Geometric: [2, num_edges]
        if edge_list:
            self.edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
        else:
            self.edge_index = torch.empty((2, 0), dtype=torch.long)
        
        logger.info(f"✓ {self.edge_index.shape[1]} aristas extraídas")
        print(f"  Dimensión del grafo: {self.edge_index.shape}")
        
        return self.edge_index
    
    def extract_crime_patterns(self) -> Dict:
        """
        Extrae patrones de crímenes para análisis adicional.
        
        Returns:
            Dict con estadísticas de crímenes
        """
        print("🔍 Analizando patrones criminales...")
        
        query = """
        MATCH (c:Citizen)-[crime:COMMITTED_CRIME]->(l:Location)
        RETURN crime.type as type,
               crime.severity as severity,
               l.type as location_type,
               crime.date as date
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            crimes = list(result)
        
        patterns = {
            'by_type': {},
            'by_location': {},
            'by_severity': [],
            'total': len(crimes)
        }
        
        for crime in crimes:
            # Por tipo de crimen
            ctype = crime['type']
            patterns['by_type'][ctype] = patterns['by_type'].get(ctype, 0) + 1
            
            # Por tipo de ubicación
            ltype = crime['location_type']
            patterns['by_location'][ltype] = patterns['by_location'].get(ltype, 0) + 1
            
            # Severidad
            patterns['by_severity'].append(crime['severity'])
        
        print(f"  Total de crímenes: {patterns['total']}")
        print(f"  Tipos de crimen: {list(patterns['by_type'].keys())}")
        print(f"  Severidad promedio: {np.mean(patterns['by_severity']):.2f}")
        
        return patterns
    
    def create_pytorch_geometric_data(self) -> Data:
        """
        Crea un objeto Data de PyTorch Geometric listo para entrenar.
        
        Returns:
            Data: Objeto con x (features), edge_index (grafo), y (labels)
        """
        print("\n🔧 Creando objeto PyTorch Geometric...")
        
        # Extraer todos los datos
        if len(self.node_features) == 0:
            self.extract_node_features()
        if len(self.edge_index) == 0:
            self.extract_edge_index()
        
        # Crear objeto Data
        data = Data(
            x=self.node_features,
            edge_index=self.edge_index,
            y=self.labels
        )
        
        # Validar
        print(f"  ✓ Nodos: {data.num_nodes}")
        print(f"  ✓ Aristas: {data.num_edges}")
        print(f"  ✓ Features por nodo: {data.num_features}")
        print(f"  ✓ Labels: {data.y.shape}")
        
        # Estadísticas adicionales
        print(f"\n📈 Estadísticas del dataset:")
        print(f"  Clase 0 (Inocentes): {(data.y == 0).sum().item()}")
        print(f"  Clase 1 (Criminales): {(data.y == 1).sum().item()}")
        print(f"  Desbalance: {(data.y == 1).sum().item() / len(data.y) * 100:.2f}% criminales")
        
        return data
    
    def save_data(self, data: Data, filepath: str = "data/precrime_graph.pt"):
        """Guarda el dataset en disco."""
        filepath = Path(filepath)
        filepath.parent.mkdir(exist_ok=True)
        
        torch.save(data, filepath)
        print(f"\n💾 Dataset guardado en: {filepath}")
        logger.info(f"Dataset guardado en {filepath}")
    
    def split_data(self, data: Data, train_ratio=0.7, val_ratio=0.15) -> Data:
        """
        Divide el dataset en train/val/test.
        
        Args:
            data: Objeto Data
            train_ratio: Proporción de entrenamiento
            val_ratio: Proporción de validación
        
        Returns:
            Data con máscaras de train/val/test
        """
        print("\n✂️ Dividiendo dataset en train/val/test...")
        
        num_nodes = data.num_nodes
        indices = torch.randperm(num_nodes)
        
        train_size = int(train_ratio * num_nodes)
        val_size = int(val_ratio * num_nodes)
        
        data.train_mask = torch.zeros(num_nodes, dtype=torch.bool)
        data.val_mask = torch.zeros(num_nodes, dtype=torch.bool)
        data.test_mask = torch.zeros(num_nodes, dtype=torch.bool)
        
        data.train_mask[indices[:train_size]] = True
        data.val_mask[indices[train_size:train_size + val_size]] = True
        data.test_mask[indices[train_size + val_size:]] = True
        
        print(f"  Train: {data.train_mask.sum().item()} nodos ({train_ratio*100:.0f}%)")
        print(f"  Val: {data.val_mask.sum().item()} nodos ({val_ratio*100:.0f}%)")
        print(f"  Test: {data.test_mask.sum().item()} nodos ({100-train_ratio*100-val_ratio*100:.0f}%)")
        
        return data
    
    def get_feature_statistics(self) -> Dict:
        """Obtiene estadísticas de las features."""
        if len(self.node_features) == 0:
            self.extract_node_features()
        
        stats = {
            'mean': self.node_features.mean(dim=0).tolist(),
            'std': self.node_features.std(dim=0).tolist(),
            'min': self.node_features.min(dim=0).values.tolist(),
            'max': self.node_features.max(dim=0).values.tolist()
        }
        
        feature_names = ['edad', 'degree', 'lugares', 'riesgo_ambiental', 'crímenes']
        
        print("\n📊 Estadísticas de Features:")
        for i, name in enumerate(feature_names):
            print(f"  {name}:")
            print(f"    Media: {stats['mean'][i]:.4f}")
            print(f"    Std: {stats['std'][i]:.4f}")
            print(f"    Min: {stats['min'][i]:.4f}")
            print(f"    Max: {stats['max'][i]:.4f}")
        
        return stats


# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    from utils import setup_logging
    
    setup_logging()
    
    print("=" * 70)
    print("🧪 PRE-CRIME DATA HYDRATOR")
    print("Transformando grafo Neo4j → Tensores PyTorch")
    print("=" * 70)
    print()
    
    hydrator = PreCrimeDataHydrator()
    
    try:
        # Paso 1: Extraer features y estructura
        hydrator.extract_node_features()
        hydrator.extract_edge_index()
        
        # Paso 2: Analizar patrones
        patterns = hydrator.extract_crime_patterns()
        
        # Paso 3: Crear dataset PyTorch Geometric
        data = hydrator.create_pytorch_geometric_data()
        
        # Paso 4: Dividir en train/val/test
        data = hydrator.split_data(data)
        
        # Paso 5: Estadísticas
        stats = hydrator.get_feature_statistics()
        
        # Paso 6: Guardar
        hydrator.save_data(data)
        
        print("\n" + "=" * 70)
        print("✅ DATOS HIDRATADOS EXITOSAMENTE")
        print("=" * 70)
        print("\n🎯 Próximos pasos:")
        print("  1. El dataset está listo en: data/precrime_graph.pt")
        print("  2. Entrena el modelo:")
        print("     python src/main.py")
        print("  3. El modelo ahora usará datos REALES del grafo Neo4j")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Error en hidratación: {e}", exc_info=True)
    finally:
        hydrator.close()
