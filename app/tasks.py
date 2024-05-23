from celery import shared_task
import time

@shared_task
def create_task(value):
    time.sleep(20)
    return value