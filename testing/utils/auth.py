import httpx
import time
from loguru import logger
import threading
from config.settings import settings


class TokenManager:
    """Manages access token and automatic background refresh"""

    def __init__(self, email: str, password: str):
        self.username = None
        self.password = password
        self.email = email
        self.access_token = None
        self.refresh_token = None
        self.expires_in = None
        self.refresh_thread = None
        self._stop_event = threading.Event()  # ← fixed: created here

        self._login()

    def _login(self):
        """Perform login and get tokens"""
        url = f"{settings.BASE_URL}/api/v1/auth/login"
        payload = {
            "email": self.email,
            "password": self.password,
            "remember_me": False
        }
        logger.info(f"🔍 Login URL: {url}")
        logger.info(f"🔍 Password: {'*' * len(self.password)}")

        response = httpx.post(url, json=payload, timeout=settings.REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.expires_in = 900
        logger.info(f"✓ Login successful. Token expires in {self.expires_in}s")

    def _refresh_access_token(self):
        """Refresh access token"""
        url = f"{settings.BASE_URL}/api/v1/auth/refresh"
        payload = {"refresh_token": self.refresh_token}

        try:
            response = httpx.post(url, json=payload, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
        except Exception as e:
            print(f"Failed to refresh token: {e}")
            self._stop_event.set()  # ← stop on failure

    def _background_refresh(self):
        """Background thread to auto-refresh token"""
        while not self._stop_event.wait(timeout=settings.TOKEN_REFRESH_INTERVAL):
            # wait() returns False on timeout, True when event is set
            # so when stop is signalled, wait() returns True and loop exits
            self._refresh_access_token()

    def start_background_refresh(self):
        """Start background token refresh thread"""
        if self.refresh_thread is None or not self.refresh_thread.is_alive():
            self._stop_event.clear()
            self.refresh_thread = threading.Thread(
                target=self._background_refresh,
                daemon=True  # ← dies automatically when pytest exits
            )
            self.refresh_thread.start()
            print("✓ Background token refresh started")

    def stop_background_refresh(self):
        """Stop background token refresh thread"""
        self._stop_event.set()  # ← wakes thread immediately
        if self.refresh_thread:
            self.refresh_thread.join(timeout=3)
        print("✓ Background token refresh stopped")

    def get_access_token(self):
        """Get current access token"""
        return self.access_token


def login_and_get_token_manager(email: str, password: str) -> TokenManager:
    """Login and return TokenManager with background refresh"""
    token_manager = TokenManager(email, password)
    token_manager.start_background_refresh()
    return token_manager