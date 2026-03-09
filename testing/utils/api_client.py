import httpx
from config.settings import settings
import allure
import json

class APIClient:
    """
    Wrapper around httpx for authenticated API calls
    Supports both access token (from login) and API key (for services)
    """
    def __init__(self, token_manager, api_key: str = None):  # ← Fixed parameters
        self.base_url = settings.BASE_URL  # ← Fixed: settings (lowercase)
        self.token_manager = token_manager
        self.api_key = api_key
         
    def _get_headers(self):
        """Build headers with both access token and API key"""
        headers = {
            "Content-Type": "application/json",
            "x-auth-source": "BOTH"
        }
        
        # Add access token from login (Bearer token)
        if self.token_manager:
            headers["Authorization"] = f"Bearer {self.token_manager.get_access_token()}"
        
        # Add API key (separate header, not Authorization)
        if self.api_key:
            headers["X-API-Key"] = self.api_key  # ← Fixed: Use X-API-Key header
        
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

    
    def get(self, endpoint: str, **kwargs):
        """GET request"""
        url = f"{self.base_url}{endpoint}"
        response = httpx.get(
            url, 
            headers=self._get_headers(),  # ← Call method, not use self.headers
            timeout=settings.REQUEST_TIMEOUT,  # ← Fixed: settings (lowercase)
            **kwargs
        )
        self._attach_to_allure(response, "GET")
        return response
    
    def post(self, endpoint: str, extra_headers: dict = None, **kwargs):
        """POST request"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
    
        if extra_headers:
            headers.update(extra_headers)
        response = httpx.post(
            url, 
            headers=headers,  # ← Fixed: Call _get_headers() method
            timeout=settings.REQUEST_TIMEOUT,  # ← Fixed: settings (lowercase)
            **kwargs
        )
        self._attach_to_allure(response, "POST")
        return response


    def delete(self, endpoint: str, **kwargs):
        """DELETE request"""
        url = f"{self.base_url}{endpoint}"
        response = httpx.delete(
            url,
            headers=self._get_headers(),
            timeout=settings.REQUEST_TIMEOUT,
            **kwargs
        )
        self._attach_to_allure(response, "DELETE")
        return response
        

    def patch(self, endpoint: str, **kwargs):
        """PATCH request"""
        url = f"{self.base_url}{endpoint}"
        response = httpx.patch(
            url,
            headers=self._get_headers(),
            timeout=settings.REQUEST_TIMEOUT,
            **kwargs
        )
        self._attach_to_allure(response, "PATCH")
        return response


