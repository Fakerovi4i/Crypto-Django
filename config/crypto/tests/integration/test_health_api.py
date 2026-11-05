from unittest.mock import patch

from rest_framework.test import APITestCase


class TestHealthApi(APITestCase):
    @patch("crypto.services._check_db", return_value=True)
    @patch("crypto.services._check_cache", return_value=True)
    @patch("crypto.services._check_celery_broker", return_value=True)
    def test_health_ok(self, *_):
        """Проверяем, что API возвращает корректный ответ при рабочих сервисах"""
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["checks"], {"database": "ok", "cache": "ok", "celery_broker": "ok"})

    @patch("crypto.services._check_db", return_value=False)
    @patch("crypto.services._check_cache", return_value=False)
    @patch("crypto.services._check_celery_broker", return_value=True)
    def test_health_fail(self, *_):
        """Проверяем, что API возвращает корректный ответ при отказе сервисов"""
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["status"], "degraded")
        self.assertEqual(response.data["checks"], {"database": "fail", "cache": "fail", "celery_broker": "ok"})

    @patch("crypto.services._check_db", return_value=True)
    @patch("crypto.services._check_cache", return_value=True)
    @patch("crypto.services._check_celery_broker", return_value=False)
    def test_health_fail_broker_only(self, *_):
        """Проверяем, что API возвращает корректный ответ при отказе только брокера"""
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["checks"]["celery_broker"], "fail")
