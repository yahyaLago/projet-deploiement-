"""Client Python de l'API MaintAI.

Il reprend en Python ce que le client web du TP2 faisait en JavaScript.

    from maintai.client import MaintaiClient

    api = MaintaiClient("http://localhost:8000", api_key="demo123")
    api.predict({
        "temperature_c": 72,
        "vibration_mm_s": 6,
        "load_pct": 85,
        "runtime_hours": 15000,
    })
"""
import httpx


class APIError(RuntimeError):
    """L'API a répondu, mais avec un autre code que 200."""

    def __init__(self, status_code: int, detail):
        super().__init__(f"Erreur {status_code} : {detail}")
        self.status_code = status_code
        self.detail = detail


class MaintaiClient:
    """Petit client synchrone, utilisable avec ou sans serveur réel."""

    def __init__(
        self,
        url: str = "http://localhost:8000",
        api_key: str | None = None,
        http: httpx.Client | None = None,
    ):
        # Les tests passent un TestClient : le code reste le même, sans réseau.
        self._http = http or httpx.Client(base_url=url, timeout=5.0)
        self.api_key = api_key

    def _entetes(self) -> dict[str, str]:
        return {"X-API-Key": self.api_key} if self.api_key else {}

    def health(self) -> dict:
        """État du service."""
        response = self._http.get("/health")
        response.raise_for_status()
        return response.json()

    def predict(self, reading: dict) -> dict:
        """Envoie un relevé.

        Lève APIError si l'API refuse la requête et httpx.HTTPError si elle
        est injoignable.
        """
        response = self._http.post(
            "/v1/predict", json=reading, headers=self._entetes()
        )
        if response.status_code != 200:
            try:
                detail = response.json().get("detail")
            except ValueError:
                detail = response.text
            raise APIError(response.status_code, detail)
        return response.json()
