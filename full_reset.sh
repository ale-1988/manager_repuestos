#!/bin/bash

echo "=============================================="
echo "     FULL RESET DEL PROYECTO DJANGO           "
echo "  (migraciones, pycache, base principal)      "
echo "=============================================="

# CONFIGURACIÓN
DB_NAME="manager_repuestos"
DB_USER="root"
DB_PASS="Tvq114-e112906"   # <-- Cambiar aquí o usar mysql_config_editor
PYTHON="python3"        # o python si corresponde

echo ""
echo "Este script:"
echo " - BORRA TODAS las migraciones"
echo " - BORRA TODOS los __pycache__"
echo " - OPCIONAL: Drop y recrea la base $DB_NAME"
echo " - Ejecuta makemigrations y migrate"
echo ""

read -p "¿Querés borrar y recrear la base completa $DB_NAME? (s/N): " DROPCONF

if [[ "$DROPCONF" == "s" || "$DROPCONF" == "S" ]]; then
    echo ""
    echo "🧨 BORRANDO BASE $DB_NAME ..."
    mysql -u "$DB_USER" -p"$DB_PASS" -e "DROP DATABASE IF EXISTS $DB_NAME;"
    echo "🟩 Creando base $DB_NAME ..."
    mysql -u "$DB_USER" -p"$DB_PASS" -e "CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
else
    echo "⏭  Saltando DROP/CREATE base."
fi

echo ""
echo "🧹 Eliminando migraciones..."
find . -path "*/migrations/*.py" ! -name "__init__.py" -delete

echo ""
echo "🧹 Eliminando __pycache__..."
find . -type d -name "__pycache__" -exec rm -rf {} +

echo ""
echo "🧹 Eliminando archivos .pyc..."
find . -name "*.pyc" -delete

echo ""
echo "🧹 Limpiando entradas de migraciones de django..."
mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "DELETE FROM django_migrations;"

echo ""
echo "⚙️ Generando nuevas migraciones..."
$PYTHON manage.py makemigrations

echo ""
echo "⚙️ Aplicando migraciones..."
$PYTHON manage.py migrate

echo ""
read -p "¿Querés crear un superusuario ahora? (s/N): " SUCONF

if [[ "$SUCONF" == "s" || "$SUCONF" == "S" ]]; then
    $PYTHON manage.py createsuperuser
else
    echo "⏭  Saltando creación de superusuario."
fi

echo ""
echo "=============================================="
echo "     ✔ FULL RESET COMPLETADO                  "
echo "     Podés correr el servidor ahora:          "
echo "     $PYTHON manage.py runserver              "
echo "=============================================="
