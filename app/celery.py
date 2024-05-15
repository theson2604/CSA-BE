import os
from celery import Celery


celery = Celery(__name__, include=["app.tasks"])
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND")

# celery.conf.task_routes = {
#     "app.tasks.*": {"queue": "default"},
#     "app.celery.*": {"queue": "default"},
# }

def get_active():
    inspector = celery.control.inspect()
    active_tasks = inspector.active()
    return active_tasks
