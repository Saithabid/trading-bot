"""
FIREBASE_CLIENT.PY
--------------------
Ye file Firebase database se baat karti hai. Kisi bhi user ka MT5 login/password
is code mein KAHIN NAHI likha - sab Firebase se live aata hai.
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():
    if not firebase_admin._apps:
        service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if not service_account_json:
            raise Exception(
                "FIREBASE_SERVICE_ACCOUNT environment variable set nahi hai. "
                "Render dashboard ya local .env file mein set karein."
            )
        cred_dict = json.loads(service_account_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()


def get_active_users():
    db = init_firebase()
    users_ref = db.collection("users").where("active", "==", True)
    docs = users_ref.stream()

    users = []
    for doc in docs:
        data = doc.to_dict()
        data["user_id"] = doc.id
        users.append(data)
    return users


def save_user_mt5_details(user_id, mt5_login, mt5_password, mt5_server, symbol="EURUSD", risk_percent=1.0):
    db = init_firebase()
    db.collection("users").document(user_id).set({
        "mt5_login": int(mt5_login),
        "mt5_password": mt5_password,
        "mt5_server": mt5_server,
        "symbol": symbol,
        "risk_percent": risk_percent,
        "active": True,
    }, merge=True)


def log_trade(user_id, trade_info):
    db = init_firebase()
    db.collection("users").document(user_id).collection("trades").add(trade_info)
