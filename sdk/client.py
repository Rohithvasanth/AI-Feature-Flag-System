from typing import Optional, List
import httpx
from app.modules.feature_flags.schemas import FeatureFlag, EvaluationResult
from sdk.exceptions import (
    FeatureFlagClientError,
    FeatureFlagNotFoundError,
    FeatureFlagServerError
)

class FeatureFlagClient:
    """
    Python SDK client for interacting with the AI Feature Flag System API.
    """
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 5.0,
        custom_client: Optional[httpx.Client] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = custom_client or httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def evaluate(self, feature_name: str, user_id: str) -> EvaluationResult:
        """
        Evaluates a feature flag deterministically for a user.

        :param feature_name: Unique feature flag identifier
        :param user_id: Unique user identifier
        :return: EvaluationResult schema instance
        """
        url = f"/api/v1/flags/{feature_name}/evaluate"
        payload = {"user_id": user_id}
        
        try:
            response = self._client.post(url, json=payload)
            if response.status_code == 404:
                raise FeatureFlagNotFoundError(f"Feature flag '{feature_name}' not found on server")
            response.raise_for_status()
            return EvaluationResult(**response.json())
        except FeatureFlagClientError:
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise FeatureFlagNotFoundError(f"Feature flag '{feature_name}' not found")
            raise FeatureFlagServerError(f"Server returned HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise FeatureFlagServerError(f"Network error communicating with Feature Flag API: {e}")

    def get_flag(self, feature_name: str) -> FeatureFlag:
        """
        Fetches feature flag configuration from server.

        :param feature_name: Unique feature flag identifier
        :return: FeatureFlag schema instance
        """
        url = f"/api/v1/flags/{feature_name}"
        try:
            response = self._client.get(url)
            if response.status_code == 404:
                raise FeatureFlagNotFoundError(f"Feature flag '{feature_name}' not found")
            response.raise_for_status()
            return FeatureFlag(**response.json())
        except FeatureFlagClientError:
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise FeatureFlagNotFoundError(f"Feature flag '{feature_name}' not found")
            raise FeatureFlagServerError(f"Server returned HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise FeatureFlagServerError(f"Network error communicating with Feature Flag API: {e}")

    def list_flags(self) -> List[FeatureFlag]:
        """
        Fetches all feature flags from server.

        :return: List of FeatureFlag schema instances
        """
        url = "/api/v1/flags/"
        try:
            response = self._client.get(url)
            response.raise_for_status()
            return [FeatureFlag(**item) for item in response.json()]
        except Exception as e:
            raise FeatureFlagServerError(f"Error fetching feature flags: {e}")

    def close(self):
        try:
            self._client.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
