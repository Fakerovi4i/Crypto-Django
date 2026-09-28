import requests
from celery import shared_task
from crypto.services import fetch_and_save_snapshot


@shared_task(
    autoretry_for=(requests.ConnectionError, requests.Timeout),
    retry_backoff=True,
    max_retries=3,
)
def fetch_snapshot_task():
    snapshot = fetch_and_save_snapshot()
    return {"snapshot_id": snapshot.pk}

