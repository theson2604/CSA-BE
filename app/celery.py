import os
from celery import Celery
import redis


celery = Celery(__name__, include=["app.tasks"])
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND")
celery.conf.beat_schedule_filename = 'celerybeat-schedule'
celery.conf.update(
    timezone="Asia/Bangkok",
    enable_utc=False,
    # beat_scheduler='redbeat.RedBeatScheduler'
    # beat_schedule={}
    # beat_schedule={'print_num_periodic_task': {   
    #         'task': 'app.tasks.print_num',
    #         'schedule': 10.0,  # Run every 10 seconds
    #     },}
)

redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

# celery.conf.task_routes = {
#     "app.tasks.*": {"queue": "default"},
#     "app.celery.*": {"queue": "default"},
# }


def trigger_task(task_name):
    # periodic_task_id = f'{task_name}_periodic_task'
    celery.conf.beat_schedule = {'print_num_periodic_task': {
            'task': 'app.tasks.print_num',
            'schedule': 5.0,  # Run every 10 seconds
            },
        }
    # celery.conf.update(
    #     # timezone="Asia/Bangkok",
    #     # enable_utc=False,
    #     # beat_schedule={}
    #     beat_schedule={'print_num_periodic_task': {
    #             'task': 'app.tasks.print_num',
    #             'schedule': 10.0,  # Run every 10 seconds
    #         },}
    # )