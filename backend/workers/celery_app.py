from celery import Celery
from celery.schedules import crontab
from config import settings

# Initialize Celery
celery_app = Celery(
    'travel_agent',
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    'refresh-popular-routes': {
        'task': 'workers.tasks.refresh_popular_routes',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'cleanup-expired-offers': {
        'task': 'workers.tasks.cleanup_expired_offers',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(['workers'])
