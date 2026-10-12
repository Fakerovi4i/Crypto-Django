import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


# ─── Расписание Beat ──────────────────────────
app.conf.beat_schedule = {
    "fetch-snapshot-every-60-min": {
        "task": "crypto.tasks.fetch_snapshot_task",  # ← имя задачи
        "schedule": 60 * 60,  # ← каждый час
        "options": {
            "expires": 600,  # если не выполнена за 10 минут — отменить
        },
    },
    # "cleanup-old-results-daily": {
    #     "task": "crypto.tasks.cleanup_old_results",
    #     "schedule": crontab(hour=3, minute=0),        # ← каждый день в 3:00
    # },
}
