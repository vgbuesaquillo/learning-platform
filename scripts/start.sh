#!/usr/bin/env bash
# =============================================================
# LearnPath — Script de inicio rápido
# Uso: bash scripts/start.sh
# =============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "  ██╗     ███████╗ █████╗ ██████╗ ███╗   ██╗██████╗  █████╗ ████████╗██╗  ██╗"
echo "  ██║     ██╔════╝██╔══██╗██╔══██╗████╗  ██║██╔══██╗██╔══██╗╚══██╔══╝██║  ██║"
echo "  ██║     █████╗  ███████║██████╔╝██╔██╗ ██║██████╔╝███████║   ██║   ███████║"
echo "  ██║     ██╔══╝  ██╔══██║██╔══██╗██║╚██╗██║██╔═══╝ ██╔══██║   ██║   ██╔══██║"
echo "  ███████╗███████╗██║  ██║██║  ██║██║ ╚████║██║     ██║  ██║   ██║   ██║  ██║"
echo "  ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "${YELLOW}  Plataforma de aprendizaje con medición de progreso real${NC}"
echo ""

# ── 1. Verificar dependencias ──────────────────────────────────────────────
echo -e "${BLUE}[1/5]${NC} Verificando dependencias..."

if ! command -v docker &>/dev/null; then
  echo -e "${RED}✗ Docker no encontrado. Instalar desde https://docker.com${NC}"
  exit 1
fi

if ! docker compose version &>/dev/null; then
  echo -e "${RED}✗ Docker Compose no encontrado.${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Docker $(docker --version | awk '{print $3}' | tr -d ',')${NC}"

# ── 2. Configurar .env ─────────────────────────────────────────────────────
echo -e "${BLUE}[2/5]${NC} Configurando entorno..."

if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${YELLOW}⚠  .env creado desde .env.example — revisa las variables antes de producción${NC}"
else
  echo -e "${GREEN}✓ .env ya existe${NC}"
fi

# ── 3. Construir y levantar contenedores ───────────────────────────────────
echo -e "${BLUE}[3/5]${NC} Construyendo y levantando servicios..."
echo ""

docker compose up --build -d

echo ""
echo -e "${BLUE}[4/5]${NC} Esperando que los servicios estén listos..."

# Esperar al backend
RETRIES=20
until curl -sf http://localhost:8000/health >/dev/null 2>&1; do
  RETRIES=$((RETRIES-1))
  if [ $RETRIES -eq 0 ]; then
    echo -e "${RED}✗ El backend no respondió. Ver logs con: docker compose logs backend${NC}"
    exit 1
  fi
  echo -n "."
  sleep 3
done
echo ""
echo -e "${GREEN}✓ Backend listo${NC}"

# ── 5. Migraciones y seed ──────────────────────────────────────────────────
echo -e "${BLUE}[5/5]${NC} Aplicando migraciones..."

docker compose exec -T backend alembic upgrade head
echo -e "${GREEN}✓ Migraciones aplicadas${NC}"

read -p "¿Cargar datos de demo? (módulo de investigación + usuarios de prueba) [s/N]: " LOAD_SEED
if [[ "$LOAD_SEED" =~ ^[Ss]$ ]]; then
  docker compose exec -T backend python scripts/seed.py
fi

# ── Resumen final ──────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅  LearnPath está corriendo${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  🌐  Frontend:    ${BLUE}http://localhost:3000${NC}"
echo -e "  🔌  API (docs):  ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  🗄️   Adminer:     ${BLUE}http://localhost:8080${NC}"
echo ""
echo -e "  Credenciales demo:"
echo -e "  Estudiante:   demo@learnpath.dev / demo1234"
echo -e "  Instructor:   instructor@learnpath.dev / demo1234"
echo ""
echo -e "  Para ver logs en tiempo real:"
echo -e "  ${YELLOW}docker compose logs -f${NC}"
echo ""
echo -e "  Para detener:"
echo -e "  ${YELLOW}docker compose down${NC}"
echo ""
