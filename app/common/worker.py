import os
import time

from celery import Celery


celery = Celery("celery_csa")
# celery.conf.broker_url = "redis://redis:6379/0"
# celery.conf.result_backend = "redis://redis:6379/0"
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")


@celery.task(name="create_task")
def create_task(task_type):
    time.sleep(int(task_type) * 10)
    return True