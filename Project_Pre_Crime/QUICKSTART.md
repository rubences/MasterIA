# 🚀 Guía de Inicio Rápido - Sistema Pre-Crime

## Opción 1: Script Automático (Recomendado)

```bash
cd /workspaces/MasterIA/Project_Pre_Crime
chmod +x run.sh
./run.sh
```

Esto:
1. ✓ Crea el entorno virtual automáticamente
2. ✓ Instala todas las dependencias
3. ✓ Te muestra un menú interactivo

## Opción 2: Ejecución Manual

### Paso 1: Activar Entorno
```bash
cd /workspaces/MasterIA/Project_Pre_Crime
source venv/bin/activate
```

O usa el script rápido:
```bash
./activate.sh
```

### Paso 2: Entrenar el Modelo
```bash
python src/main.py
```

**Salida esperada:**
```
============================================================
INICIANDO SISTEMA DE PREDICCIÓN PRE-CRIME
============================================================
Dispositivo: cuda (o cpu)
Configuración cargada: {...}

[PASO 1] Cargando datos del grafo...
Grafo creado: 100 nodos, 300 aristas

[PASO 2] Entrenando modelo Pre-Crime (GAN)...
Epoch 0 | Loss Policía: 1.5457 | Loss Criminal: 0.6410
...
Epoch 90 | Loss Policía: 1.6941 | Loss Criminal: 0.7722

✓ Modelo entrenado exitosamente

[PASO 3] Guardando modelo...
✓ Modelos guardados en models

[PASO 4] Generando predicciones...
✓ Predicciones generadas. Riesgo promedio: 0.5522
============================================================
✓ Ejecución exitosa
```

### Paso 3: Evaluar el Modelo
```bash
python src/evaluate.py
```

**Salida esperada:**
```
============================================================
EVALUACIÓN DEL SISTEMA PRE-CRIME
============================================================
Cargando datos de prueba...
Cargando modelos entrenados...
✓ Modelos cargados

Evaluando modelo...

============================================================
MÉTRICAS DE EVALUACIÓN
============================================================
  mean_risk: 0.5370
  max_risk: 0.7212
  min_risk: 0.3974
  std_risk: 0.0437
============================================================
```

## Estructura de Archivos

```
Project_Pre_Crime/
├── src/                    # Código fuente
│   ├── main.py            # Punto de entrada principal
│   ├── models.py          # Modelos GAN (Generator, Discriminator)
│   ├── train.py           # Loop de entrenamiento
│   ├── evaluate.py        # Evaluación del modelo
│   ├── connector.py       # Conexión a Neo4j
│   └── utils.py           # Funciones auxiliares
│
├── scripts/               # Scripts de configuración
│   └── setup_db.cypher    # Inicialización de Neo4j
│
├── models/                # Modelos entrenados (generados automáticamente)
│   ├── generator.pth
│   └── discriminator.pth
│
├── data/                  # Datos (generados automáticamente)
├── logs/                  # Logs (generados automáticamente)
│
├── .env                   # Variables de entorno
├── requirements.txt       # Dependencias Python
├── README.md             # Documentación completa
├── run.sh                # Script de ejecución
├── activate.sh           # Script de activación de venv
└── precrime.log          # Log de ejecución
```

## Configuración Personalizada

### Editar `.env`

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Grafo
NUM_NODES=100              # Aumenta para grafos más grandes
NUM_EDGES=300
NUM_FEATURES=16
HIDDEN_DIM=64

# Entrenamiento
EPOCHS=100                 # Más épocas = mejor entrenamiento
LEARNING_RATE_G=0.001      # Tasa de aprendizaje generador
LEARNING_RATE_D=0.001      # Tasa de aprendizaje discriminador

# Exportación
EXPORT_TO_NEO4J=false      # Cambia a true para usar Neo4j real
```

### Usar GPU (CUDA)

Si tienes NVIDIA GPU:
```bash
# El sistema detecta automáticamente CUDA si está disponible
python src/main.py

# Verificar disponibilidad:
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

## Solución de Problemas

### "ModuleNotFoundError: No module named 'X'"

Solución:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Neo4j connection refused"

Solución:
- Neo4j no está disponible por defecto
- Cambia `EXPORT_TO_NEO4J=false` en `.env` (por defecto)
- O instala Neo4j localmente y configura la conexión

### Lentitud del entrenamiento

Posibles causas:
- Estás usando CPU en lugar de GPU
- Aumenta `NUM_NODES` y `NUM_EDGES` en `.env`
- Reduce `EPOCHS` para pruebas rápidas

## Comandos Útiles

```bash
# Ver Python version
python --version

# Ver versiones de librerías
pip list | grep -E "torch|neo4j|numpy"

# Ver logs en tiempo real
tail -f precrime.log

# Entrenar con diferentes parámetros
export EPOCHS=50
python src/main.py

# Limpiar modelos anteriores
rm -rf models/*.pth

# Desactivar entorno virtual
deactivate
```

## Próximos Pasos

1. **Leer documentación completa** → [README.md](README.md)
2. **Entender la arquitectura** → Ver `src/models.py`
3. **Modificar hiperparámetros** → Editar `.env` y `src/train.py`
4. **Integrar datos reales** → Implementar en `src/utils.py`
5. **Conectar a Neo4j** → Cambiar `EXPORT_TO_NEO4J=true`

## Support

¿Problemas? Revisa:
- `precrime.log` para detalles de errores
- `README.md` para documentación completa
- Los comentarios en el código fuente

---

**¡Disfruta prediciendo crímenes como los Precogs de Minority Report!** 🚨
