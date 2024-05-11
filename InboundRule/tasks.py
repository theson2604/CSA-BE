import time
from app.common.celery import celery

@celery.task(name="create_task")
def create_task(value):
    time.sleep(6)
    return value