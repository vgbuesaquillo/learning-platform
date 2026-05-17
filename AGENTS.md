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
- [x] Seed script: crea users, **4 Themes + LearningItems + UserProgress** + LearningModule legacy
- [x] Tests E2E e integración (38/38 pass)
- [x] **Nuevo endpoint** `POST /api/v1/learning-items/{id}/view`: auto-registra vista + mastery
- [x] **Nuevo endpoint** `GET /api/v1/progress/themes`: progreso multi-tema para homepage
- [x] **FIX:** `passlib` + `bcrypt 5.0.0` → pinned `bcrypt==4.0.1`
- [x] **FIX:** Seed ahora crea `Theme` + `LearningItem` + `UserProgress` (faltaban)
- [x] **FIX:** `get_active_theme()` ya no hardcodea "Inglés"
- [x] **FIX:** `KnowledgeInferenceService.determine_level_and_heatmap()` ya existe
- [x] **FIX:** `get_level_classification()` retorna español (novato/intermedio/competente/experto)
- [x] **FIX:** `conftest.py` sobrescribe `get_current_user` para tests con tokens dummy
- [ ] `infrastructure/cache.py` no existe

### Frontend (~85%)
- [x] Layout raíz + metadata + AuthProvider + Navbar sticky
- [x] Homepage auth-aware con progreso real (4 tarjetas con barra, nivel, items)
- [x] Página `/login` con formulario funcional
- [x] Página `/register` con formulario funcional
- [x] Página `/evidence` con EvidenceForm (visible solo instructores)
- [x] Página `/dashboard` con LearningDashboard (Recharts, auth-guard)
- [x] **Nueva página** `/learn/[slug]` con flujo secuencial de aprendizaje
- [x] Cliente API (`api.ts`) con JWT + tipado completo
- [x] AuthContext/AuthProvider (`auth-context.tsx`)
- [x] Navbar auth-aware con links condicionales (Evidencia solo si instructor)
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
6. ~~Rediseñar flujo de auto-aprendizaje (login → ejes → contenido progresivo)~~ ✅
7. Agregar manejo de errores visual consistente en frontend
8. Configurar CI/CD básico

## Cambios recientes (15-May-2026)
### Backend
- **Nuevo endpoint `POST /api/v1/learning-items/{item_id}/view`**: auto-registra vista de item, actualiza mastery vía `KnowledgeInferenceService`, crea `UserInteraction`. Retorna `interaction_id`, `mastery_level`, `level`.
- **Nuevo endpoint `GET /api/v1/progress/themes`**: retorna resumen de progreso por tema para la homepage (mastery, nivel, items completados/total, por usuario autenticado).
- **Schema `ThemeProgressSummary` y `ThemesProgressResponse`**: estructura de respuesta para progreso multi-tema.
- **Schema `RecordInteractionResponse` mejorado**: ahora incluye `mastery_level` y `level` además de `interaction_id`.
- **4to tema en seed.py**: "Deportes y salud" con 7 LearningItems (nutrición, entrenamiento, anatomía, fisiología, planificación).

### Frontend
- **Homepage (`page.tsx`) rediseñada**: cuando el usuario está autenticado, fetchea `GET /progress/themes` y muestra cada tema como tarjeta con barra de progreso, badge de nivel (novato/intermedio/competente/experto con colores), contador de items y porcentaje. Sin autenticar, muestra lista estática de 4 temas con links a /login.
- **Nueva página `/learn/[slug]`**: flujo de aprendizaje secuencial. Muestra items uno por uno. Botón "✓ Lo sé" que llama `POST /items/{id}/view` y avanza al siguiente. Barra de progreso. Pantalla final "¡Completaste!" con opciones de repaso o volver.
- **Mapa slug-nombre**: `english`→Inglés comunicativo, `research`→Metodología de investigación, `programming`→Programación, `sports`→Deportes y salud.
- **Navbar simplificada**: link "Evidencia" oculto para estudiantes (visible solo para instructores). Link "Dashboard" visible para todos los autenticados.

### Endpoints verificados funcionales
- `POST /api/v1/auth/login` → token JWT
- `GET /api/v1/progress/themes` → 4 themes con progreso
- `POST /api/v1/learning-items/{id}/view` → mastery actualizado
- `GET /api/v1/learning-items/` → lista de items
- `GET /api/v1/themes/` → lista de temas
