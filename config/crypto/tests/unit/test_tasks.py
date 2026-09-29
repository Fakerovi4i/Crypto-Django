from unittest.mock import patch, MagicMock

from django.test import SimpleTestCase

from crypto.providers.exceptions import TemporaryProviderError, PermanentProviderError
from crypto.tasks import fetch_snapshot_task


class TestFetchSnapshotTask(SimpleTestCase):
    def setUp(self):
        """Патчим рэдис из декоратра и fetch_and_save_snapshot"""
        p1 = patch("crypto.decorators.redis.from_url")
        self.from_url = p1.start()
        self.addCleanup(p1.stop)

        p2 = patch("crypto.tasks.fetch_and_save_snapshot")
        self.fetch_and_save_snapshot = p2.start()
        self.addCleanup(p2.stop)

        #мокаем получение рэдис
        self.from_url.return_value.set.return_value = True

    def test_fetch_snapshot_task_success(self):
        """Проверяем успешное выполнение задачи"""
        self.fetch_and_save_snapshot.return_value = MagicMock(pk=7)
        result = fetch_snapshot_task.apply()
        self.assertEqual(result.get(), {"snapshot_id": 7})

    def test_retries_temporary_error(self):
        """Проверяем, что задача выполняется с 3-мя ретраями и вызовом TemporaryProviderError"""
        self.fetch_and_save_snapshot.side_effect = TemporaryProviderError('Temporary error')
        result = fetch_snapshot_task.apply()
        self.assertEqual(self.fetch_and_save_snapshot.call_count, 4)# 1+3 ретрая
        self.assertEqual(result.state, 'FAILURE')

    def test_no_retries_permanent_error(self):
        """Проверяем, что задача выполняется с 1-й попыткой и вызовом PermanentProviderError"""
        self.fetch_and_save_snapshot.side_effect = PermanentProviderError('Permanent error')
        result = fetch_snapshot_task.apply()
        self.assertEqual(self.fetch_and_save_snapshot.call_count, 1)
        self.assertEqual(result.state, 'FAILURE')

    def test_one_instance_already_running(self):
        """Проверяем, что задача пропустится, если одна из задач уже выполняется"""
        self.from_url.return_value.set.return_value = None  # лок занят
        result = fetch_snapshot_task.apply()
        self.assertEqual(result.get(), {"skipped": True})
        self.fetch_and_save_snapshot.assert_not_called()
