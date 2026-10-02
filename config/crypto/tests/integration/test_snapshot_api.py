from rest_framework import status
from rest_framework.test import APITestCase


class SnapshotsApiTests(APITestCase):
    def test_snapshot_list_anonymous_200(self):
        """Аноним может читать список снимков"""
        response = self.client.get("/api/snapshots/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_snapshot_post_not_allowed_405(self):
        """Снимки нельзя создавать через API"""
        response = self.client.post("/api/snapshots/", {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
