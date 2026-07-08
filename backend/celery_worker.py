from celery import Celery, Task
from celery.schedules import crontab
from app import app

# 1. Initialize the celety app

celery_app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
    include=['tasks']
)


# ======================
# CELERY BEAT SCHEDULE
# ======================

celery_app.conf.timezone = 'Asia/Kolkata'

celery_app.conf.beat_schedule = {
    'sse-heartbeat': {
        'task': 'tasks.send_sse_heartbeat',
        'schedule': 15.0, # Runs every 15 seconds
    },
    'daily-reminder-job': {
        'task': 'tasks.send_daily_reminders',
        # For testing purposes, we are setting this to run EVERY MINUTE.
        # In production, this would be: crontab(hour=8, minute=0)
        'schedule': crontab(minute='*'),
    },
    'monthly-admin-report': {
        'task': 'tasks.send_monthly_report',
        # Production: crontab(day_of_month='1', hour=9, minute=0)
        'schedule': crontab(minute='*/2')
    }
}


# 2. The VIP pass (Context Manager)

class FlaskTask(Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery_app.Task = FlaskTask