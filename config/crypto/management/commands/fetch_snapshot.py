from django.core.management.base import BaseCommand, CommandError

from crypto.tasks import fetch_snapshot_task


class Command(BaseCommand):
    help = "Запрашивает данные с API биржи и сохраняет снимок рынка в БД"

    def handle(self, *args, **options):
        result = fetch_snapshot_task.delay()
        self.stdout.write(f"Задача запущена: {result.id}, ожидаю...")
        try:
            data = result.get(timeout=10)
        except Exception as e:
            raise CommandError(f"Сбор снимка не удался: {e}")
        self.stdout.write(self.style.SUCCESS(f"Снимок сохранен: {data}"))
