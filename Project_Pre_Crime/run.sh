#!/bin/bash

# Script de configuración y ejecución del Sistema Pre-Crime
# =========================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

echo "🚨 SISTEMA PRE-CRIME"
echo "===================="
echo ""

# 1. Verificar si el entorno virtual existe
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv "$VENV_DIR"
fi

# 2. Activar entorno virtual
echo "🔌 Activando entorno virtual..."
source "$VENV_DIR/bin/activate"

# 3. Instalar/actualizar dependencias
echo "📥 Instalando dependencias..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 4. Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p models data logs

# 5. Mostrar información del sistema
echo ""
echo "✓ Entorno configurado"
echo "📊 Información del sistema:"
echo "  - Python: $(python --version)"
echo "  - PyTorch: $(python -c 'import torch; print(torch.__version__)')"
echo "  - CUDA disponible: $(python -c 'import torch; print(torch.cuda.is_available())')"
echo ""

# 6. Menú de opciones
echo "📋 Opciones disponibles:"
echo "  1) Ejecutar entrenamiento completo (python src/main.py)"
echo "  2) Evaluar modelo (python src/evaluate.py)"
echo "  3) Salir"
echo ""

read -p "Elige una opción (1-3): " option

case $option in
    1)
        echo ""
        echo "🚀 Iniciando entrenamiento..."
        echo ""
        python src/main.py
        ;;
    2)
        echo ""
        echo "📊 Evaluando modelo..."
        echo ""
        python src/evaluate.py
        ;;
    3)
        echo "👋 Hasta luego!"
        ;;
    *)
        echo "❌ Opción no válida"
        exit 1
        ;;
esac

echo ""
echo "✓ Listo"
