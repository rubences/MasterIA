"""
Definiciones de redes neuronales para Project Pre-Crime.
Importa desde src/models.py para evitar duplicación.
"""
import sys
from pathlib import Path

# Añadir directorio src al path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from models import CrimeGenerator, PoliceDiscriminator
    
    __all__ = ['CrimeGenerator', 'PoliceDiscriminator']
    
except ImportError as e:
    import logging
    logging.warning(f"No se pudieron importar modelos desde src/: {e}")
    
    # Definiciones de respaldo
    import torch
    import torch.nn as nn
    
    class CrimeGenerator(nn.Module):
        """Placeholder para CrimeGenerator."""
        def __init__(self, in_channels, hidden_channels, out_channels):
            super().__init__()
            self.fc = nn.Linear(in_channels, out_channels)
        
        def forward(self, x, edge_index):
            return self.fc(x)
    
    class PoliceDiscriminator(nn.Module):
        """Placeholder para PoliceDiscriminator."""
        def __init__(self, in_channels, hidden_channels, out_channels):
            super().__init__()
            self.fc = nn.Linear(in_channels, out_channels)
        
        def forward(self, x, edge_index):
            return torch.sigmoid(self.fc(x))
    
    __all__ = ['CrimeGenerator', 'PoliceDiscriminator']
