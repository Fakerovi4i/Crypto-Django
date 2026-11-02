import structlog
from celery import shared_task

from crypto.decorators import single_instance
from crypto.providers.exceptions import TemporaryProviderError
from crypto.services import analytics_cache, fetch_and_save_snapshot

logger = structlog.get_logger(__name__)


@shared_task(
    autoretry_for=(TemporaryProviderError,),
    retry_backoff=True,
    max_retries=3,
)
@single_instance("fetch_snapshot_task")
def fetch_snapshot_task():
    logger.info("fetch_snapshot_task", status="started")
    snapshot = fetch_and_save_snapshot()
    analytics_cache()
    logger.info("fetch_snapshot_task", snapshot_id=snapshot.pk, status="finished")
    return {"snapshot_id": snapshot.pk}
