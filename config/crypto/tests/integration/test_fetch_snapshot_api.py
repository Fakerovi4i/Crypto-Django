from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class TestFetchSnapshotApi(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345", is_staff=True)

    @patch("crypto.views.fetch_snapshot_task")
    def test_start_task_return_202_admin_permission_worked(self, mock_task):
        """Проверяем, что эндпоинт /api/fetch-snapshot/ возвращает 202 и id задачи"""
        self.client.force_authenticate(user=self.user)
        mock_task.delay.return_value = MagicMock(id="abc-123")

        response = self.client.post("/api/fetch-snapshot/")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data, {"task_id": "abc-123"})

    def test_start_not_auth_401(self):
        """Проверяем, что эндпоинт /api/fetch-snapshot/ возвращает 401, если не отправлены учетные данные"""

        response = self.client.post("/api/fetch-snapshot/")

        self.assertEqual(response.status_code, 401)

    @patch("crypto.views.AsyncResult")
    def test_known_task_returns_status(self, mock_async_result):
        """Проверяем, что эндпоинт /api/fetch-snapshot-status/ возвращает 200 и статус задачи"""
        self.client.force_authenticate(user=self.user)

        mock_async_result.return_value = MagicMock(id="abc-123", status="SUCCESS", result={"snapshot_id": 7})

        response = self.client.get("/api/fetch-snapshot-status/abc-123/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["task_id"], "abc-123")
        self.assertEqual(response.data["status"], "SUCCESS")

    # Вариант чтоб не поднимать редис или убрать patch
    @patch("crypto.views.AsyncResult")
    def test_unknown_task_id_returns_pending(self, mock_async_result):
        """
        Проверяем, что эндпоинт /api/fetch-snapshot-status/ возвращает 200 и статус PENDING,
        если задача не существует
        """
        self.client.force_authenticate(user=self.user)
        mock_async_result.return_value = MagicMock(id="nonexistent-id", status="PENDING", result=None)

        response = self.client.get("/api/fetch-snapshot-status/nonexistent-id/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "PENDING")
