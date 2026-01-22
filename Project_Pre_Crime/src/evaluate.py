"""
Script de evaluación del modelo Pre-Crime
==========================================
Evalúa el desempeño del modelo entrenado.
"""

import torch
import logging
from pathlib import Path
from dotenv import load_dotenv

from models import CrimeGenerator, PoliceDiscriminator
from utils import setup_logging, load_config, create_dummy_graph, evaluate_model_performance

load_dotenv()
logger = logging.getLogger(__name__)


def evaluate():
    """Evaluar el modelo entrenado"""
    
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("EVALUACIÓN DEL SISTEMA PRE-CRIME")
    logger.info("=" * 60)
    
    # Configuración
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    config = load_config()
    
    # Crear datos de prueba
    logger.info("\nCargando datos de prueba...")
    data = create_dummy_graph(
        config['num_nodes'],
        config['num_edges'],
        config['num_features'],
        device
    )
    
    # Cargar modelos entrenados
    logger.info("Cargando modelos entrenados...")
    models_dir = Path(config['model_path'])
    
    if not (models_dir / 'generator.pth').exists():
        logger.error("✗ No se encontró el modelo generador. Entrena primero.")
        return
    
    in_dim = config['num_features']
    hidden_dim = config['hidden_dim']
    
    generator = CrimeGenerator(in_dim, hidden_dim, in_dim).to(device)
    discriminator = PoliceDiscriminator(in_dim, hidden_dim, 1).to(device)
    
    generator.load_state_dict(torch.load(models_dir / 'generator.pth'))
    discriminator.load_state_dict(torch.load(models_dir / 'discriminator.pth'))
    
    logger.info("✓ Modelos cargados")
    
    # Evaluar
    logger.info("\nEvaluando modelo...")
    generator.eval()
    discriminator.eval()
    
    with torch.no_grad():
        # Generar predicciones
        predictions = generator(data.x, data.edge_index)
        risk_scores = discriminator(predictions, data.edge_index)
        
        # Calcular métricas
        metrics = evaluate_model_performance(risk_scores)
        
        logger.info("\n" + "=" * 60)
        logger.info("MÉTRICAS DE EVALUACIÓN")
        logger.info("=" * 60)
        for metric, value in metrics.items():
            logger.info(f"  {metric}: {value:.4f}")
        logger.info("=" * 60)
    
    return metrics


if __name__ == "__main__":
    evaluate()
