# 🏙️ Guía: Generación de Ciudad Sintética - Parte 2 y 3

## Introducción

Esta guía cubre la **Parte 2** (Generación de Ciudad) y **Parte 3** (Hidratación de Datos) del proyecto Pre-Crime. Aprenderás a crear una ciudad completa con patrones criminales realistas y prepararla para entrenamiento de IA.

---

## 📋 Tabla de Contenidos

1. [Preparación del Entorno](#preparación)
2. [Parte 2: Generación de Ciudad](#parte-2)
3. [Parte 3: Hidratación de Datos](#parte-3)
4. [Visualización en Neo4j](#visualización)
5. [Entrenamiento con Datos Reales](#entrenamiento)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Preparación del Entorno {#preparación}

### 1. Instalar nuevas dependencias

```bash
cd /workspaces/MasterIA/Project_Pre_Crime
source venv/bin/activate
pip install -r requirements.txt
```

Esto instalará:
- `faker`: Generación de datos sintéticos realistas
- `tqdm`: Barras de progreso

### 2. Verificar Neo4j

Asegúrate de tener Neo4j corriendo:

```bash
# Si usas Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# Verificar que esté corriendo
curl http://localhost:7474
```

O accede a: http://localhost:7474

---

## 🏙️ Parte 2: Generación de Ciudad {#parte-2}

### ¿Qué hace este script?

El `city_generator.py` crea una ciudad completa con:

✅ **1000 ciudadanos** con identidades realistas (nombres, trabajos, edades)  
✅ **50 ubicaciones** (bancos, callejones, parques, cafés, etc.)  
✅ **Red social** con patrón de "Small World" (homofilia)  
✅ **Rutinas diarias** (ciudadanos visitan lugares regularmente)  
✅ **Crímenes históricos** contextuales y realistas  

### Conceptos Clave

#### 1. **Semilla de Riesgo (risk_seed)**

```python
risk_seed = random.betavariate(2, 10)
```

- Variable **oculta** que simula factores socioeconómicos
- Mayoría de ciudadanos tienen riesgo bajo (≈0.1)
- Pequeño porcentaje tiene riesgo alto (>0.7)
- La IA intentará **descubrir** este patrón

#### 2. **Homofilia Programada**

```python
if person["risk"] > 0.6 and friend["risk"] > 0.6:
    prob += 0.5  # Criminales se conocen entre sí
```

- Los nodos similares tienden a conectarse
- Simula **pandillas** y crimen organizado
- Fundamental para que GraphSAGE funcione

#### 3. **Crimen Contextual**

```python
if target["type"] == "Bank":
    crime_type = "Robbery"  # Roban bancos
elif target["type"] == "Park":
    crime_type = "Vandalism"  # Vandalizan parques
```

- El tipo de crimen depende del lugar
- Crea patrones que GAT puede aprender

### Ejecución

```bash
# Opción 1: Usar valores por defecto (1000 ciudadanos, 50 ubicaciones)
python src/city_generator.py

# Opción 2: Personalizar tamaño
python src/city_generator.py 500 30  # 500 ciudadanos, 30 ubicaciones
```

**Salida esperada:**

```
======================================================================
🚨 PRE-CRIME CITY GENERATOR 🚨
Generando ciudad sintética estilo Minority Report
======================================================================

🛡️ Estableciendo leyes físicas (Indices)...
🧹 Limpiando la ciudad (Base de datos)...
🏢 Construyendo 50 ubicaciones...
👥 Poblando la ciudad con 1000 ciudadanos...
🕸️ Tejiendo la red social...
Social Links: 100%|███████████████████| 1000/1000 [00:15<00:00, 65.2it/s]
🚶 Estableciendo rutinas diarias...
Routines: 100%|██████████████████████| 1000/1000 [00:03<00:00, 320.5it/s]
🚨 Generando historial criminal...

======================================================================
✅ CIUDAD GENERADA EXITOSAMENTE
⏱️  Tiempo total: 23.45 segundos
======================================================================

📊 Estadísticas de la ciudad:
  👥 Ciudadanos: 1000
  🏢 Ubicaciones: 50
  🤝 Conexiones sociales: 3247
  🚶 Rutinas establecidas: 5432
  🚨 Crímenes históricos: 287
  👮 Criminales únicos: 58 (5.8%)
  🕸️ Densidad de red: 0.0032
```

---

## 🧪 Parte 3: Hidratación de Datos {#parte-3}

### ¿Qué hace este script?

El `data_hydrator.py` transforma el grafo de Neo4j en tensores PyTorch:

1. **Extrae features de nodos**: edad, conexiones, lugares visitados, riesgo ambiental
2. **Extrae estructura del grafo**: edge_index para PyTorch Geometric
3. **Crea labels**: 1 = criminal, 0 = inocente
4. **Divide en train/val/test**: 70% / 15% / 15%
5. **Guarda en disco**: `data/precrime_graph.pt`

### Features Extraídas

Por cada ciudadano, se extraen **5 features normalizadas**:

```python
[
    edad_normalizada,          # 0-1
    degree_normalizado,        # Número de amigos (log scale)
    lugares_normalizados,      # Lugares visitados
    riesgo_ambiental_promedio, # Riesgo de lugares frecuentados
    crímenes_normalizados      # Historial criminal
]
```

### Ejecución

```bash
python src/data_hydrator.py
```

**Salida esperada:**

```
======================================================================
🧪 PRE-CRIME DATA HYDRATOR
Transformando grafo Neo4j → Tensores PyTorch
======================================================================

📊 Extrayendo características de nodos...
  Dimensión de features: torch.Size([1000, 5])
  Criminales detectados: 58 (5.8%)

🕸️ Extrayendo estructura del grafo...
  Dimensión del grafo: torch.Size([2, 3247])

🔍 Analizando patrones criminales...
  Total de crímenes: 287
  Tipos de crimen: ['Robbery', 'Assault', 'Vandalism']
  Severidad promedio: 6.43

🔧 Creando objeto PyTorch Geometric...
  ✓ Nodos: 1000
  ✓ Aristas: 3247
  ✓ Features por nodo: 5
  ✓ Labels: torch.Size([1000])

📈 Estadísticas del dataset:
  Clase 0 (Inocentes): 942
  Clase 1 (Criminales): 58
  Desbalance: 5.80% criminales

✂️ Dividiendo dataset en train/val/test...
  Train: 700 nodos (70%)
  Val: 150 nodos (15%)
  Test: 150 nodos (15%)

💾 Dataset guardado en: data/precrime_graph.pt

======================================================================
✅ DATOS HIDRATADOS EXITOSAMENTE
======================================================================
```

---

## 🔍 Visualización en Neo4j {#visualización}

### Verificar que la ciudad fue creada

Abre Neo4j Browser: http://localhost:7474

#### Query 1: Ver toda la ciudad

```cypher
MATCH (n)
RETURN n
LIMIT 100
```

#### Query 2: Ver células criminales (pandillas)

```cypher
// Ver comunidades de criminales
MATCH (c1:Citizen)-[:KNOWS]-(c2:Citizen)
WHERE c1.risk_seed > 0.7 AND c2.risk_seed > 0.7
RETURN c1, c2
LIMIT 50
```

Deberías ver **clusters densos** de nodos conectados. Esas son las pandillas.

#### Query 3: Mapa de crímenes

```cypher
MATCH (c:Citizen)-[crime:COMMITTED_CRIME]->(l:Location)
RETURN c, crime, l
LIMIT 30
```

#### Query 4: Estadísticas rápidas

```cypher
// Contar todo
MATCH (c:Citizen) RETURN count(c) as Ciudadanos
UNION
MATCH (l:Location) RETURN count(l) as Ubicaciones
UNION
MATCH ()-[:KNOWS]->() RETURN count(*) as Amistades
UNION
MATCH ()-[:COMMITTED_CRIME]->() RETURN count(*) as Crímenes
```

---

## 🚀 Entrenamiento con Datos Reales {#entrenamiento}

### Activar datos reales

Edita `.env`:

```env
USE_REAL_DATA=true  # Cambia de false a true
```

### Entrenar el modelo

```bash
python src/main.py
```

Ahora el modelo usará:
- **Datos reales** de la ciudad generada
- **Features enriquecidas** (5 features vs 16 aleatorias)
- **Labels verdaderas** (criminales vs inocentes)

**Diferencias clave:**

| Aspecto | Datos Dummy | Datos Reales |
|---------|-------------|--------------|
| Features | 16 aleatorias | 5 significativas |
| Grafo | Conexiones aleatorias | Red social realista |
| Labels | No hay | Criminal/Inocente |
| Precisión esperada | ~50% (azar) | >80% (aprende patrones) |

---

## ❓ Troubleshooting {#troubleshooting}

### Error: "Connection refused" (Neo4j)

**Problema:** Neo4j no está corriendo.

**Solución:**
```bash
# Docker
docker start neo4j

# O inicia uno nuevo
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j
```

### Error: "Constraint already exists"

**Problema:** La base de datos no está limpia.

**Solución:**
```cypher
// En Neo4j Browser
MATCH (n) DETACH DELETE n
```

O ejecuta de nuevo el generador (limpia automáticamente).

### Error: "No se pudieron cargar datos reales"

**Problema:** No ejecutaste `data_hydrator.py`.

**Solución:**
```bash
# Primero genera la ciudad
python src/city_generator.py

# Luego hidrata los datos
python src/data_hydrator.py

# Finalmente entrena
python src/main.py
```

### La generación es muy lenta

**Problema:** Muchas conexiones sociales.

**Solución 1:** Reduce el tamaño de la ciudad:
```bash
python src/city_generator.py 500 30  # Más pequeña
```

**Solución 2:** Ajusta la probabilidad de conexión en `city_generator.py`:
```python
prob = 0.05  # Reduce de 0.1 a 0.05
```

### Desbalance de clases extremo

**Problema:** Muy pocos criminales generados.

**Solución:** Ajusta la distribución Beta en `city_generator.py`:
```python
risk_seed = random.betavariate(2, 8)  # Más peligrosos (antes era 2, 10)
```

---

## 🎯 Workflow Completo

```bash
# Paso 1: Activar entorno
source venv/bin/activate

# Paso 2: Generar ciudad
python src/city_generator.py

# Paso 3: Hidratar datos
python src/data_hydrator.py

# Paso 4: Activar datos reales
# Edita .env: USE_REAL_DATA=true

# Paso 5: Entrenar modelo
python src/main.py

# Paso 6: Evaluar
python src/evaluate.py
```

---

## 📊 Métricas Esperadas

Con datos reales, deberías ver:

```
Epoch 0 | Loss Policía: 0.9234 | Loss Criminal: 1.2341
Epoch 10 | Loss Policía: 0.7123 | Loss Criminal: 0.9876
...
Epoch 90 | Loss Policía: 0.3456 | Loss Criminal: 0.5432

✓ Predicciones generadas. Riesgo promedio: 0.2341
```

**Interpretación:**
- Riesgo promedio **bajo** (~0.2-0.3) = Mayoría son inocentes ✓
- Algunos nodos con riesgo **alto** (>0.8) = Criminales detectados ✓
- Loss bajando consistentemente = Modelo aprendiendo ✓

---

## 🔗 Referencias

- [Parte 1: Arquitectura](../README.md)
- [Neo4j Graph Data Science](https://neo4j.com/docs/graph-data-science/)
- [PyTorch Geometric Docs](https://pytorch-geometric.readthedocs.io/)
- [Faker Documentation](https://faker.readthedocs.io/)

---

**¡Ahora tienes una ciudad completa para entrenar a tus Precogs! 🚨**
