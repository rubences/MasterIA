# 🚨 Sistema de Predicción Pre-Crime

Un sistema avanzado de predicción de crímenes basado en **Graph Neural Networks (GNN)** inspirado en la película "Minority Report" de Spielberg.

## 📋 Descripción

Este proyecto implementa una arquitectura **GAN-like** con redes neuronales gráficas para:
- **Generar** una ciudad sintética completa con ciudadanos, ubicaciones y crímenes históricos
- **Generar** embeddings que representen "intenciones criminales" (Criminal Generator - GraphSAGE)
- **Discriminar** entre crímenes reales y ruido (Police Discriminator - GAT)
- **Predecir** potenciales incidentes criminales en una ciudad

### 🆕 Nuevas Características (Parte 2 y 3)

- ✅ **Generador de Ciudad Sintética**: Crea una ciudad completa con patrones realistas
- ✅ **Homofilia Programada**: Criminales se conectan entre sí (pandillas)
- ✅ **Crimen Contextual**: Los crímenes dependen del tipo de ubicación
- ✅ **Data Hydrator**: Transforma Neo4j → Tensores PyTorch
- ✅ **Datos Reales**: Entrena con datos de grafos reales, no aleatorios

## 🏗️ Arquitectura

### Componentes Principales

```
┌─────────────────────────────────────┐
│   CRIMINAL GENERATOR (GraphSAGE)    │
│  Genera embeddings de intenciones   │
│  basadas en estructura de vecindad  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  POLICE DISCRIMINATOR (GAT)         │
│  Evalúa riesgo real vs ruido        │
│  Usa atención para detectar patrones│
└─────────────────────────────────────┘
               │
               ▼
          PREDICCIONES
       (Risk Scores 0-1)
```

### Archivos Principales

```
src/
├── main.py              # Punto de entrada principal
├── models.py            # Definición de modelos (Generator, Discriminator)
├── train.py             # Loop de entrenamiento GAN
├── evaluate.py          # Script de evaluación
├── connector.py         # Conexión a Neo4j
├── utils.py             # Funciones auxiliares
├── city_generator.py    # 🆕 Generador de ciudad sintética (Parte 2)
└── data_hydrator.py     # 🆕 Transformación Neo4j → PyTorch (Parte 3)

scripts/
└── setup_db.cypher      # Script para inicializar Neo4j

data/                    # Datos procesados
├── precrime_graph.pt    # 🆕 Tensores listos para entrenar

.env                     # Variables de entorno
requirements.txt         # Dependencias Python
```

## 🚀 Instalación

### 1. Crear Entorno Virtual
```bash
cd Project_Pre_Crime
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno
Edita `.env` según tus necesidades:
```env
NEO4J_URI=bolt://localhost:7687
NUM_NODES=100
EPOCHS=100
EXPORT_TO_NEO4J=false
```

## 📊 Uso

### Modo 1: Entrenamiento Rápido (Datos Sintéticos Dummy)

```bash
python src/main.py
```

Esto entrena con datos aleatorios generados al vuelo.

### 🆕 Modo 2: Workflow Completo (Ciudad Real)

**Paso 1: Generar ciudad sintética en Neo4j**
```bash
python src/city_generator.py
```

Esto crea:
- 1000 ciudadanos con identidades realistas
- 50 ubicaciones (bancos, callejones, parques, etc.)
- Red social con homofilia (criminales se conocen)
- Rutinas diarias
- Crímenes históricos contextuales

**Paso 2: Transformar a tensores PyTorch**
```bash
python src/data_hydrator.py
```

Esto extrae:
- Features de nodos (edad, conexiones, lugares visitados)
- Estructura del grafo (edge_index)
- Labels (criminal/inocente)
- Split train/val/test

**Paso 3: Entrenar con datos reales**

Edita `.env`:
```env
USE_REAL_DATA=true  # Cambia de false a true
```

Luego:
```bash
python src/main.py
```

### 🚀 Modo 3: Demo Automática

Script todo-en-uno que ejecuta todo el workflow:

```bash
./demo_workflow.sh
```

### Evaluar Modelo

```bash
python src/evaluate.py
```

## 📈 Parámetros de Entrenamiento

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `EPOCHS` | 100 | Épocas de entrenamiento |
| `NUM_NODES` | 100 | Nodos en el grafo |
| `NUM_EDGES` | 300 | Aristas en el grafo |
| `HIDDEN_DIM` | 64 | Dimensión de capas ocultas |
| `LEARNING_RATE_G` | 0.001 | Tasa de aprendizaje del generador |
| `LEARNING_RATE_D` | 0.001 | Tasa de aprendizaje del discriminador |

## 🔗 Integración Neo4j

### Opción 1: Generar Ciudad Sintética (Recomendado)

```bash
# Generar ciudad completa
python src/city_generator.py

