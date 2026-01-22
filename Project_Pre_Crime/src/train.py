import torch
import torch.nn.functional as F
from models import CrimeGenerator, PoliceDiscriminator
# from connector import Neo4jConnector # Uncomment when using real DB

def train_precrime_gan(data, epochs=50, device=None, lr_g=0.01, lr_d=0.01):
    # Configuración del dispositivo si no se proporciona
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Mover datos al dispositivo
    data = data.to(device)
    
    # Inicialización
    in_dim = data.num_features
    hidden_dim = 64
    out_dim = in_dim # Dimensión del embedding (Debe coincidir con in_dim para que el discriminador acepte data.x)
    
    generator = CrimeGenerator(in_dim, hidden_dim, out_dim).to(device)
    discriminator = PoliceDiscriminator(out_dim, hidden_dim, 1).to(device) # Salida 1 (Probabilidad)

    # Optimizadores separados
    optimizer_G = torch.optim.Adam(generator.parameters(), lr=lr_g)
    optimizer_D = torch.optim.Adam(discriminator.parameters(), lr=lr_d)

    # Simulación del Bucle
    for epoch in range(epochs):
        # ---------------------
        # 1. Entrenar a la Policía (Discriminador)
        # ---------------------
        optimizer_D.zero_grad()
        
        # Generar "crímenes potenciales" (embeddings)
        fake_node_embeddings = generator(data.x, data.edge_index)
        
        # El discriminador evalúa los datos reales vs los generados
        # (Nota: En una implementación real, aquí decodificaríamos los enlaces)
        real_pred = discriminator(data.x, data.edge_index) 
        fake_pred = discriminator(fake_node_embeddings.detach(), data.edge_index)
        
        # Loss: Maximizar acierto en reales y acierto en detectar falsos
        loss_D = -torch.mean(torch.log(real_pred + 1e-9) + torch.log(1 - fake_pred + 1e-9))
        loss_D.backward()
        optimizer_D.step()

        # ---------------------
        # 2. Entrenar al Criminal (Generador)
        # ---------------------
        optimizer_G.zero_grad()
        
        # El generador quiere que el discriminador se equivoque (diga que es real)
        fake_node_embeddings = generator(data.x, data.edge_index)
        fake_pred = discriminator(fake_node_embeddings, data.edge_index)
        
        loss_G = -torch.mean(torch.log(fake_pred + 1e-9))
        loss_G.backward()
        optimizer_G.step()

        if epoch % 10 == 0:
            print(f"Epoch {epoch} | Loss Policía: {loss_D.item():.4f} | Loss Criminal: {loss_G.item():.4f}")

    return generator, discriminator

# --- EJECUCIÓN ---
if __name__ == "__main__":
    # 1. Crear datos Dummy para probar (Simulando ciudadanos y ubicaciones)
    from torch_geometric.data import Data
    
    # 100 Nodos (Personas/Lugares), 16 características cada uno
    x = torch.randn((100, 16), device=device)
    # Conexiones aleatorias (Grafo social)
    edge_index = torch.randint(0, 100, (2, 300), device=device)
    
    data = Data(x=x, edge_index=edge_index)
    
    print("Iniciando Sistema Pre-Crime...")
    gen, disc = train_precrime_gan(data)
    
    # 2. Simular exportación a Neo4j (requiere base de datos activa)
    # db = Neo4jConnector("bolt://localhost:7687", "neo4j", "password")
    # fake_predictions = [{'source': 1, 'target': 5, 'risk': 0.98}] # Ejemplo
    # db.update_predictions(fake_predictions)
    # db.close()
    print("Entrenamiento finalizado. Precogs listos.")
