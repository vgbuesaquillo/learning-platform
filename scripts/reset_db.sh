#!/usr/bin/env bash
# Resetea completamente la base de datos y vuelve a aplicar migraciones + seed
# USO: bash scripts/reset_db.sh

set -e
echo "⚠️  Esto BORRARÁ todos los datos. ¿Continuar? [s/N]"
read CONFIRM
if [[ ! "$CONFIRM" =~ ^[Ss]$ ]]; then
  echo "Cancelado."
  exit 0
fi

echo "Deteniendo servicios y borrando volúmenes..."
docker compose down -v

echo "Levantando servicios limpios..."
docker compose up -d db redis

sleep 5

echo "Aplicando migraciones..."
docker compose run --rm backend alembic upgrade head

echo "Cargando seed..."
docker compose run --rm backend python scripts/seed.py

echo "Levantando todos los servicios..."
docker compose up -d

echo "✅ Base de datos reseteada y servicios corriendo."
