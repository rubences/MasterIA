# Pre-Crime Department API 🔮

Sistema de predicción de crímenes usando **Graph Neural Networks** (GNN) y **FastAPI**.

## Arquitectura

```
/app
├── main.py              # Punto de entrada FastAPI
├── config.py            # Configuración y variables de entorno
├── /core
│   ├── database.py      # Gestor Neo4j asíncrono
│   └── ai_engine.py     # Motor de inferencia (Precogs)
├── /models
│   ├── schemas.py       # Modelos Pydantic (DTOs)
│   └── neural_net.py    # Redes neuronales PyTorch
└── /routers
    ├── citizens.py      # Endpoints de ciudadanos
    └── predictions.py   # Endpoints de predicciones
```

## Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo de ejemplo y edita con tus credenciales:

```bash
cp .env.example .env
nano .env
```

Variables clave:
- `NEO4J_URI`: URL de tu base de datos Neo4j
- `NEO4J_USER` / `NEO4J_PASSWORD`: Credenciales
- `MODEL_PATH`: Ruta al modelo entrenado (`.pt`)
- `DEVICE`: `cpu` o `cuda`

### 3. Iniciar el servidor

```bash
# Modo desarrollo (con auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Modo producción
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

O directamente:

```bash
python -m app.main
```

## Uso de la API

### Documentación interactiva

Una vez iniciado el servidor, visita:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints principales

#### 🔍 Listar ciudadanos

```bash
curl http://localhost:8000/citizens/?limit=10
```

#### 🔮 Analizar riesgo de un ciudadano

```bash
curl http://localhost:8000/precogs/scan/42
```

Respuesta ejemplo:
```json
{
  "subject_id": 42,
  "subject_name": "John Anderton",
  "probability": 0.92,
  "verdict": "INTERVENE",
  "confidence": 0.88,
  "analyzed_at": "2026-01-22T16:30:00"
}
```

Verdicts posibles:
- `SAFE`: Probabilidad < 60%
- `WATCHLIST`: Probabilidad 60-85%
- `INTERVENE`: Probabilidad > 85% (🔴 Bola Roja)

#### 📊 Análisis masivo

```bash
curl -X POST http://localhost:8000/precogs/batch-scan \
  -H "Content-Type: application/json" \
  -d '{"citizen_ids": [1, 2, 3, 42, 100]}'
```

#### 🚨 Ciudadanos de alto riesgo

```bash
curl http://localhost:8000/precogs/high-risk?threshold=0.7
```

#### 🌐 Red social de un ciudadano

```bash
curl http://localhost:8000/citizens/42/network
```

#### ❤️ Health Check

```bash
curl http://localhost:8000/health
```

## Estructura de Datos

### Ciudadano (CitizenFeatureVector)

```json
{
  "id": 42,
  "name": "John Anderton",
  "status": "ACTIVE",
  "criminal_degree": 3,
  "risk_seed": 0.45,
  "job_vector": [0.0, 1.0, 0.0, ...],
  "age_normalized": 0.35
}
```

### Predicción (PredictionOutput)

```json
{
  "subject_id": 42,
  "subject_name": "John Anderton",
  "probability": 0.92,
  "verdict": "INTERVENE",
  "confidence": 0.88,
  "analyzed_at": "2026-01-22T16:30:00.123456"
}
```

## Flujo de Inferencia

1. **Request**: Cliente solicita análisis de ciudadano por ID
2. **Data Hydration**: FastAPI consulta Neo4j para extraer:
   - Datos del ciudadano (edad, trabajo, risk_seed)
   - Red social (contactos criminales)
3. **Feature Engineering**: Se construye tensor de entrada:
   - Age normalizada
   - One-hot encoding de trabajo
   - Grado criminal (número de amigos con crímenes)
4. **Inference**: Modelo PyTorch (GraphSAGE/GAT) predice probabilidad
5. **Verdict**: Se clasifica según umbrales configurados
6. **Response**: JSON con predicción y metadata

## Arquitectura Asíncrona

La API usa **async/await** nativo de Python para:
- Consultas Neo4j no bloqueantes
- Procesamiento paralelo de múltiples requests
- Background tasks (registro de "Bolas Rojas")

Esto permite manejar cientos de requests/segundo en un solo proceso.

## Modelos de IA

Los modelos se cargan **una sola vez** al iniciar el servidor (evento `lifespan`):

- **CrimeGenerator**: GraphSAGE para generar embeddings
- **PoliceDiscriminator**: GAT para clasificación de riesgo

Si no se encuentra `MODEL_PATH`, la API funciona en **modo heurístico** usando `risk_seed` y `criminal_degree`.

## Despliegue en Producción

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY src/ ./src/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose con Neo4j

```yaml
version: '3.8'
services:
  neo4j:
    image: neo4j:5.16
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/password

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: password
    depends_on:
      - neo4j
```

## Testing

```bash
# Ejecutar tests unitarios
pytest tests/

# Verificar health
curl http://localhost:8000/health

# Análisis de ciudadano de prueba
curl http://localhost:8000/precogs/scan/1
```

## Logs

Los logs se imprimen en stdout con formato:

```
2026-01-22 16:30:00 - PreCrimeAPI - INFO - 🔮 Iniciando Sistema Pre-Crime...
2026-01-22 16:30:01 - PreCrimeDB - INFO - 🔌 Conectado a Neo4j en bolt://localhost:7687
2026-01-22 16:30:02 - PreCogSystem - INFO - ✅ Modelos cargados exitosamente
2026-01-22 16:30:15 - PredictionsRouter - INFO - 🔮 Análisis completado: Ciudadano #42 → INTERVENE (92.0%)
```

## Troubleshooting

### Error: "El driver de Neo4j no está inicializado"

- Verifica que Neo4j esté corriendo: `docker ps`
- Comprueba las credenciales en `.env`
- Health check: `curl http://localhost:8000/health`

### Error: "No se pudieron importar modelos"

- Asegúrate de que `src/models.py` existe
- El sistema funcionará en modo heurístico

### Modelos no se cargan

- Verifica que `MODEL_PATH` apunte a un archivo `.pt` válido
- Si no tienes modelo entrenado, ejecuta primero `python src/train.py`

## Próximos Pasos

- [ ] Añadir autenticación JWT
- [ ] Implementar rate limiting
- [ ] Cache con Redis para predicciones recientes
- [ ] WebSocket para streaming de predicciones en vivo
- [ ] Frontend React con visualización del grafo

---

**Desarrollado con** 🔮 **para el Pre-Crime Department**
