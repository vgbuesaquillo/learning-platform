"""
Seed inicial: Módulo "Metodología de investigación científica"
Ejecutar con: docker compose exec backend python scripts/seed.py
"""
import sys
import os
sys.path.insert(0, "/app")

from app.infrastructure.database import SessionLocal
from app.domain.models import (
    LearningModule, Competency, Activity,
    ActivityCompetency, User, EvidenceType
)
from app.core.security import hash_password


def seed():
    db = SessionLocal()
    try:
        # Usuario demo
        existing = db.query(User).filter(User.email == "demo@learnpath.dev").first()
        if not existing:
            user = User(
                email="demo@learnpath.dev",
                full_name="Estudiante Demo",
                hashed_password=hash_password("demo1234"),
            )
            instructor = User(
                email="instructor@learnpath.dev",
                full_name="Instructor Demo",
                hashed_password=hash_password("demo1234"),
                is_instructor=True,
            )
            db.add_all([user, instructor])
            db.flush()
            print("✓ Usuarios demo creados")

        # Módulo principal
        module = db.query(LearningModule).filter(
            LearningModule.slug == "metodologia-investigacion"
        ).first()

        if not module:
            module = LearningModule(
                slug="metodologia-investigacion",
                title="Metodología de investigación científica",
                description=(
                    "Desde el estado del arte hasta la publicación "
                    "en revista indexada. Aprende a diseñar, ejecutar y "
                    "comunicar investigación de calidad."
                ),
                topic="Investigación académica",
                estimated_hours=80,
                is_published=True,
            )
            db.add(module)
            db.flush()
            print(f"✓ Módulo creado: {module.title}")

            # Competencias
            competencies_data = [
                {
                    "name": "Revisión y síntesis bibliográfica",
                    "description": "Capacidad de buscar, evaluar y sintetizar literatura científica",
                    "level_indicators": {
                        "novato": ["Identifica fuentes primarias y secundarias"],
                        "intermedio": ["Usa gestores bibliográficos", "Evalúa calidad de fuentes"],
                        "competente": ["Construye estado del arte coherente", "Detecta brechas en la literatura"],
                        "experto": ["Sintetiza críticamente múltiples perspectivas", "Propone agenda de investigación"],
                    },
                    "weight": 1.5,
                },
                {
                    "name": "Diseño metodológico",
                    "description": "Diseño de estrategias y métodos de investigación adecuados",
                    "level_indicators": {
                        "novato": ["Distingue enfoques cuali/cuantitativos"],
                        "intermedio": ["Diseña instrumentos básicos", "Selecciona diseño adecuado"],
                        "competente": ["Diseña estudios robustos", "Anticipa sesgos y limitaciones"],
                        "experto": ["Diseña estudios mixtos complejos", "Valida instrumentos"],
                    },
                    "weight": 2.0,
                },
                {
                    "name": "Análisis e interpretación de datos",
                    "description": "Procesar y extraer significado de datos cuali/cuantitativos",
                    "level_indicators": {
                        "novato": ["Aplica estadísticas descriptivas básicas"],
                        "intermedio": ["Usa software estadístico", "Codifica datos cualitativos"],
                        "competente": ["Aplica análisis multivariado", "Triangula fuentes"],
                        "experto": ["Modelos estadísticos avanzados", "Teoría emergente"],
                    },
                    "weight": 2.0,
                },
                {
                    "name": "Escritura científica",
                    "description": "Comunicar hallazgos con rigor y claridad académica",
                    "level_indicators": {
                        "novato": ["Estructura IMRD básica"],
                        "intermedio": ["Argumenta con evidencia", "Maneja citas correctamente"],
                        "competente": ["Redacta artículo completo", "Responde a revisores"],
                        "experto": ["Publica en revistas Q1-Q2", "Revisa artículos de pares"],
                    },
                    "weight": 1.5,
                },
            ]

            comps = []
            for cd in competencies_data:
                c = Competency(module_id=module.id, **cd)
                db.add(c)
                comps.append(c)
            db.flush()
            print(f"✓ {len(comps)} competencias creadas")

            # Actividades
            activities_data = [
                {
                    "title": "Mapa de literatura: estado del arte inicial",
                    "description": "Construye un mapa visual de la literatura existente sobre tu tema",
                    "instructions": (
                        "1. Busca 20+ artículos en Scopus/WoS sobre tu tema\n"
                        "2. Clasifícalos por metodología y hallazgos\n"
                        "3. Identifica brechas y debates abiertos\n"
                        "4. Escribe una síntesis de 500 palabras\n"
                        "5. Reflexiona: ¿Qué te sorprendió? ¿Qué aún no entiendes?"
                    ),
                    "evidence_type": EvidenceType.ACTIVIDAD,
                    "rubric": {
                        "cobertura_bibliografica": {
                            "descripcion": "Amplitud y calidad de fuentes consultadas",
                            "niveles": {
                                "novato": {"criterio": "< 10 fuentes relevantes", "peso": 1},
                                "intermedio": {"criterio": "10-19 fuentes, mezcla de calidades", "peso": 2},
                                "competente": {"criterio": "20+ fuentes, mayoría Q1-Q2", "peso": 3},
                                "experto": {"criterio": "20+ fuentes, todas indexadas, cobertura temporal amplia", "peso": 4},
                            },
                        },
                        "sintesis_critica": {
                            "descripcion": "Capacidad de integrar y analizar críticamente la literatura",
                            "niveles": {
                                "novato": {"criterio": "Descripción superficial", "peso": 1},
                                "intermedio": {"criterio": "Resumen sin análisis propio", "peso": 2},
                                "competente": {"criterio": "Análisis con posición argumentada", "peso": 3},
                                "experto": {"criterio": "Síntesis crítica que identifica brechas y propone dirección", "peso": 4},
                            },
                        },
                    },
                    "max_score": 100.0,
                    "order_index": 1,
                    "competency_idx": 0,  # Revisión bibliográfica
                },
                {
                    "title": "Diseño del protocolo de investigación",
                    "description": "Elabora el diseño metodológico completo de tu investigación",
                    "instructions": (
                        "1. Define tu pregunta de investigación (PICO/PEO)\n"
                        "2. Justifica el enfoque metodológico elegido\n"
                        "3. Describe muestra/participantes y criterios\n"
                        "4. Diseña o adapta instrumentos\n"
                        "5. Describe el plan de análisis\n"
                        "6. Reflexión: ¿Cuáles son las limitaciones de tu diseño?"
                    ),
                    "evidence_type": EvidenceType.PROYECTO,
                    "rubric": {
                        "pregunta_investigacion": {
                            "descripcion": "Claridad y pertinencia de la pregunta",
                            "niveles": {
                                "novato": {"criterio": "Vaga, sin marco claro", "peso": 1},
                                "experto": {"criterio": "SMART, respaldada en literatura, viable", "peso": 4},
                            },
                        },
                        "coherencia_metodologica": {
                            "descripcion": "Alineación entre pregunta, método y análisis",
                            "niveles": {
                                "novato": {"criterio": "Sin coherencia aparente", "peso": 1},
                                "experto": {"criterio": "Coherencia total con justificación epistemológica", "peso": 4},
                            },
                        },
                    },
                    "max_score": 100.0,
                    "order_index": 2,
                    "competency_idx": 1,  # Diseño metodológico
                },
                {
                    "title": "Autoevaluación metacognitiva del proceso",
                    "description": "Reflexiona sobre tu propio proceso de aprendizaje en investigación",
                    "instructions": (
                        "Responde estas preguntas con profundidad y honestidad:\n"
                        "1. ¿Qué conceptos dominás bien? ¿Cómo lo sabés?\n"
                        "2. ¿Qué todavía te genera confusión o inseguridad?\n"
                        "3. ¿Cómo ha cambiado tu comprensión de la investigación?\n"
                        "4. ¿Qué estrategias de aprendizaje te han funcionado mejor?\n"
                        "5. ¿Qué harías diferente si empezaras de nuevo?"
                    ),
                    "evidence_type": EvidenceType.AUTOEVALUACION,
                    "rubric": {
                        "profundidad_reflexion": {
                            "descripcion": "Nivel de análisis metacognitivo",
                            "niveles": {
                                "novato": {"criterio": "Descripción superficial sin análisis", "peso": 1},
                                "experto": {"criterio": "Análisis profundo con planes de mejora concretos", "peso": 4},
                            },
                        },
                    },
                    "max_score": 100.0,
                    "order_index": 3,
                    "competency_idx": 0,
                },
            ]

            for ad in activities_data:
                comp_idx = ad.pop("competency_idx")
                activity = Activity(module_id=module.id, **ad)
                db.add(activity)
                db.flush()

                # Vincular con competencia
                ac = ActivityCompetency(
                    activity_id=activity.id,
                    competency_id=comps[comp_idx].id,
                    contribution_weight=1.0,
                )
                db.add(ac)

            print(f"✓ {len(activities_data)} actividades creadas")

        db.commit()
        print("\n✅ Seed completado exitosamente")
        print("   Usuario:     demo@learnpath.dev  / demo1234")
        print("   Instructor:  instructor@learnpath.dev  / demo1234")

    except Exception as e:
        db.rollback()
        print(f"❌ Error en seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
