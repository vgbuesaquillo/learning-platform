# LearnPath — Plataforma de Aprendizaje con Progreso Real

Plataforma educativa que mide **aprendizaje real** (comprensión, aplicación, metacognición) en lugar de simples porcentajes de avance.

## Stack tecnológico

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Frontend | Next.js 14 + TypeScript | App Router, RSC, SSR/SSG, ecosistema robusto |
| Backend | FastAPI (Python) | Alto rendimiento, OpenAPI automático, tipado nativo |
| Base de datos | PostgreSQL 15 | Soporte JSONB para rúbricas, full-text search, confiable |
| Cache | Redis 7 | Sesiones, rate limiting, colas de notificaciones |
| Contenedores | Docker + Compose | Paridad dev/prod, reproducibilidad total |
| Auth | JWT + httpOnly cookies | Seguro, stateless, compatible con SSR |

## Inicio rápido

```bash
# 1. Clonar y configurar variables de entorno
cp .env.example .env

# 2. Levantar todo el stack
docker compose up --build

# 3. Aplicar migraciones (primera vez)
docker compose exec backend alembic upgrade head

# 4. Seed de datos de demo (opcional)
docker compose exec backend python scripts/seed.py
```

Accesos:
- **Frontend:** http://localhost:3000
- **API (docs):** http://localhost:8000/docs
- **Adminer (DB):** http://localhost:8080

## Flujo de desarrollo

```
1. docker compose up --build    → levanta servicios con hot-reload
2. editar frontend/src/...      → Next.js recarga automáticamente
3. editar backend/app/...       → Uvicorn recarga automáticamente
4. docker compose logs -f       → ver logs en tiempo real
5. docker compose exec backend alembic revision --autogenerate -m "nombre"
   docker compose exec backend alembic upgrade head   → nueva migración
```

## Estructura del proyecto

```
learnpath/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── frontend/                   # Next.js 14 + TypeScript
│   ├── Dockerfile
│   ├── src/
│   │   ├── app/               # App Router
│   │   │   ├── (auth)/        # Rutas de autenticación
│   │   │   ├── dashboard/     # Dashboard principal
│   │   │   ├── courses/       # Módulos y rutas de aprendizaje
│   │   │   └── api/           # API routes (proxy/BFF)
│   │   ├── components/        # Componentes React
│   │   │   ├── ui/            # Primitivos (Button, Card, etc.)
│   │   │   ├── learning/      # Componentes de dominio educativo
│   │   │   └── dashboard/     # Widgets del dashboard
│   │   ├── lib/               # Utilidades, cliente API, hooks
│   │   └── types/             # Tipos TypeScript compartidos
│   └── package.json
├── backend/                    # FastAPI + Python
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py            # Entry point
│   │   ├── api/               # Routers
│   │   │   ├── auth.py
│   │   │   ├── learning.py
│   │   │   ├── progress.py
│   │   │   └── evidence.py
│   │   ├── domain/            # Modelos de dominio (Clean Architecture)
│   │   │   ├── models.py      # SQLAlchemy models
│   │   │   ├── schemas.py     # Pydantic schemas
│   │   │   └── services/      # Lógica de negocio
│   │   ├── infrastructure/    # Adaptadores externos
│   │   │   ├── database.py
│   │   │   ├── cache.py
│   │   │   └── repositories/
│   │   └── core/              # Config, seguridad, deps
│   │       ├── config.py
│   │       ├── security.py
│   │       └── dependencies.py
│   ├── alembic/               # Migraciones
│   └── requirements.txt
└── scripts/                   # Utilidades DevOps
    ├── seed.py
    └── reset_db.sh
```

## Extender el proyecto

### Agregar un nuevo módulo de aprendizaje
1. Crear registro en `learning_modules` via API o seed
2. Definir competencias en `competencies`
3. Crear actividades en `activities` con rúbricas en JSONB
4. El dashboard calculará métricas automáticamente

### Definir una nueva competencia
```python
# backend/app/domain/services/competency_service.py
competency = Competency(
    name="Diseño metodológico",
    description="...",
    domain_levels=["novato", "intermedio", "competente", "experto"],
    indicators={
        "novato": ["Identifica tipos de investigación"],
        "experto": ["Diseña estudios mixtos complejos"]
    }
)
```

### Nueva métrica de progreso
Implementar `calculate_*` en `ProgressCalculator` y exponer en `/api/progress/metrics`.

## Despliegue en la nube

| Plataforma | Comando / Guía |
|-----------|----------------|
| **Railway** | `railway up` — detecta Dockerfile automáticamente |
| **Render** | Conectar repo, usar `docker-compose.prod.yml` |
| **AWS ECS** | `aws ecs create-cluster` + task definitions desde compose |
| **Vercel** (solo frontend) | `vercel --prod` desde `/frontend` |

## Desarrollo en línea

- **GitHub Codespaces**: abrir repo → "Code" → "Codespaces" → `docker compose up`
- **Gitpod**: prefijo `https://gitpod.io/#` antes de la URL del repo
- **Replit**: importar repo, usar el Replit Nix environment con Docker support
