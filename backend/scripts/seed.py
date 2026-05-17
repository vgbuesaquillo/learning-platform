"""
Seed inicial: Crea themes, learning items, módulo de investigación y progreso demo.
Ejecutar con: docker compose exec backend python scripts/seed.py
"""
import sys
import os
sys.path.insert(0, "/app")

from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.infrastructure.database import SessionLocal
from app.domain.models import (
    LearningModule, Theme, LearningItem, UserProgress,
    Competency, Activity, ActivityCompetency, User, EvidenceType
)
from app.core.security import hash_password


def seed():
    db = SessionLocal()
    try:
        # ── Usuarios demo ────────────────────────────────────────────────
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

        user = db.query(User).filter(User.email == "demo@learnpath.dev").first()

        # ── Themes ──────────────────────────────────────────────────────
        themes_data = [
            {"name": "Inglés comunicativo", "description": "Vocabulario, gramática y frases para comunicación diaria en inglés.", "order": 1},
            {"name": "Metodología de investigación", "description": "Diseño, ejecución y comunicación de investigación científica.", "order": 2},
            {"name": "Programación", "description": "Fundamentos de lógica, estructuras de datos y algoritmos.", "order": 3},
            {"name": "Deportes y salud", "description": "Nutrición, entrenamiento, anatomía básica y hábitos saludables.", "order": 4},
        ]
        themes_created = 0
        for td in themes_data:
            theme = db.query(Theme).filter(Theme.name == td["name"]).first()
            if not theme:
                theme = Theme(name=td["name"], description=td["description"], order=td["order"])
                db.add(theme)
                db.flush()
                themes_created += 1
            # Crear learning items si no existen
            items = db.query(LearningItem).filter(LearningItem.theme_id == theme.id).count()
            if items == 0:
                demo_items = _items_for_theme(theme.name)
                for item_data in demo_items:
                    li = LearningItem(theme_id=theme.id, **item_data)
                    db.add(li)
                db.flush()
                # Crear progreso demo para cada item
                all_items = db.query(LearningItem).filter(LearningItem.theme_id == theme.id).all()
                for idx, li in enumerate(all_items):
                    existing_progress = db.query(UserProgress).filter(
                        UserProgress.user_id == user.id,
                        UserProgress.learning_item_id == li.id
                    ).first()
                    if not existing_progress:
                        p = UserProgress(
                            user_id=user.id,
                            theme_id=theme.id,
                            learning_item_id=li.id,
                            mastery_level=max(0.1, 1.0 - idx * 0.15),
                            recurrence_score=idx,
                            last_practiced_at=datetime.now(timezone.utc) - timedelta(days=idx * 3),
                            history=[
                                {
                                    "type": "interaction",
                                    "mastery_level_before": max(0.0, 1.0 - idx * 0.15 - 0.1),
                                    "mastery_level_after": max(0.1, 1.0 - idx * 0.15),
                                    "timestamp": (datetime.now(timezone.utc) - timedelta(days=idx * 3 + 1)).isoformat(),
                                }
                            ],
                        )
                        db.add(p)
                print(f"  → {len(all_items)} ítems + progreso para '{theme.name}'")
        print(f"✓ {themes_created} themes creados")

        # ── Módulo de aprendizaje (legacy: research) ────────────────────
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
                {"name": "Revisión y síntesis bibliográfica", "description": "Capacidad de buscar, evaluar y sintetizar literatura científica", "weight": 1.5, "level_indicators": {"novato": ["Identifica fuentes primarias y secundarias"], "intermedio": ["Usa gestores bibliográficos", "Evalúa calidad de fuentes"], "competente": ["Construye estado del arte coherente", "Detecta brechas en la literatura"], "experto": ["Sintetiza críticamente múltiples perspectivas", "Propone agenda de investigación"]}},
                {"name": "Diseño metodológico", "description": "Diseño de estrategias y métodos de investigación adecuados", "weight": 2.0, "level_indicators": {"novato": ["Distingue enfoques cuali/cuantitativos"], "intermedio": ["Diseña instrumentos básicos", "Selecciona diseño adecuado"], "competente": ["Diseña estudios robustos", "Anticipa sesgos y limitaciones"], "experto": ["Diseña estudios mixtos complejos", "Valida instrumentos"]}},
                {"name": "Análisis e interpretación de datos", "description": "Procesar y extraer significado de datos cuali/cuantitativos", "weight": 2.0, "level_indicators": {"novato": ["Aplica estadísticas descriptivas básicas"], "intermedio": ["Usa software estadístico", "Codifica datos cualitativos"], "competente": ["Aplica análisis multivariado", "Triangula fuentes"], "experto": ["Modelos estadísticos avanzados", "Teoría emergente"]}},
                {"name": "Escritura científica", "description": "Comunicar hallazgos con rigor y claridad académica", "weight": 1.5, "level_indicators": {"novato": ["Estructura IMRD básica"], "intermedio": ["Argumenta con evidencia", "Maneja citas correctamente"], "competente": ["Redacta artículo completo", "Responde a revisores"], "experto": ["Publica en revistas Q1-Q2", "Revisa artículos de pares"]}},
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
                {"title": "Mapa de literatura: estado del arte inicial", "description": "Construye un mapa visual de la literatura existente sobre tu tema", "instructions": "1. Busca 20+ artículos en Scopus/WoS sobre tu tema\n2. Clasifícalos por metodología y hallazgos\n3. Identifica brechas y debates abiertos\n4. Escribe una síntesis de 500 palabras\n5. Reflexiona: ¿Qué te sorprendió? ¿Qué aún no entiendes?", "evidence_type": EvidenceType.ACTIVIDAD.value, "rubric": {"cobertura_bibliografica": {"descripcion": "Amplitud y calidad de fuentes consultadas", "niveles": {"novato": {"criterio": "< 10 fuentes relevantes", "peso": 1}, "intermedio": {"criterio": "10-19 fuentes, mezcla de calidades", "peso": 2}, "competente": {"criterio": "20+ fuentes, mayoría Q1-Q2", "peso": 3}, "experto": {"criterio": "20+ fuentes, todas indexadas, cobertura temporal amplia", "peso": 4}}}, "sintesis_critica": {"descripcion": "Capacidad de integrar y analizar críticamente la literatura", "niveles": {"novato": {"criterio": "Descripción superficial", "peso": 1}, "intermedio": {"criterio": "Resumen sin análisis propio", "peso": 2}, "competente": {"criterio": "Análisis con posición argumentada", "peso": 3}, "experto": {"criterio": "Síntesis crítica que identifica brechas y propone dirección", "peso": 4}}}}, "max_score": 100.0, "order_index": 1, "competency_idx": 0},
                {"title": "Diseño del protocolo de investigación", "description": "Elabora el diseño metodológico completo de tu investigación", "instructions": "1. Define tu pregunta de investigación (PICO/PEO)\n2. Justifica el enfoque metodológico elegido\n3. Describe muestra/participantes y criterios\n4. Diseña o adapta instrumentos\n5. Describe el plan de análisis\n6. Reflexión: ¿Cuáles son las limitaciones de tu diseño?", "evidence_type": EvidenceType.PROYECTO.value, "rubric": {"pregunta_investigacion": {"descripcion": "Claridad y pertinencia de la pregunta", "niveles": {"novato": {"criterio": "Vaga, sin marco claro", "peso": 1}, "experto": {"criterio": "SMART, respaldada en literatura, viable", "peso": 4}}}, "coherencia_metodologica": {"descripcion": "Alineación entre pregunta, método y análisis", "niveles": {"novato": {"criterio": "Sin coherencia aparente", "peso": 1}, "experto": {"criterio": "Coherencia total con justificación epistemológica", "peso": 4}}}}, "max_score": 100.0, "order_index": 2, "competency_idx": 1},
                {"title": "Autoevaluación metacognitiva del proceso", "description": "Reflexiona sobre tu propio proceso de aprendizaje en investigación", "instructions": "Responde estas preguntas con profundidad y honestidad:\n1. ¿Qué conceptos dominás bien? ¿Cómo lo sabés?\n2. ¿Qué todavía te genera confusión o inseguridad?\n3. ¿Cómo ha cambiado tu comprensión de la investigación?\n4. ¿Qué estrategias de aprendizaje te han funcionado mejor?\n5. ¿Qué harías diferente si empezaras de nuevo?", "evidence_type": EvidenceType.AUTOEVALUACION.value, "rubric": {"profundidad_reflexion": {"descripcion": "Nivel de análisis metacognitivo", "niveles": {"novato": {"criterio": "Descripción superficial sin análisis", "peso": 1}, "experto": {"criterio": "Análisis profundo con planes de mejora concretos", "peso": 4}}}}, "max_score": 100.0, "order_index": 3, "competency_idx": 0},
            ]
            for ad in activities_data:
                comp_idx = ad.pop("competency_idx")
                activity = Activity(module_id=module.id, **ad)
                db.add(activity)
                db.flush()
                ac = ActivityCompetency(activity_id=activity.id, competency_id=comps[comp_idx].id, contribution_weight=1.0)
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


