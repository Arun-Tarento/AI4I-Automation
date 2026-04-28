"""
Debug Script: Token Refresh Consistency Check
Logs in as ADMIN, then calls POST /auth/refresh 20 times with a 5-second gap.
Prints old vs new token comparison for each iteration.

Run from the testing/ directory:
    python debug_token_refresh.py
"""

import sys
import time
import httpx
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config.settingsv2 import settings


def run():
    base_url = settings.BASE_URL

    # Step 1: Login as ADMIN
    print("=" * 60)
    print("Logging in as ADMIN...")
    login_response = httpx.post(
        f"{base_url}{settings.AUTH_LOGIN}",
        json={
            "email": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD,
            "remember_me": False
        },
        timeout=settings.REQUEST_TIMEOUT
    )

    if login_response.status_code != 200:
        print(f"Login FAILED: {login_response.status_code} {login_response.text}")
        return

    login_data = login_response.json()
    current_access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    print(f"Login OK — access token tail: ...{current_access_token[-20:]}")
    print("=" * 60)

    # Step 2: Refresh 20 times with 5s gap
    for i in range(1, 21):
        print(f"\n[Iteration {i:02d}/20]")
        print(f"  OLD token: ...{current_access_token[-20:]}")

        refresh_response = httpx.post(
            f"{base_url}{settings.AUTH_REFRESH}",
            json={"refresh_token": refresh_token},
            timeout=settings.REQUEST_TIMEOUT
        )

        if refresh_response.status_code != 200:
            print(f"  Refresh FAILED: {refresh_response.status_code} {refresh_response.text}")
            break

        new_access_token = refresh_response.json().get("access_token", "")
        tokens_differ = new_access_token != current_access_token

        print(f"  NEW token: ...{new_access_token[-20:]}")
        print(f"  Tokens differ: {'✅ YES' if tokens_differ else '❌ NO  ← SAME TOKEN RETURNED'}")

        current_access_token = new_access_token

        if i < 20:
            print(f"  Waiting 5 seconds...")
            time.sleep(5)

    print("\n" + "=" * 60)
    print("Done.")


if __name__ == "__main__":
    run()
