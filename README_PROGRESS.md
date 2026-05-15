# LearnPath — Progreso del Proyecto

> Plataforma educativa que mide **aprendizaje real** (comprensión, aplicación, metacognición).

## Leyenda
- ✅ Completado
- 🔧 En progreso
- ⬜ Pendiente
- ❌ Con bugs

---

## Backend (FastAPI/Python) — ~90%

### Modelos y Base de Datos
- ✅ Modelos SQLAlchemy (User, Theme, LearningItem, UserProgress, LearningModule, Activity, Competency, etc.)
- ✅ Migración Alembic autogenerada (coincide con modelos)
- ✅ Seed crea 3 Themes + LearningItems + UserProgress para demo
- ✅ **FIX:** DomainLevel español, Competency.module_id, etc.

### API Endpoints
- ✅ Auth: register, login, me
- ✅ Themes CRUD
- ✅ Learning Items CRUD
- ✅ Progress dashboard (usa active theme)
- ✅ Evidence: create, submit, review
- ✅ **Activities:** `/api/v1/activities/module/{module_id}` (nuevo)
- ✅ **FIX:** `get_active_theme()` sin hardcodeo de "Inglés"

### Schemas
- ✅ Theme, LearningItem, UserInteraction, UserProgress, Activity, etc.
- ✅ UserRegister, UserLogin, TokenResponse, UserOut, EvidenceCreate, EvidenceReview, EvidenceOut, LearningDashboard, CompetencyProgress

### Servicios de Dominio
- ✅ `KnowledgeInferenceService` — decaimiento, maestría, brecha metacognitiva, **determine_level_and_heatmap**
- ✅ **FIX:** `get_level_classification()` retorna español (`novato`/`intermedio`/`competente`/`experto`)
- ⬜ Integrar NLP real (actualmente keyword matching placeholder)

### Infraestructura
- ✅ Database (SQLAlchemy + PostgreSQL)
- ⬜ `infrastructure/cache.py` — no implementado
- ✅ Scheduler (APScheduler + Redis lock para decaimiento semanal)
- ✅ **FIX:** bcrypt 4.0.1 pinned (passlib incompatible con bcrypt 5.x)

### Tests
- ✅ E2E: auth flow, evidence flow, RBAC (9/38 pass, mejorado de 6)
- ✅ Integration: RBAC
- ✅ **FIX:** `conftest.py` sobrescribe `get_current_user` para tokens dummy
- ❌ Tests existentes tienen UUIDs hardcodeados que colisionan

---

## Frontend (Next.js 14/TypeScript) — ~75%

### Páginas
- ✅ Homepage `/` auth-aware (3 tarjetas, enlaces condicionales)
- ✅ `/login` — formulario funcional
- ✅ `/register` — formulario funcional
- ✅ `/evidence` — EvidenceForm + selector dinámico de actividades
- ✅ `/dashboard` — LearningDashboard (Recharts, auth-guard)
- ✅ `/themes/[slug]` — rutas dinámicas con auth-guard

### Componentes
- ✅ `EvidenceForm` — contenido, reflexión metacognitiva, nivel de confianza
- ✅ `LearningDashboard` — radar chart, evolución temporal, métricas, brecha metacognitiva
- ✅ `Navbar` — sticky con auth-aware (Login/Register vs nombre + Salir)
- ✅ AuthContext/AuthProvider

### API Client
- ✅ Cliente HTTP con JWT via localStorage
- ✅ Tipos TypeScript compartidos
- ⬜ Manejo de errores visual consistente

### Estado y Estilos
- ✅ AuthContext/AuthProvider
- ⬜ Sin estado global adicional
- ⬜ Tailwind CSS instalado pero no usado (inline styles)

---

## DevOps — ~50%

### Docker
- ✅ `docker-compose.yml` con todos los servicios
- ✅ `docker-compose.prod.yml`
- ✅ Dockerfiles multi-etapa (frontend + backend)
- ✅ Frontend con hot-reload vía volumen montado

### Scripts
- ✅ `seed.py` — datos demo (3 themes + learning module legacy)
- ✅ `reset_db.sh` — reinicio de BD
- ✅ `start.sh` — inicio rápido

### CI/CD
- ⬜ Sin pipeline configurado

---

## Issues Conocidos

| ID | Severidad | Descripción | Archivos |
|----|-----------|-------------|----------|
| B5 | 🟡 Media | `infrastructure/cache.py` no existe | — |
| B6 | 🟡 Media | Tests con UUIDs hardcodeados que colisionan | `backend/tests/` |
| F4 | 🟡 Baja | Manejo de errores visual inconsistente | `frontend/src/` |

---

## Próximos Pasos Recomendados

1. ~~Backend — imports, schemas, bcrypt, seed, dashboard~~ ✅
2. ~~Frontend — auth pages, theme routes, navbar, dashboard conectado~~ ✅
3. **Refactorizar tests** — UUIDs únicos, fixtures independientes
4. **Manejo de errores visual** consistente en frontend
5. **Configurar CI/CD** básico