# Visualizar en Neo4j Browser
# http://localhost:7474
```

**Consultas útiles:**

Ver células criminales (pandillas):
```cypher
MATCH (c1:Citizen)-[:KNOWS]-(c2:Citizen)
WHERE c1.risk_seed > 0.7 AND c2.risk_seed > 0.7
RETURN c1, c2 LIMIT 50
```

Ver mapa de crímenes:
```cypher
MATCH (c:Citizen)-[crime:COMMITTED_CRIME]->(l:Location)
RETURN c, crime, l LIMIT 30
```

### Opción 2: Inicializar Base de Datos Manualmente

```bash
cypher-shell -u neo4j -p password < scripts/setup_db.cypher
```

### Exportar Predicciones

En `.env`, cambia:
```env
EXPORT_TO_NEO4J=true
```

Luego ejecuta:
```bash
python src/main.py
```

## 📊 Estructura de Datos Neo4j

### Nodos
- **Citizen**: Personas en la ciudad
  - Propiedades: `id`, `name`, `risk_base`, `status`
  
- **Location**: Lugares/ubicaciones
  - Propiedades: `id`, `type`, `crime_rate`

### Relaciones
- **LIVES_IN**: Ciudadano vive en ubicación
- **VISITS**: Ciudadano visita ubicación
- **WILL_COMMIT**: Predicción de crimen (ROJO, añadida por el modelo)

## 🧪 Ejemplo de Salida

```
============================================================
INICIANDO SISTEMA DE PREDICCIÓN PRE-CRIME
============================================================
Dispositivo: cuda

[PASO 1] Cargando datos del grafo...
Grafo creado: 100 nodos, 300 aristas

[PASO 2] Entrenando modelo Pre-Crime (GAN)...
Epoch 0 | Loss Policía: 1.5457 | Loss Criminal: 0.6410
Epoch 10 | Loss Policía: 1.5971 | Loss Criminal: 0.5842
...
Epoch 90 | Loss Policía: 1.6941 | Loss Criminal: 0.7722

✓ Modelo entrenado exitosamente

[PASO 3] Guardando modelo...
✓ Modelos guardados en models

[PASO 4] Generando predicciones...
✓ Predicciones generadas. Riesgo promedio: 0.5522
============================================================
```

## 🤖 Modelos

### CrimeGenerator (GraphSAGE)
- **Entrada**: Características de nodos + estructura del grafo
- **Procesamiento**: 2 capas SAGEConv
- **Salida**: Embeddings latentes (intenciones criminales)

### PoliceDiscriminator (GAT)
- **Entrada**: Embeddings + estructura del grafo
- **Procesamiento**: 2 capas GAT con attention heads
- **Salida**: Probabilidad de riesgo (0-1)

## 📚 Dependencias

- **PyTorch**: Framework de aprendizaje profundo
- **PyG (Torch Geometric)**: Redes neuronales gráficas
- **Neo4j**: Base de datos de grafos
- **NumPy**: Computación numérica
- **Scikit-learn**: Machine learning utilities
- **Faker**: 🆕 Generación de datos sintéticos realistas
- **tqdm**: 🆕 Barras de progreso

## 🔧 Configuración Avanzada

### Usar GPU/CUDA
```bash
export DEVICE=cuda
python src/main.py
```

### Cambiar Arquitectura
Edita `src/models.py` para modificar:
- Número de capas
- Dimensiones ocultas
- Función de activación
- Mecanismos de atención

### Cargar Datos Reales
Implementa en `src/utils.py`:
```python
def create_real_graph_from_neo4j(...)
```

## 📝 Logging

Los logs se guardan en `precrime.log` y se muestran en consola.

Niveles: INFO, WARNING, ERROR

## x] Arquitectura GAN básica (GraphSAGE + GAT)
- [x] 🆕 Generador de ciudad sintética completa
- [x] 🆕 Transformación Neo4j → Tensores PyTorch
- [x] 🆕 Entrenamiento con datos reales del grafo
- [ ] Soporte para datos de crímenes reales
- [ ] Métricas avanzadas (Precision, Recall, F1)
- [ ] Dashboard de visualización
- [ ] API REST para predicciones
- [ ] Interpretabilidad (GradCAM para grafos)
- [ ] Sistema de alertas en tiempo real
- [ ] API REST para predicciones
- [ ] Interpretabilidad (GradCAM para grafos)

## ⚠️ Consideraciones Éticas

Este es un **proyecto educativo** inspirado en ciencia ficción. 

⚠️ **ADVERTENCIA**: Los sistemas de predicción de crímenes reales pueden perpetuar sesgos y discriminación. Usar con cuidado en aplicaciones reales.

## 📖 Referencias
5. 🆕 [Guía Completa Parte 2 y 3](PARTE_2_3_GUIA.md) - Generación de ciudad e hidratación de datos

## 📄 Documentación Adicional

- [README.md](README.md) - Este archivo (documentación general)
- [QUICKSTART.md](QUICKSTART.md) - Guía rápida de inicio
- [PARTE_2_3_GUIA.md](PARTE_2_3_GUIA.md) - 🆕 Guía detallada de generación de ciudad
- [PROYECTO.txt](PROYECTO.txt) - Descripción visual del proyecto

1. "Minority Report" - Película (Spielberg, 2002)
2. "Semi-Supervised Classification with Graph Convolutional Networks" - Kipf & Welling (2017)
3. "Inductive Representation Learning on Large Graphs" - Hamilton et al. (GraphSAGE)
4. "Graph Attention Networks" - Velickovic et al. (2018)

## 👨‍💻 Autor

Rubences - MasterIA Project

## 📄 Licencia

MIT License

---

**¿Tienes preguntas?** Abre un issue en el repositorio.
