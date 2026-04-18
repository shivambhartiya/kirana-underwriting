from celery import Celery

from app.core.config import get_settings


settings = get_settings()

celery_backend = "cache+memory://" if settings.enable_local_sync_jobs else settings.redis_url
celery_broker = "memory://" if settings.enable_local_sync_jobs else settings.redis_url
celery_app = Celery("kirana_underwriting", broker=celery_broker, backend=celery_backend)
celery_app.conf.task_default_queue = "q_predict"
celery_app.conf.imports = (
    "app.workers.tasks_predict",
    "app.workers.tasks_cv",
    "app.workers.tasks_geo",
    "app.workers.tasks_explain",
    "app.workers.tasks_cleanup",
)
celery_app.conf.broker_connection_retry_on_startup = True
