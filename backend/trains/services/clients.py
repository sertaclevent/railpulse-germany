from __future__ import annotations

from dataclasses import dataclass

import requests
from django.conf import settings


class ExternalAPIError(Exception):
    pass


@dataclass
class DBApiClient:
    base_url: str

    @property
    def headers(self) -> dict[str, str]:
        headers = {
            "Accept": "*/*",
        }
        if settings.DB_CLIENT_ID:
            headers["DB-Client-Id"] = settings.DB_CLIENT_ID
        if settings.DB_API_KEY:
            headers["DB-Api-Key"] = settings.DB_API_KEY
        return headers

    def get_json(self, path: str, params: dict | None = None) -> dict | list:
        try:
            response = requests.get(
                f"{self.base_url.rstrip('/')}/{path.lstrip('/')}",
                headers=self.headers,
                params=params,
                timeout=settings.HTTP_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise ExternalAPIError("External API request failed.") from exc
        except ValueError as exc:
            raise ExternalAPIError("External API did not return valid JSON.") from exc

    def get_text(self, path: str, params: dict | None = None, accept: str = "application/xml") -> str:
        headers = self.headers | {"Accept": accept}
        try:
            response = requests.get(
                f"{self.base_url.rstrip('/')}/{path.lstrip('/')}",
                headers=headers,
                params=params,
                timeout=settings.HTTP_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            raise ExternalAPIError("External API request failed.") from exc
