#!/bin/bash
# Script para activar el entorno virtual

source venv/bin/activate
echo "✓ Entorno virtual activado"
echo "Python version: $(python --version)"
echo "Dependencias instaladas:"
pip list | grep -E "torch|neo4j|numpy|scikit" | sed 's/^/  - /'
