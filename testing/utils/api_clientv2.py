import httpx
from config.settingsv2 import settings
import allure
import json


class APIClient:
    """
    JWT-only API client wrapper for test_api_01/
    Uses Bearer token authentication only (no API keys)
    """

    def __init__(self, token_manager):
        """
        Initialize API client with JWT token manager

        Args:
            token_manager: TokenManager instance with JWT access token
        """
        self.base_url = settings.BASE_URL
        self.token_manager = token_manager

    def _get_headers(self, extra_headers: dict = None):
        """
        Build headers with JWT Bearer token only

        Args:
            extra_headers: Optional additional headers to merge

        Returns:
            dict: HTTP headers with Authorization Bearer token
        """
        headers = {
            "Content-Type": "application/json"
        }

        # Add JWT Bearer token
        if self.token_manager:
            headers["Authorization"] = f"Bearer {self.token_manager.get_access_token()}"

        # Merge any extra headers (e.g., X-Context-Aware)
        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _attach_to_allure(self, response: httpx.Response, method: str):
        """Attach full request and response details to the Allure report."""

        # --- REQUEST ---
        request = response.request
        # Request body (may be empty for GET/DELETE)
        try:
            request_body = json.loads(request.content)
            request_body_str = json.dumps(request_body, indent=2)
        except Exception:
            request_body_str = request.content.decode("utf-8", errors="ignore") or "(no body)"

        allure.attach(
            body=f"{method} {request.url}\n\n{request_body_str}",
            name=f"Request — {method}",
            attachment_type=allure.attachment_type.JSON,
        )

        # --- RESPONSE ---
        try:
            response_body = json.dumps(response.json(), indent=2)
        except Exception:
            response_body = response.text or "(no body)"

        allure.attach(
            body=f"Status: {response.status_code}\n\n{response_body}",
            name=f"Response — {response.status_code}",
            attachment_type=allure.attachment_type.JSON,
        )

    def get(self, endpoint: str, extra_headers: dict = None, **kwargs):
        """
        HTTP GET request

        Args:
            endpoint: API endpoint path (e.g., "/api/v1/auth/me")
            extra_headers: Optional additional headers
            **kwargs: Additional httpx.get() parameters

        Returns:
            httpx.Response: Response object
        """
        url = f"{self.base_url}{endpoint}"
        response = httpx.get(
            url,
            headers=self._get_headers(extra_headers),
            timeout=settings.REQUEST_TIMEOUT,
            **kwargs
        )
        self._attach_to_allure(response, "GET")
        return response

    def post(self, endpoint: str, extra_headers: dict = None, **kwargs):
        """
        HTTP POST request

        Args:
            endpoint: API endpoint path
            extra_headers: Optional additional headers
            **kwargs: Additional httpx.post() parameters (e.g., json=payload)

        Returns:
            httpx.Response: Response object
        """
        url = f"{self.base_url}{endpoint}"
        response = httpx.post(
            url,
            headers=self._get_headers(extra_headers),
            timeout=settings.REQUEST_TIMEOUT,
            **kwargs
        )
        self._attach_to_allure(response, "POST")
        return response

    def patch(self, endpoint: str, extra_headers: dict = None, **kwargs):
        """
        HTTP PATCH request

        Args:
            endpoint: API endpoint path
            extra_headers: Optional additional headers
            **kwargs: Additional httpx.patch() parameters

        Returns:
            httpx.Response: Response object
        """
        url = f"{self.base_url}{endpoint}"
        response = httpx.patch(
            url,
            headers=self._get_headers(extra_headers),
            timeout=settings.REQUEST_TIMEOUT,
            **kwargs
        )
        self._attach_to_allure(response, "PATCH")
        return response

    def delete(self, endpoint: str, extra_headers: dict = None, **kwargs):
        """
        HTTP DELETE request

        Args:
            endpoint: API endpoint path
            extra_headers: Optional additional headers
            **kwargs: Additional httpx.delete() parameters

        Returns:
            httpx.Response: Response object
        """
        url = f"{self.base_url}{endpoint}"
        response = httpx.delete(
            url,
            headers=self._get_headers(extra_headers),
            timeout=settings.REQUEST_TIMEOUT,
            **kwargs
        )
        self._attach_to_allure(response, "DELETE")
        return response

    def put(self, endpoint: str, extra_headers: dict = None, **kwargs):
        """
        HTTP PUT request

        Args:
            endpoint: API endpoint path
            extra_headers: Optional additional headers
            **kwargs: Additional httpx.put() parameters

        Returns:
            httpx.Response: Response object
        """
        url = f"{self.base_url}{endpoint}"
        response = httpx.put(
            url,
            headers=self._get_headers(extra_headers),
            timeout=settings.REQUEST_TIMEOUT,
            **kwargs
        )
        self._attach_to_allure(response, "PUT")
        return response
