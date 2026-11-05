from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Вызывает ошибку для теста Sentry"

    def handle(self, *args, **options) -> None:
        raise RuntimeError("Test error from Sentry")
