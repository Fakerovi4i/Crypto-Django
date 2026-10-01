from unittest.mock import MagicMock

import requests
from django.test import SimpleTestCase

from crypto.providers.connector import Connector
from crypto.providers.exceptions import PermanentProviderError, TemporaryProviderError


class TestConnectorMappingError(SimpleTestCase):
    def setUp(self):
        self.connector = Connector()
        self.connector.session = MagicMock()

    def test_network_errors_temporary(self):
        """Проверяем, что сетевые ошибки считаются временными"""

        # Для наглядности не параметризировал
        self.connector.session.get.side_effect = requests.exceptions.ConnectionError()
        with self.assertRaises(TemporaryProviderError):
            self.connector.get("http://example.com", {})

        self.connector.session.get.side_effect = requests.exceptions.Timeout()
        with self.assertRaises(TemporaryProviderError):
            self.connector.get("http://example.com", {})

    def test_http_codes(self):
        """Проверяем соответствие HTTP-кодов"""
        cases = [
            (429, TemporaryProviderError),
            (500, TemporaryProviderError),
            (400, PermanentProviderError),
            (404, PermanentProviderError),
        ]

        for code, expected in cases:
            with self.subTest(code=code):
                response = MagicMock()
                response.raise_for_status.side_effect = requests.HTTPError(response=MagicMock(status_code=code))
                self.connector.session.get.return_value = response
                with self.assertRaises(expected):
                    self.connector.get("http://example.com", {})
