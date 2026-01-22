#!/bin/bash
# Script de demostración completa del flujo de trabajo Pre-Crime
# Ejecuta todo el pipeline: Generación → Hidratación → Entrenamiento

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║  🚨 PRE-CRIME COMPLETE WORKFLOW DEMO 🚨                      ║"
echo "║                                                               ║"
echo "║  Minority Report meets Real Data Science                      ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Activar entorno
source venv/bin/activate

echo "📋 Este script ejecutará:"
echo "  1. city_generator.py   → Generar ciudad sintética en Neo4j"
echo "  2. data_hydrator.py    → Transformar a tensores PyTorch"
echo "  3. main.py (opcional)  → Entrenar modelo con datos reales"
echo ""
read -p "¿Continuar? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelado por el usuario"
    exit 0
fi

# Verificar que Neo4j esté disponible (opcional)
echo ""
echo "🔍 Verificando conexión a Neo4j..."
if python -c "from neo4j import GraphDatabase; GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')).verify_connectivity()" 2>/dev/null; then
    echo "✓ Neo4j está disponible"
else
    echo "⚠️  ADVERTENCIA: No se pudo conectar a Neo4j"
    echo "   El script continuará pero puede fallar."
    echo "   Para iniciar Neo4j con Docker:"
    echo "   docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j"
    echo ""
    read -p "¿Continuar de todas formas? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# PASO 1: Generar Ciudad
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "PASO 1/3: GENERANDO CIUDAD SINTÉTICA"
echo "════════════════════════════════════════════════════════════════"
echo ""

python src/city_generator.py

if [ $? -ne 0 ]; then
    echo "❌ Error en generación de ciudad"
    exit 1
fi

# PASO 2: Hidratar Datos
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "PASO 2/3: HIDRATANDO DATOS (Neo4j → PyTorch)"
echo "════════════════════════════════════════════════════════════════"
echo ""

python src/data_hydrator.py

if [ $? -ne 0 ]; then
    echo "❌ Error en hidratación de datos"
    exit 1
fi

# PASO 3: Entrenar (opcional)
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "PASO 3/3 (OPCIONAL): ENTRENAR MODELO"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "El dataset está listo en: data/precrime_graph.pt"
echo ""
read -p "¿Quieres entrenar el modelo ahora con datos REALES? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Activar datos reales temporalmente
    export USE_REAL_DATA=true
    
    echo ""
    echo "🚀 Iniciando entrenamiento con datos reales..."
    python src/main.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Entrenamiento completado"
        echo ""
        read -p "¿Evaluar el modelo? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python src/evaluate.py
        fi
    fi
fi

# Resumen final
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ WORKFLOW COMPLETADO"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Archivos generados:"
echo "  ✓ Neo4j Database: Ciudad con 1000 ciudadanos y relaciones"
echo "  ✓ data/precrime_graph.pt: Tensores listos para PyTorch"
if [ -f "models/generator.pth" ]; then
    echo "  ✓ models/generator.pth: Modelo generador entrenado"
    echo "  ✓ models/discriminator.pth: Modelo discriminador entrenado"
fi
echo ""
echo "🎯 Próximos pasos:"
echo "  1. Visualiza en Neo4j Browser: http://localhost:7474"
echo "  2. Consulta células criminales:"
echo "     MATCH (c1:Citizen)-[:KNOWS]-(c2:Citizen)"
echo "     WHERE c1.risk_seed > 0.7 AND c2.risk_seed > 0.7"
echo "     RETURN c1, c2 LIMIT 50"
echo ""
echo "  3. Para entrenar con datos reales:"
echo "     Edita .env: USE_REAL_DATA=true"
echo "     python src/main.py"
echo ""
echo "📚 Lee la guía completa: PARTE_2_3_GUIA.md"
echo ""
echo "════════════════════════════════════════════════════════════════"
