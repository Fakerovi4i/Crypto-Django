import requests

from crypto.providers.exeptions import TemporaryProviderError, PermanentProviderError


class Connector:
    def __init__(self, headers: dict | None = None):
        self.headers = headers
        self.session: requests.Session | None = None

    def __enter__(self):
        self.session = requests.Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


    def get(self, url: str, params: dict, timeout: int = 10) -> list[dict] | dict:
        if self.session is None:
            raise RuntimeError("'Connector' должен использоваться как контекстный менеджер")

        try:
            response = self.session.get(url=url, params=params, headers=self.headers)
            response.raise_for_status()
        except (requests.ConnectionError, requests.Timeout) as e:
            raise TemporaryProviderError(f"Сетевая ошибка: {str(e)}") from e
        except requests.HTTPError as e:
            code = e.response.status_code
            if code == 429 or code >= 500:
                raise TemporaryProviderError(f"HTTP {str(e)}") from e
            raise PermanentProviderError(f"HTTP {str(e)}") from e

        return response.json()