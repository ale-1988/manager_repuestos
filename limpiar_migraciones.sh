#!/bin/bash

echo "----------------------------------------"
echo "   LIMPIANDO MIGRACIONES Y __pycache__  "
echo "----------------------------------------"

# 1. Borrar todas las migraciones excepto __init__.py
echo ""
echo "🧹 Eliminando archivos de migración..."
find . -path "*/migrations/*.py" ! -name "__init__.py" -delete

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
echo "----------------------------------------"
echo ""
echo "Ahora ejecutá:"
echo "  python manage.py makemigrations"
echo "  python manage.py migrate"
echo "para regenerar migraciones limpias."
