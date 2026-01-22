#!/usr/bin/env python3
"""
Sistema de Predicción de Crímenes (Pre-Crime)
============================================
Usa redes neuronales gráficas (GNNs) con una arquitectura GAN-like
para predecir potenciales incidentes criminales en una ciudad.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import torch
from torch_geometric.data import Data

from models import CrimeGenerator, PoliceDiscriminator
from train import train_precrime_gan
from connector import Neo4jConnector
from utils import setup_logging, load_config, create_dummy_graph, load_real_graph_data

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logger = logging.getLogger(__name__)


def main():
    """Función principal del sistema Pre-Crime"""
    
    # 1. CONFIGURACIÓN INICIAL
    logger.info("=" * 60)
    logger.info("INICIANDO SISTEMA DE PREDICCIÓN PRE-CRIME")
    logger.info("=" * 60)
    
    # Detectar dispositivo
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Dispositivo: {device}")
    
    # Cargar configuración
    config = load_config()
    logger.info(f"Configuración cargada: {config}")
    
    # 2. CARGAR DATOS
    logger.info("\n[PASO 1] Cargando datos del grafo...")
    
    # Intentar cargar datos reales primero
    use_real_data = config.get('use_real_data', False)
    
    if use_real_data:
        logger.info("Intentando cargar datos reales de Neo4j...")
        try:
            data = load_real_graph_data(device=device)
            logger.info(f"✓ Datos reales cargados: {data.num_nodes} nodos, {data.num_edges} aristas")
        except Exception as e:
            logger.warning(f"No se pudieron cargar datos reales: {e}")
            logger.info("Usando datos sintéticos dummy...")
            data = create_dummy_graph(
                num_nodes=config['num_nodes'],
                num_edges=config['num_edges'],
                num_features=config['num_features'],
                device=device
            )
    else:
        logger.info("Usando datos sintéticos dummy...")
        data = create_dummy_graph(
            num_nodes=config['num_nodes'],
            num_edges=config['num_edges'],
            num_features=config['num_features'],
            device=device
        )
    
    logger.info(f"Grafo cargado: {data.num_nodes} nodos, {data.num_edges} aristas")
    logger.info(f"Características por nodo: {data.num_features}")
    
    # 3. ENTRENAR MODELO
    logger.info("\n[PASO 2] Entrenando modelo Pre-Crime (GAN)...")
    generator, discriminator = train_precrime_gan(
        data=data,
        epochs=config['epochs'],
        device=device,
        lr_g=config['learning_rate_g'],
        lr_d=config['learning_rate_d']
    )
    logger.info("✓ Modelo entrenado exitosamente")
    
    # 4. GUARDAR MODELO
    logger.info("\n[PASO 3] Guardando modelo...")
    models_dir = Path(config['model_path'])
    models_dir.mkdir(exist_ok=True)
    
    torch.save(generator.state_dict(), models_dir / 'generator.pth')
    torch.save(discriminator.state_dict(), models_dir / 'discriminator.pth')
    logger.info(f"✓ Modelos guardados en {models_dir}")
    
    # 5. HACER PREDICCIONES
    logger.info("\n[PASO 4] Generando predicciones...")
    with torch.no_grad():
        predictions = generator(data.x, data.edge_index)
    
    risk_scores = discriminator(predictions, data.edge_index)
    logger.info(f"✓ Predicciones generadas. Riesgo promedio: {risk_scores.mean():.4f}")
    
    # 6. EXPORTAR A NEO4J (opcional)
    if config.get('export_to_neo4j'):
        logger.info("\n[PASO 5] Exportando predicciones a Neo4j...")
        try:
            db = Neo4jConnector(
                config['neo4j_uri'],
                config['neo4j_user'],
                config['neo4j_password']
            )
            # Preparar predicciones para exportar
            predictions_list = []
            for i in range(min(10, len(risk_scores))):
                predictions_list.append({
                    'source': i,
                    'target': (i + 1) % data.num_nodes,
                    'risk': float(risk_scores[i])
                })
            
            db.update_predictions(predictions_list)
            db.close()
            logger.info("✓ Predicciones exportadas a Neo4j")
        except Exception as e:
            logger.warning(f"⚠ No se pudo conectar a Neo4j: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("SISTEMA PRE-CRIME FINALIZADO")
    logger.info("=" * 60)
    
    return generator, discriminator


if __name__ == "__main__":
    # Configurar logging
    setup_logging()
    
    try:
        gen, disc = main()
        logger.info("✓ Ejecución exitosa")
        sys.exit(0)
    except Exception as e:
        logger.error(f"✗ Error crítico: {e}", exc_info=True)
        sys.exit(1)
