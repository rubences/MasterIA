import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv, GATConv

class CrimeGenerator(torch.nn.Module):
    """
    EL CRIMINAL (GraphSAGE):
    Intenta generar embeddings de nodos que sugieran nuevas conexiones (crímenes)
    basándose en la estructura local.
    """
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(CrimeGenerator, self).__init__()
        # SAGEConv es inductivo: aprende a reconocer patrones de vecindario
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        # x: Características del nodo (historial, riesgo base)
        # edge_index: Conexiones actuales
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.2, training=self.training)
        x = self.conv2(x, edge_index)
        # Retorna embeddings latentes que representan la "intención criminal"
        return x

class PoliceDiscriminator(torch.nn.Module):
    """
    LOS PRECOGS (GAT - Graph Attention Network):
    Evalúa si un enlace (conexión entre nodos) es un crimen real o ruido.
    Usa atención para decidir qué vecinos son cómplices importantes.
    """
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(PoliceDiscriminator, self).__init__()
        # GAT usa 'heads' para mirar diferentes aspectos de la relación simultáneamente
        self.conv1 = GATConv(in_channels, hidden_channels, heads=2, dropout=0.3)
        self.conv2 = GATConv(hidden_channels * 2, out_channels, heads=1, concat=False, dropout=0.3)

    def forward(self, x, edge_index):
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.conv1(x, edge_index)
        x = F.elu(x)
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.conv2(x, edge_index)
        return torch.sigmoid(x) # Probabilidad: 0 (Ruido) a 1 (Crimen/Riesgo Real)
