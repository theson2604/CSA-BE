import os
from celery import Celery
import redis

celery = Celery(__name__, include=["app.tasks"])
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND")
celery.conf.update(
    timezone="Asia/Bangkok",
    enable_utc=False,
)
# celery.conf.beat_schedule = {
#     'scan_email_on_interval': {
#         'task': 'app.tasks.scan_email',
#         'schedule': 15.0,
#     },
# }

redis_client = redis.StrictRedis(host='redis', port=6379, db=0)