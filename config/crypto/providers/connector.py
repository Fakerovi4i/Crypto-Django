import requests



class Connector:
    def __init__(self, headers: dict | None = None):
        self.headers = headers
        self.session: requests.Session | None = None

    def __enter__(self):
        self.session = requests.Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    # @retry(3, 2)
    def get(self, url: str, params: dict) -> list[dict] | dict:
        if self.session is None:
            raise RuntimeError("'Connector' должен использоваться как контекстный менеджер")
        response = self.session.get(url=url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()