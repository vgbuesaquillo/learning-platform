import redis
import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
from app.infrastructure.database import SessionLocal
from app.domain.services.knowledge_inference import KnowledgeInferenceService
from app.domain.models import UserProgress
from typing import List
from uuid import UUID


logger = structlog.get_logger()
scheduler = BackgroundScheduler(timezone="UTC")

DECAY_LOCK_KEY = "learnpath:decay_job_lock"

def apply_weekly_forgetting_decay():
    """
    Job principal de decadencia. Protegido por Redis lock para
    garantizar ejecucion unica en entornos multi-replica.
    """
    if not settings.SCHEDULER_ENABLED:
        return

    try:
        r = redis.from_url(settings.REDIS_URL)
        lock_ttl_ms = settings.DECAY_JOB_LOCK_TTL_SECONDS * 1000

        # SET NX PX: atomico, idempotente en multi-pod
        # nx=True: solo establece la clave si no existe
        # px=lock_ttl_ms: establece un tiempo de expiracion en milisegundos
        acquired = r.set(DECAY_LOCK_KEY, "1", nx=True, px=lock_ttl_ms)
        if not acquired:
            logger.info("decay_job_skipped", reason="lock_held_by_another_instance")
            return

        db = SessionLocal()
        processed = 0
        errors = 0
        try:
            logger.info("decay_job_started")
            # Procesar en batches para no saturar la BD
            offset = 0
            while True:
                records = (
                    db.query(UserProgress)
                    .order_by(UserProgress.id)
                    .offset(offset)
                    .limit(settings.DECAY_BATCH_SIZE)
                    .all()
                )
                if not records:
                    break
                svc = KnowledgeInferenceService(db)
                for record in records:
                    try:
                        # Llamar al metodo existente en el servicio de dominio
                        # Se asume que existe y maneja la logica de decay_amount
                        # y actualizacion del historial.
                        svc.apply_forgetting_decay(record)
                        processed += 1
                    except Exception as e:
                        errors += 1
                        logger.error(
                            "decay_record_error",
                            record_id=str(record.id),
                            error=str(e),
                            exc_info=True # Log traceback para debugging
                        )
                db.commit()
                offset += settings.DECAY_BATCH_SIZE

            logger.info("decay_job_finished", processed=processed, errors=errors)
        except Exception as e:
            db.rollback()
            logger.error("decay_job_failed", error=str(e), exc_info=True)
        finally:
            db.close()
            # Liberar el lock siempre, incluso si hay rollback
            r.delete(DECAY_LOCK_KEY)

    except redis.exceptions.ConnectionError as e:
        logger.error("redis_connection_error", error=str(e), exc_info=True)
    except Exception as e:
        logger.error("decay_job_outer_exception", error=str(e), exc_info=True)


def start_scheduler():
    """Configura y arranca el scheduler de APScheduler."""
    if not scheduler.running:
        scheduler.add_job(
            apply_weekly_forgetting_decay,
            trigger=CronTrigger(
                day_of_week=settings.DECAY_CRON_DAY_OF_WEEK,
                hour=settings.DECAY_CRON_HOUR,
                minute=settings.DECAY_CRON_MINUTE,
                timezone="UTC"
            ),
            id="weekly_forgetting_decay",
            replace_existing=True,
            misfire_grace_time=3600,  # 1 hora de gracia, para que se ejecute al reiniciar si se perdio
        )
        scheduler.start()
        logger.info("scheduler_started")
    else:
        logger.info("scheduler_already_running")


def shutdown_scheduler():
    """Detiene el scheduler de APScheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")