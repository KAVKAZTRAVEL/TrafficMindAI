from app.jobs.celery_app import celery_app


@celery_app.task(name="app.jobs.smart_alert_jobs.find_smart_alerts")
def find_smart_alerts() -> list[str]:
    return [
        "Появился новый источник трафика.",
        "Конверсия изменилась по сравнению со вчерашним днем.",
    ]
