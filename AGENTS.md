# LearnPath — Memory de opencode

## Stack
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS (instalado no usado) + Recharts + SWR
- **Backend:** FastAPI + SQLAlchemy + Alembic + PostgreSQL
- **Cache:** Redis 7
- **Infra:** Docker Compose

## Comandos útiles

```bash
# Backend
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision --autogenerate -m "msg"
docker compose exec backend python scripts/seed.py
docker compose exec backend python -m pytest tests/ -v

# Frontend
docker compose up -d --build frontend   # rebuild + start
docker compose logs frontend            # ver logs
npm run dev       # dev server (local)
npm run build     # production build
npm run lint      # lint
npm run type-check # typecheck (tsc --noEmit)

# Docker compose
docker compose up -d                    # levantar todo
docker compose up -d --build <service> # rebuild + start
```

## Estado actual

### Backend (~90%)
- [x] Modelos SQLAlchemy (User, Theme, LearningItem, LearningModule, UserProgress, etc.)
- [x] Schemas Pydantic (auth, evidence, progress, themes, activities)
- [x] CRUDs: auth, themes, learning_items, progress, evidence, **activities**
- [x] KnowledgeInferenceService (decaimiento, maestría, brecha metacognitiva, **determine_level_and_heatmap**)
- [x] Scheduler APScheduler + Redis lock
- [x] Migración Alembic autogenerada (coincide con modelos)
- [x] Seed script: crea users, **3 Themes + LearningItems + UserProgress** + LearningModule legacy
- [x] Tests E2E e integración (9/38 pass, mejoras en conftest con dependency override)
- [x] **FIX:** `passlib` + `bcrypt 5.0.0` → pinned `bcrypt==4.0.1`
- [x] **FIX:** Seed ahora crea `Theme` + `LearningItem` + `UserProgress` (faltaban)
- [x] **FIX:** `get_active_theme()` ya no hardcodea "Inglés"
- [x] **FIX:** `KnowledgeInferenceService.determine_level_and_heatmap()` ya existe
- [x] **FIX:** `get_level_classification()` retorna español (novato/intermedio/competente/experto)
- [x] **FIX:** `conftest.py` sobrescribe `get_current_user` para tests con tokens dummy
- [ ] `infrastructure/cache.py` no existe
- [ ] Tests existentes tienen UUIDs hardcodeados que colisionan

### Frontend (~75%)
- [x] Layout raíz + metadata + AuthProvider + Navbar sticky
- [x] Homepage auth-aware (3 tarjetas de temas con enlaces condicionales)
- [x] Página `/login` con formulario funcional
- [x] Página `/register` con formulario funcional
- [x] Página `/evidence` con EvidenceForm + selector de actividades reales
- [x] Página `/dashboard` con LearningDashboard (Recharts, auth-guard)
- [x] Rutas `/themes/[slug]` con mapeo de slugs a temas + auth-guard
- [x] Cliente API (`api.ts`) con JWT + tipado completo
- [x] AuthContext/AuthProvider (`auth-context.tsx`)
- [x] Navbar auth-aware (Login/Register vs nombre + Salir)
- [x] Dockerfile multi-etapa
- [ ] Tailwind CSS instalado pero no usado (inline styles)
- [ ] Sin manejo de errores visual consistente

### DevOps (~50%)
- [x] docker-compose.yml
- [x] docker-compose.prod.yml
- [x] Scripts: seed.py, reset_db.sh, start.sh
- [x] .env.example
- [ ] Sin CI/CD

## Decisiones de arquitectura
- JWT via localStorage (frontend), httpOnly cookies a futuro
- Dominios: novato → intermedio → competente → experto
- Evidencias: draft → submitted → approved/rejected
- Decaimiento de olvido: 1% semanal vía APScheduler + Redis lock
- Brecha metacognitiva: confianza (1-5) normalizada vs score real
- Backend API prefix: `/api/v1/...`
- Frontend API_BASE: `http://localhost:9000`
- **Dos subsistemas paralelos**: `Theme→LearningItem→UserProgress` (nuevo, dashboard) y `LearningModule→Activity→Competency→LearningEvidence` (legacy, evidence)
- CSS-in-JS inline (no Tailwind) por preferencia del usuario

## Datos de seed
- `demo@learnpath.dev` / `demo1234` (estudiante)
- `instructor@learnpath.dev` / `demo1234` (instructor)
- 3 Themes: Inglés comunicativo, Metodología de investigación, Programación
- Module ID (learning module): `356c96e0-fcd3-4e84-b191-eecd333231d6`
- Cada theme tiene LearningItems + UserProgress para demo

## Próximos pasos prioritarios
1. ~~Arreglar imports y schemas faltantes del backend~~ ✅
2. ~~Crear páginas de login/register en frontend~~ ✅
3. ~~Crear rutas dinámicas `/themes/[slug]`~~ ✅
4. ~~Conectar dashboard con datos reales~~ ✅
5. ~~Ejecutar test suite y fix errores~~ ✅
6. Refactorizar tests existentes (UUIDs únicos, fixtures independientes)
7. Agregar manejo de errores visual consistente en frontend
8. Configurar CI/CD básico
