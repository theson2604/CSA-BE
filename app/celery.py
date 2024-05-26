import os
from celery import Celery
import redis


celery = Celery(__name__, include=["app.tasks"])
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND")

redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

# celery.conf.task_routes = {
#     "app.tasks.*": {"queue": "default"},
#     "app.celery.*": {"queue": "default"},
# }
