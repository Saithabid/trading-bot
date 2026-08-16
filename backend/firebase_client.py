"""
FIREBASE_CLIENT.PY
--------------------
Firebase database se baat karne wala hissa. Passwords kabhi is file mein nahi likhe.
"""
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():
    if not firebase_admin._apps:
        service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if not service_account_json:
            raise Exception("FIREBASE_SERVICE_ACCOUNT environment variable set nahi hai.")
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


def save_user_mt5_details(user_id, mt5_login, mt5_password, mt5_server, symbol="EURUSD",
                           risk_percent=1.0, reward_ratio=2.0, strategy="auto",
                           lot_size=None, timeframe="15m"):
    db = init_firebase()
    data = {
        "mt5_login": int(mt5_login),
        "mt5_password": mt5_password,
        "mt5_server": mt5_server,
        "symbol": symbol,
        "risk_percent": risk_percent,
        "reward_ratio": reward_ratio,
        "strategy": strategy,
        "timeframe": timeframe,
        "active": True,
    }
    # lot_size optional hai - khali chorne par field hi save nahi hoti,
    # taake backend auto-calculate kar sake
    if lot_size not in (None, ""):
        data["lot_size"] = lot_size
    db.collection("users").document(user_id).set(data, merge=True)


def disconnect_user_mt5(user_id):
    """User khud disconnect kare to sirf active False kar dete hain - auto-trading ruk jati hai,
    lekin details save rehti hain taake dobara connect karna aasan ho."""
    db = init_firebase()
    db.collection("users").document(user_id).set({
        "active": False,
    }, merge=True)


def get_user_login_server(user_id):
    """Disconnect ke waqt MetaApi par account dhundne ke liye login/server chahiye
    (password ki zarurat nahi hoti undeploy karne ke liye)."""
    db = init_firebase()
    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    if not data.get("mt5_login"):
        return None
    return {
        "mt5_login": data.get("mt5_login"),
        "mt5_server": data.get("mt5_server"),
    }


def get_user_status(user_id):
    """Dashboard ke liye - MT5 connected hai ya nahi, password DIKHAYE bagair."""
    db = init_firebase()
    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        return {"connected": False}
    data = doc.to_dict()
    login_str = str(data.get("mt5_login", ""))
    masked = "***" + login_str[-3:] if len(login_str) >= 3 else "***"
    return {
        "connected": True,
        "mt5_login_masked": masked,
        "mt5_server": data.get("mt5_server"),
        "symbol": data.get("symbol"),
        "risk_percent": data.get("risk_percent"),
        "reward_ratio": data.get("reward_ratio", 2.0),
        "strategy": data.get("strategy", "auto"),
        "lot_size": data.get("lot_size"),
        "timeframe": data.get("timeframe", "15m"),
        "active": data.get("active", True),
    }


def get_user_trades(user_id):
    db = init_firebase()
    trades_ref = db.collection("users").document(user_id).collection("trades").order_by(
        "timestamp", direction=firestore.Query.DESCENDING
    ).limit(20)
    docs = trades_ref.stream()
    return [doc.to_dict() for doc in docs]


def log_trade(user_id, trade_info):
    db = init_firebase()
    db.collection("users").document(user_id).collection("trades").add(trade_info)