def _items_for_theme(theme_name: str) -> list:
    items_map = {
        "Inglés comunicativo": [
            {"item_type": "vocabulary", "content": "Hello / Goodbye", "item_metadata": {"difficulty": 1, "category": "greetings"}},
            {"item_type": "vocabulary", "content": "Please / Thank you", "item_metadata": {"difficulty": 1, "category": "politeness"}},
            {"item_type": "vocabulary", "content": "Yes / No / Maybe", "item_metadata": {"difficulty": 1, "category": "basics"}},
            {"item_type": "phrase", "content": "How are you?", "item_metadata": {"difficulty": 1, "category": "greetings"}},
            {"item_type": "phrase", "content": "I don't understand", "item_metadata": {"difficulty": 2, "category": "expressions"}},
            {"item_type": "grammar_rule", "content": "Simple Present: I/You/We/They + verb", "item_metadata": {"difficulty": 2, "category": "grammar"}},
            {"item_type": "grammar_rule", "content": "Present Continuous: to be + verb-ing", "item_metadata": {"difficulty": 2, "category": "grammar"}},
            {"item_type": "idiom", "content": "Break the ice", "item_metadata": {"difficulty": 3, "category": "idioms"}},
            {"item_type": "idiom", "content": "Piece of cake", "item_metadata": {"difficulty": 3, "category": "idioms"}},
        ],
        "Metodología de investigación": [
            {"item_type": "concept", "content": "Estado del arte", "item_metadata": {"difficulty": 2, "category": "methodology"}},
            {"item_type": "concept", "content": "Pregunta de investigación (PICO/PEO)", "item_metadata": {"difficulty": 2, "category": "design"}},
            {"item_type": "concept", "content": "Triangulación metodológica", "item_metadata": {"difficulty": 3, "category": "analysis"}},
            {"item_type": "method", "content": "Scoping Review", "item_metadata": {"difficulty": 3, "category": "literature_review"}},
            {"item_type": "method", "content": "Análisis temático", "item_metadata": {"difficulty": 3, "category": "qualitative"}},
            {"item_type": "method", "content": "Estadística inferencial (t-test, ANOVA)", "item_metadata": {"difficulty": 4, "category": "quantitative"}},
            {"item_type": "principle", "content": "Ética en investigación: consentimiento informado", "item_metadata": {"difficulty": 2, "category": "ethics"}},
        ],
        "Programación": [
            {"item_type": "concept", "content": "Variables y tipos de datos", "item_metadata": {"difficulty": 1, "category": "basics"}},
            {"item_type": "concept", "content": "Estructuras condicionales (if/else)", "item_metadata": {"difficulty": 1, "category": "control_flow"}},
            {"item_type": "concept", "content": "Bucles (for/while)", "item_metadata": {"difficulty": 2, "category": "control_flow"}},
            {"item_type": "concept", "content": "Funciones y scope", "item_metadata": {"difficulty": 2, "category": "functions"}},
            {"item_type": "concept", "content": "Estructuras de datos: listas, dicts, sets", "item_metadata": {"difficulty": 2, "category": "data_structures"}},
            {"item_type": "method", "content": "Recursión", "item_metadata": {"difficulty": 3, "category": "algorithms"}},
            {"item_type": "method", "content": "Algoritmos de búsqueda y ordenamiento", "item_metadata": {"difficulty": 3, "category": "algorithms"}},
        ],
        "Deportes y salud": [
            {"item_type": "concept", "content": "Macronutrientes: proteínas, carbohidratos, grasas", "item_metadata": {"difficulty": 1, "category": "nutrition"}},
            {"item_type": "concept", "content": "Principios del entrenamiento: sobrecarga progresiva", "item_metadata": {"difficulty": 1, "category": "training"}},
            {"item_type": "concept", "content": "Anatomía básica: grupos musculares principales", "item_metadata": {"difficulty": 2, "category": "anatomy"}},
            {"item_type": "concept", "content": "Frecuencia cardíaca y zonas de esfuerzo", "item_metadata": {"difficulty": 2, "category": "physiology"}},
            {"item_type": "method", "content": "Rutina full body vs split", "item_metadata": {"difficulty": 2, "category": "training"}},
            {"item_type": "principle", "content": "Hidratación y electrolitos durante el ejercicio", "item_metadata": {"difficulty": 2, "category": "nutrition"}},
            {"item_type": "method", "content": "Planificación de semana deportiva: descanso activo", "item_metadata": {"difficulty": 3, "category": "planning"}},
        ],
    }
    return items_map.get(theme_name, [])


if __name__ == "__main__":
    seed()
