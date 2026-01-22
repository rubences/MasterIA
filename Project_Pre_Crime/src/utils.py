"""
Utilidades para el sistema Pre-Crime
====================================
Funciones auxiliares para configuración, logging y procesamiento de datos.
"""

import logging
import os
from pathlib import Path
import torch
from torch_geometric.data import Data


def setup_logging():
    """Configurar sistema de logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('precrime.log'),
            logging.StreamHandler()
        ]
    )


def load_config():
    """Cargar configuración desde variables de entorno"""
    config = {
        # Neo4j
        'neo4j_uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        'neo4j_user': os.getenv('NEO4J_USER', 'neo4j'),
        'neo4j_password': os.getenv('NEO4J_PASSWORD', 'password'),
        
        # Rutas
        'model_path': os.getenv('MODEL_PATH', './models'),
        'data_path': os.getenv('DATA_PATH', './data'),
        'log_path': os.getenv('LOG_PATH', './logs'),
        
        # Modelo
        'num_nodes': int(os.getenv('NUM_NODES', '100')),
        'num_edges': int(os.getenv('NUM_EDGES', '300')),
        'num_features': int(os.getenv('NUM_FEATURES', '16')),
        'hidden_dim': int(os.getenv('HIDDEN_DIM', '64')),
        
        # Entrenamiento
        'epochs': int(os.getenv('EPOCHS', '100')),
        'batch_size': int(os.getenv('BATCH_SIZE', '32')),
        'learning_rate_g': float(os.getenv('LEARNING_RATE_G', '0.001')),
        'learning_rate_d': float(os.getenv('LEARNING_RATE_D', '0.001')),
        
        # Datos
        'use_real_data': os.getenv('USE_REAL_DATA', 'false').lower() == 'true',
        
        # Exportación
        'export_to_neo4j': os.getenv('EXPORT_TO_NEO4J', 'false').lower() == 'true',
    }
    
    # Crear directorios si no existen
    for key in ['model_path', 'data_path', 'log_path']:
        Path(config[key]).mkdir(exist_ok=True)
    
    return config


def create_dummy_graph(num_nodes, num_edges, num_features, device):
    """
    Crear un grafo dummy para pruebas
    
    Args:
        num_nodes: Número de nodos
        num_edges: Número de aristas
        num_features: Características por nodo
        device: Dispositivo (cpu/cuda)
    
    Returns:
        torch_geometric.data.Data: Grafo
    """
    # Características: vector aleatorio para cada nodo
    x = torch.randn((num_nodes, num_features), device=device)
    
    # Aristas: conexiones aleatorias
    edge_index = torch.randint(0, num_nodes, (2, num_edges), device=device)
    
    return Data(x=x, edge_index=edge_index)


def create_real_graph_from_neo4j(db_uri, db_user, db_password, device):
    """
    Cargar datos reales de Neo4j (implementación futura)
    
    Args:
        db_uri: URI de conexión a Neo4j
        db_user: Usuario de Neo4j
        db_password: Contraseña de Neo4j
        device: Dispositivo (cpu/cuda)
    
    Returns:
        torch_geometric.data.Data: Grafo
    """
    # TODO: Implementar carga desde Neo4j
    raise NotImplementedError("Carga de datos reales desde Neo4j aún no implementada")


def load_real_graph_data(device='cpu', data_path='data/precrime_graph.pt'):
    """
    Carga datos reales del grafo desde archivo guardado.
    
    Args:
        device: Dispositivo (cpu/cuda)
        data_path: Ruta al archivo de datos
    
    Returns:
        torch_geometric.data.Data: Grafo con datos reales
    """
    from pathlib import Path
    
    data_file = Path(data_path)
    if not data_file.exists():
        raise FileNotFoundError(
            f"Archivo de datos no encontrado: {data_path}\n"
            "Ejecuta primero: python src/data_hydrator.py"
        )
    
    data = torch.load(data_file)
    data = data.to(device)
    
    logging.info(f"Datos reales cargados desde {data_path}")
    return data


def save_predictions_to_file(predictions, output_path='predictions.csv'):
    """
    Guardar predicciones en archivo CSV
    
    Args:
        predictions: Lista de predicciones
        output_path: Ruta del archivo de salida
    """
    import csv
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['source', 'target', 'risk', 'timestamp'])
        writer.writeheader()
        writer.writerows(predictions)
    
    logging.info(f"Predicciones guardadas en {output_path}")


def evaluate_model_performance(predictions, real_labels=None):
    """
    Evaluar el desempeño del modelo
    
    Args:
        predictions: Predicciones del modelo
        real_labels: Etiquetas reales (opcional)
    
    Returns:
        dict: Métricas de evaluación
    """
    metrics = {
        'mean_risk': float(predictions.mean()),
        'max_risk': float(predictions.max()),
        'min_risk': float(predictions.min()),
        'std_risk': float(predictions.std()),
    }
    
    if real_labels is not None:
        # TODO: Calcular precisión, recall, F1, etc.
        pass
    
    return metrics
