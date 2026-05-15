# LearnPath — Progreso del Proyecto

> Plataforma educativa que mide **aprendizaje real** (comprensión, aplicación, metacognición).

## Leyenda
- ✅ Completado
- 🔧 En progreso
- ⬜ Pendiente
- ❌ Con bugs

---

## Backend (FastAPI/Python) — ~80%

### Modelos y Base de Datos
- ✅ Modelos SQLAlchemy (User, Theme, LearningItem, UserProgress, UserInteraction, LearningModule, Activity, LearningEvidence, Competency, Enrollment)
- ✅ Migración inicial Alembic
- ✅ Seed script con datos demo
- ⬜ Migrationes adicionales según nuevos features

### API Endpoints
- ✅ Auth: register, login, me
- ✅ Themes CRUD
- ✅ Learning Items CRUD
- ✅ Progress dashboard
- ✅ Evidence: create, submit, review
- ❌ **Import paths rotos** — `main.py` referencia `app.api.v1.auth` inexistente

### Schemas
- ✅ Theme, LearningItem, UserInteraction, UserProgress
- ❌ **Faltan:** UserRegister, UserLogin, TokenResponse, UserOut, EvidenceCreate, EvidenceReview, EvidenceOut, LearningDashboard

### Servicios de Dominio
- ✅ `KnowledgeInferenceService` — decaimiento de olvido, clasificación de maestría, brecha metacognitiva
- ✅ `ProgressCalculator` — consistencia, nivel de dominio, brecha metacognitiva
- ⬜ Integrar NLP real (actualmente keyword matching placeholder)

### Infraestructura
- ✅ Database (SQLAlchemy + PostgreSQL)
- ⬜ `infrastructure/cache.py` — no implementado
- ✅ Scheduler (APScheduler + Redis lock para decaimiento semanal)

### Tests
- ✅ E2E: auth flow, evidence flow, RBAC
- ✅ Integration: RBAC
- ❌ Tests con tokens dummy que no validan auth real

---

## Frontend (Next.js 14/TypeScript) — ~30%

### Páginas
- ✅ Homepage `/` con lista de temas
- ✅ `/evidence` — formulario de registro de evidencia
- ✅ `/dashboard` — dashboard de aprendizaje (con setup guide por ahora)
- ⬜ **Login/Register** — no existen páginas de auth
- ⬜ **Rutas `/themes/[slug]`** — no existen

### Componentes
- ✅ `EvidenceForm` — contenido, reflexión metacognitiva, nivel de confianza
- ✅ `LearningDashboard` — radar chart, evolución temporal, métricas, brecha metacognitiva
- ⬜ Auth components (login form, register form)
- ⬜ Theme detail components

### API Client
- ✅ Cliente HTTP con JWT via localStorage
- ✅ Tipos TypeScript compartidos
- ⬜ Manejo de errores visual consistente

### Estado y Estilos
- ⬜ Sin contexto de auth/provider
- ⬜ Sin estado global
- ⬜ Tailwind CSS instalado pero no usado (inline styles actualmente)

---

## DevOps — ~50%

### Docker
- ✅ `docker-compose.yml` con todos los servicios
- ✅ `docker-compose.prod.yml`
- ✅ Dockerfiles multi-etapa (frontend + backend)

### Scripts
- ✅ `seed.py` — datos demo
- ✅ `reset_db.sh` — reinicio de BD
- ✅ `start.sh` — inicio rápido

### CI/CD
- ⬜ Sin pipeline configurado

---

## Issues Conocidos

| ID | Severidad | Descripción | Archivos |
|----|-----------|-------------|----------|
| B1 | 🔴 Alta | Import path `app.api.v1.auth` no existe | `backend/app/main.py` |
| B2 | 🔴 Alta | Schemas faltantes UserRegister, UserLogin, etc. | `backend/app/api/auth.py` |
| B3 | 🔴 Alta | Import path `app.core.knowledge_inference_service` incorrecto | `backend/app/api/progress.py` |
| B4 | 🟡 Media | `item.metadata` vs `item.item_metadata` | `backend/app/api/learning_items.py` |
| B5 | 🟡 Media | `infrastructure/cache.py` no existe | — |
| B6 | 🟡 Media | Tests con tokens dummy | `backend/tests/conftest.py` |
| F1 | 🔴 Alta | Sin páginas de login/register | `frontend/src/app/` |
| F2 | 🔴 Alta | `DEMO_MODULE_ID` vacío | `frontend/src/app/dashboard/page.tsx` |
| F3 | 🟡 Media | Rutas `/themes/*` no existen | `frontend/src/app/` |

---

## Próximos Pasos Recomendados

1. **Arreglar backend** — imports, schemas faltantes, bugs
2. **Completar frontend** — auth pages, theme routes, conectar dashboard
3. **Ejecutar tests** y corregir errores
4. **Configurar CI/CD** básico
