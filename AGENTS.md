# LearnPath — Memory de opencode

## Stack
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS (instalado no usado)
- **Backend:** FastAPI + SQLAlchemy + Alembic + PostgreSQL
- **Cache:** Redis 7
- **Infra:** Docker Compose

## Comandos útiles

```bash
# Backend
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision --autogenerate -m "msg"
docker compose exec backend python scripts/seed.py
docker compose exec backend python -m pytest

# Frontend
npm run dev       # dev server
npm run build     # production build
npm run lint      # lint
npm run type-check # typecheck (tsc --noEmit)
```

## Estado actual

### Backend (~80%)
- [x] Modelos SQLAlchemy (User, Theme, LearningItem, UserProgress, etc.)
- [x] Schemas Pydantic
- [x] CRUDs: auth, themes, learning_items, progress, evidence
- [x] KnowledgeInferenceService (decaimiento, maestría, brecha metacognitiva)
- [x] ProgressCalculator (consistencia, nivel de dominio)
- [x] Scheduler APScheduler + Redis lock
- [x] Migración inicial Alembic
- [x] Seed script
- [x] Tests E2E e integración
- [ ] **BUG:** Import paths rotos: `main.py` → `app.api.v1.auth` (debe ser `app.api.auth`), `progress.py` → `app.core.knowledge_inference_service` (debe ser `app.domain.services`)
- [ ] **BUG:** Schemas faltantes: UserRegister, UserLogin, TokenResponse, UserOut, EvidenceCreate, EvidenceReview, EvidenceOut, LearningDashboard
- [ ] **BUG:** `learning_items.py` usa `item.metadata` en vez de `item.item_metadata`
- [ ] **FALTANTE:** `infrastructure/cache.py` no existe
- [ ] Tests con tokens dummy que no funcionan

### Frontend (~30%)
- [x] Layout raíz + metadata
- [x] Homepage con 3 temas
- [x] Página `/evidence` con EvidenceForm
- [x] Página `/dashboard` con LearningDashboard (Recharts)
- [x] Cliente API (api.ts) con JWT
- [x] Dockerfile multi-etapa
- [ ] FALTAN páginas de auth (login/register)
- [ ] Rutas `/themes/*` no existen
- [ ] `DEMO_MODULE_ID` vacío en dashboard
- [ ] Sin contexto/auth provider
- [ ] Sin estado global
- [ ] Tailwind CSS instalado pero no usado (inline styles)
- [ ] Sin manejo de errores visual consistente

### DevOps (~50%)
- [x] docker-compose.yml
- [x] docker-compose.prod.yml
- [x] Scripts: seed.py, reset_db.sh, start.sh
- [x] .env.example
- [ ] Sin CI/CD

## Decisiones de arquitectura
- JWT via httpOnly cookies → localStorage (frontend actual usa localStorage)
- Dominios: novato → intermedio → competente → experto
- Evidencias: draft → submitted → approved/rejected
- Decaimiento de olvido: 1% semanal vía APScheduler + Redis lock
- Brecha metacognitiva: confianza (1-5) normalizada vs score real

## Próximos pasos prioritarios
1. Arreglar imports y schemas faltantes del backend
2. Crear páginas de login/register en frontend
3. Crear rutas dinámicas `/themes/[slug]`
4. Conectar dashboard con datos reales
5. Ejecutar test suite y fix errores
