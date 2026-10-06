from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase


class SnapshotsApiTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_snapshot_list_anonymous_200(self):
        """Аноним может читать список снимков"""
        response = self.client.get("/api/v1/snapshots/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_snapshot_post_not_allowed_405(self):
        """Снимки нельзя создавать через API"""
        response = self.client.post("/api/v1/snapshots/", {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_throttle_anonymous_429(self):
        """Аноним не может сделать более 5 запросов в минуту"""
        for _ in range(5):
            response = self.client.get("/api/v1/snapshots/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get("/api/v1/snapshots/")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("Retry-After", response.headers)

    def test_unknown_api_version_404(self):
        """Неизвестная версия API возвращает 404"""
        response = self.client.get("/api/v2/snapshots/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
