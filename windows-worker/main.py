"""
MAIN.PY (Worker Loop)
--------------------------
Ye file Render par as a background worker chalegi.
Firebase se sab active users uthati hai aur MetaApi ke zariye trade lagati hai.
"""

import time
from firebase_client import get_active_users
from metaapi_engine import run_for_user

CHECK_INTERVAL_SECONDS = 60 * 15  # har 15 minute baad dobara check karega

def main_loop():
    print("=== Cloud Trading Bot Worker Shuru Ho Gaya ===")
    while True:
        try:
            users = get_active_users()
            print(f"\n--- Cycle: {time.strftime('%Y-%m-%d %H:%M:%S')} | {len(users)} active users ---")
            
            for user in users:
                login_id = user.get('mt5_login', 'Unknown')
                try:
                    # Yahan hum default "BUY" bhej rahe hain
                    # Strategy ke hisab se isay BUY ya SELL mein change kar lein
                    result = run_for_user(user, signal_type="BUY")
                    print(f"[{login_id}] Result: {result}")
                except Exception as e:
                    print(f"[{login_id}] Error: {e}")
                    
        except Exception as e:
            print(f"Cycle error: {e}")

        print(f"--- Agla check {CHECK_INTERVAL_SECONDS // 60} minute baad ---")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main_loop()
