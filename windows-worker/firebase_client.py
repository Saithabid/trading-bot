"""
FIREBASE_CLIENT.PY (Worker version)
--------------------------------------
Windows machine se Firebase database ko padhta hai - kaunse users active hain,
unka MT5 login kya hai. Trades ka record bhi wapis Firebase mein likhta hai.
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
                "Isay apne Windows machine par set karein (README dekhein)."
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


def log_trade(user_id, trade_info):
    db = init_firebase()
    db.collection("users").document(user_id).collection("trades").add(trade_info)
