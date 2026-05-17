#!/bin/bash
set -e

cd /workspace

echo "--- Instalando dependencias del backend ---"
pip install --no-cache-dir -r backend/requirements.txt

echo "--- Instalando dependencias del frontend ---"
cd frontend && npm install && cd ..

echo "--- Ejecutando migraciones ---"
cd backend && alembic upgrade head && cd ..

echo "--- Asegurando acceso a Docker ---"
# El socket de Docker del host tiene un GID distinto al del contenedor
# Solución: hacer el socket accesible para todos (devcontainer, no producción)
sudo chmod 666 /var/run/docker.sock

echo "--- Sembrando base de datos ---"
python backend/scripts/seed.py

echo ""
echo "==================================="
echo "  LearnPath listo en Codespaces!"
echo "==================================="
echo ""
echo "Para levantar los servidores:"
echo "  Backend:  cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo "  Frontend: cd frontend && npm run dev"
echo ""
