#!/bin/bash
set -e

cd /workspace

echo "--- Instalando dependencias del backend ---"
pip install --no-cache-dir -r backend/requirements.txt

echo "--- Instalando dependencias del frontend ---"
cd frontend && npm install && cd ..

echo "--- Ejecutando migraciones ---"
cd backend && alembic upgrade head && cd ..

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
