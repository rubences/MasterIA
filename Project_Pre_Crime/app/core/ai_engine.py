"""
Motor de Inteligencia Artificial - "Sala de los Precogs"
Carga y gestiona los modelos de PyTorch para inferencia en tiempo real.
"""
import os
import logging
import torch
import numpy as np
from typing import Dict, Any
from pathlib import Path

# Importar modelos desde el directorio src
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

try:
    from models import CrimeGenerator, PoliceDiscriminator
except ImportError:
    # Fallback si los modelos no están disponibles
    CrimeGenerator = None
    PoliceDiscriminator = None

from app.config import settings
from app.models.schemas import CitizenFeatureVector

logger = logging.getLogger("PreCogSystem")

class PrecogSystem:
    """
    Sistema de inferencia neuronal.
    Carga modelos PyTorch al inicio y mantiene en memoria.
    """
    
    def __init__(self):
        self.generator = None
        self.discriminator = None
        self.device = torch.device(settings.DEVICE)
        self.models_loaded = False
        
    def load_models(self):
        """Carga los modelos desde disco o inicializa desde cero."""
        try:
            model_path = Path(settings.MODEL_PATH)
            
            if model_path.exists():
                logger.info(f"📦 Cargando modelos desde {model_path}")
                checkpoint = torch.load(model_path, map_location=self.device)
                
                # Reconstruir arquitectura
                self.generator = CrimeGenerator(
                    in_channels=checkpoint.get('in_dim', 16),
                    hidden_channels=checkpoint.get('hidden_dim', 64),
                    out_channels=checkpoint.get('out_dim', 16)
                ).to(self.device)
                
                self.discriminator = PoliceDiscriminator(
                    in_channels=checkpoint.get('out_dim', 16),
                    hidden_channels=checkpoint.get('hidden_dim', 64),
                    out_channels=1
                ).to(self.device)
                
                # Cargar pesos
                self.generator.load_state_dict(checkpoint['generator_state_dict'])
                self.discriminator.load_state_dict(checkpoint['discriminator_state_dict'])
                
                logger.info("✅ Modelos cargados exitosamente")
            else:
                logger.warning(f"⚠️ No se encontró {model_path}. Inicializando modelos sin entrenar.")
                # Inicializar con pesos aleatorios (modo demo)
                if CrimeGenerator and PoliceDiscriminator:
                    self.generator = CrimeGenerator(16, 64, 16).to(self.device)
                    self.discriminator = PoliceDiscriminator(16, 64, 1).to(self.device)
                else:
                    logger.warning("⚠️ Clases de modelos no disponibles. Modo mock activado.")
            
            # Modo evaluación (no entrenamiento)
            if self.generator:
                self.generator.eval()
            if self.discriminator:
                self.discriminator.eval()
                
            self.models_loaded = True
            logger.info("🔮 Sistema Pre-Crime listo para inferencia")
            
        except Exception as e:
            logger.error(f"❌ Error al cargar modelos: {e}")
            self.models_loaded = False
            raise

    def predict(self, citizen: CitizenFeatureVector) -> Dict[str, Any]:
        """
        Ejecuta inferencia para un ciudadano.
        
        Args:
            citizen: Vector de características del ciudadano
            
        Returns:
            Diccionario con probability, confidence y verdict
        """
        if not self.models_loaded:
            # Modo fallback: usar solo risk_seed
            return self._fallback_prediction(citizen)
        
        try:
            with torch.no_grad():
                # Construir tensor de entrada
                # En producción real, aquí cargaríamos el subgrafo desde Neo4j
                features = self._build_feature_tensor(citizen)
                
                if self.discriminator is None:
                    return self._fallback_prediction(citizen)
                
                # Mock de edge_index (en producción vendría de Neo4j)
                edge_index = torch.tensor([[0], [0]], dtype=torch.long, device=self.device)
                
                # Inferencia
                prediction = self.discriminator(features, edge_index)
                probability = prediction.item()
                
                # Calcular confianza (basada en distancia del umbral)
                confidence = abs(probability - 0.5) * 2
                
                return {
                    "probability": float(probability),
                    "confidence": float(confidence),
                    "method": "neural_network"
                }
                
        except Exception as e:
            logger.error(f"❌ Error en inferencia: {e}")
            return self._fallback_prediction(citizen)
    
    def _build_feature_tensor(self, citizen: CitizenFeatureVector) -> torch.Tensor:
        """Construye tensor de entrada desde CitizenFeatureVector."""
        features = [
            citizen.risk_seed,
            citizen.criminal_degree / 10.0,  # Normalizar
            citizen.age_normalized or 0.35,
        ]
        
        # Añadir job_vector si existe
        if citizen.job_vector:
            features.extend(citizen.job_vector[:13])  # Max 13 jobs
        else:
            features.extend([0.0] * 13)
        
        # Padding hasta 16 features
        while len(features) < 16:
            features.append(0.0)
        
        return torch.tensor([features], dtype=torch.float32, device=self.device)
    
    def _fallback_prediction(self, citizen: CitizenFeatureVector) -> Dict[str, Any]:
        """Predicción de respaldo usando heurística simple."""
        # Combinación ponderada de risk_seed y criminal_degree
        base_risk = citizen.risk_seed
        social_risk = min(citizen.criminal_degree * 0.1, 0.4)
        probability = min(base_risk + social_risk, 1.0)
        
        confidence = 0.6  # Confianza baja en modo fallback
        
        return {
            "probability": float(probability),
            "confidence": float(confidence),
            "method": "heuristic_fallback"
        }

# Instancia global del sistema Pre-Crime
precog_system = PrecogSystem()
