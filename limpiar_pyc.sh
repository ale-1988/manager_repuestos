#!/bin/bash

echo "----------------------------------------"
echo "   LIMPIANDO __pycache__  "
echo "----------------------------------------"

# 2. Borrar archivos .pyc
echo ""
echo "🧹 Eliminando archivos .pyc..."
find . -name "*.pyc" -delete

# 3. Borrar directorios __pycache__
echo ""
echo "🧹 Eliminando __pycache__..."
find . -type d -name "__pycache__" -exec rm -rf {} +

echo ""
echo "----------------------------------------"
echo "  ✔ Limpieza completada correctamente"
