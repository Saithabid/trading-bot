"""
MAIN.PY (Windows Worker)
--------------------------
Ye file Windows laptop/VPS par chalti hai (MT5 terminal khula hone ke sath).
Firebase se sab active users uthati hai, har user ke liye baari-baari
connect -> analyze -> trade -> disconnect karti hai, phir loop dobara.

Chalane ka tareeqa:
    python main.py
"""

import time
from firebase_client import get_active_users
from mt5_engine import run_for_user

CHECK_INTERVAL_SECONDS = 60 * 15  # har 15 minute baad dobara check


def main_loop():
    print("=== Trading Bot Worker Shuru Ho Gaya ===")
    while True:
        try:
            users = get_active_users()
            print(f"\n--- Cycle: {time.strftime('%Y-%m-%d %H:%M:%S')} | {len(users)} active users ---")
            for user in users:
                try:
                    result = run_for_user(user)
                    print(f"[{result['user_id']}] {result}")
                except Exception as e:
                    print(f"[{user.get('user_id')}] Error: {e}")
        except Exception as e:
            print(f"Cycle error: {e}")

        print(f"--- Agla check {CHECK_INTERVAL_SECONDS // 60} minute baad ---")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main_loop()
