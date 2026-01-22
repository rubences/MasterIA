#!/bin/bash
# Script de inicio rápido para la API Pre-Crime

set -e

echo "🔮 Pre-Crime Department API - Inicio Rápido"
echo "=========================================="
echo ""

# Verificar entorno virtual
if [ ! -d "venv" ]; then
    echo "⚠️  No se encontró entorno virtual. Creando..."
    python3 -m venv venv
fi

echo "📦 Activando entorno virtual..."
source venv/bin/activate || source venv/Scripts/activate

echo "📥 Instalando/actualizando dependencias..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "🔧 Verificando configuración..."

# Verificar .env
if [ ! -f ".env" ]; then
    echo "⚠️  No se encontró archivo .env. Creando desde plantilla..."
    cp .env.example .env
    echo "   ⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales Neo4j"
    echo "   nano .env"
    echo ""
fi

# Verificar Neo4j (opcional)
echo "🔌 Probando conexión a Neo4j..."
if command -v nc &> /dev/null; then
    if nc -z localhost 7687 2>/dev/null; then
        echo "   ✅ Neo4j detectado en puerto 7687"
    else
        echo "   ⚠️  Neo4j no detectado. Asegúrate de que esté corriendo:"
        echo "   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.16"
    fi
else
    echo "   ℹ️  Saltando verificación de Neo4j (nc no disponible)"
fi

echo ""
echo "🚀 Iniciando servidor FastAPI..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "   Presiona Ctrl+C para detener"
echo ""

# Iniciar servidor
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
