from celery import Celery
from celery.schedules import crontab
from app.config import get_settings

settings = get_settings()
celery_app = Celery("trafficmind", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.timezone = "Europe/Moscow"
celery_app.conf.beat_schedule = {
    "daily-reports": {"task": "app.jobs.daily_reports.generate_daily_reports", "schedule": crontab(hour=9, minute=0)},
    "weekly-reports": {"task": "app.jobs.weekly_reports.generate_weekly_reports", "schedule": crontab(hour=9, minute=0, day_of_week="monday")},
    "monthly-reports": {"task": "app.jobs.monthly_reports.generate_monthly_reports", "schedule": crontab(hour=9, minute=0, day_of_month="1")},
    "subscription-checks": {"task": "app.jobs.subscription_jobs.check_subscriptions", "schedule": 60 * 60},
}
