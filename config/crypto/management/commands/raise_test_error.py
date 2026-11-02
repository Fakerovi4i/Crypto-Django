from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Вызывает ошибку для теста Sentry"

    def handle(self, *args, **options) -> None:
        a = 1 / 0
        print(a)
