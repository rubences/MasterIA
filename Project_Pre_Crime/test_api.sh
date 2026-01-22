#!/bin/bash
# Script de prueba rápida de la API Pre-Crime

echo "🧪 Pruebas de API Pre-Crime"
echo "==========================="
echo ""

API_URL="http://localhost:8000"

echo "1️⃣  Health Check..."
curl -s "$API_URL/health" | python -m json.tool 2>/dev/null || echo "❌ Error"
echo ""

echo "2️⃣  Info del sistema..."
curl -s "$API_URL/info" | python -m json.tool 2>/dev/null || echo "❌ Error"
echo ""

echo "3️⃣  Listar primeros 5 ciudadanos..."
curl -s "$API_URL/citizens/?limit=5" | python -m json.tool 2>/dev/null || echo "❌ Error o BD vacía"
echo ""

echo "4️⃣  Análisis de riesgo (ciudadano #1)..."
curl -s "$API_URL/precogs/scan/1" | python -m json.tool 2>/dev/null || echo "❌ Error o ciudadano no existe"
echo ""

echo "5️⃣  Ciudadanos de alto riesgo..."
curl -s "$API_URL/precogs/high-risk" | python -m json.tool 2>/dev/null || echo "❌ Error"
echo ""

echo "✅ Pruebas completadas"
echo ""
echo "📖 Para más endpoints, visita: $API_URL/docs"
