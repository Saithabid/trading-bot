"""
APP.PY
-------
Ye web server hai - website (frontend) isi se baat karti hai.
Ye Render (Linux) par chalta hai - MetaTrader5 ki zarurat nahi is file mein.
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from firebase_client import (
    save_user_mt5_details,
    get_user_status,
    get_user_trades,
    get_active_users,
    disconnect_user_mt5,
    get_user_login_server,
)
from metaapi_engine import run_for_user, run_disconnect, ALLOWED_TIMEFRAMES

app = Flask(__name__)
CORS(app)

CRON_SECRET = os.environ.get("CRON_SECRET")


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({"status": "bot zinda hai"})


@app.route("/api/connect-mt5", methods=["POST"])
def connect_mt5():
    data = request.get_json()
    required = ["user_id", "mt5_login", "mt5_password", "mt5_server"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Ye fields chahiye: {missing}"}), 400

    lot_size = data.get("lot_size")
    if lot_size in ("", None):
        lot_size = None
    else:
        try:
            lot_size = float(lot_size)
        except (TypeError, ValueError):
            return jsonify({"error": "Lot size ek number hona chahiye"}), 400

    timeframe = data.get("timeframe", "15m")
    if timeframe not in ALLOWED_TIMEFRAMES:
        return jsonify({"error": f"Timeframe in mein se hona chahiye: {ALLOWED_TIMEFRAMES}"}), 400

    save_user_mt5_details(
        user_id=data["user_id"],
        mt5_login=data["mt5_login"],
        mt5_password=data["mt5_password"],
        mt5_server=data["mt5_server"],
        symbol=data.get("symbol", "EURUSD"),
        risk_percent=data.get("risk_percent", 1.0),
        reward_ratio=data.get("reward_ratio", 2.0),
        strategy=data.get("strategy", "auto"),
        lot_size=lot_size,
        timeframe=timeframe,
    )
    return jsonify({"message": "MT5 account jorh diya gaya"})


@app.route("/api/disconnect-mt5", methods=["POST"])
def disconnect_mt5():
    data = request.get_json()
    user_id = data.get("user_id") if data else None
    if not user_id:
        return jsonify({"error": "user_id chahiye"}), 400

    # Pehle MetaApi par account undeploy karne ki koshish karein taake
    # billing na lage - agar ye fail bhi ho jaye, Firestore disconnect phir bhi hoga
    creds = get_user_login_server(user_id)
    metaapi_note = ""
    if creds and creds.get("mt5_login") and creds.get("mt5_server"):
        try:
            result = run_disconnect(creds["mt5_login"], creds["mt5_server"])
            if not result.get("success"):
                metaapi_note = " (MetaApi par undeploy karte waqt warning aayi, manually check kar lein)"
        except Exception as e:
            print(f"MetaApi disconnect warning: {str(e)}")
            metaapi_note = " (MetaApi par undeploy karte waqt error aayi, manually check kar lein)"

    disconnect_user_mt5(user_id)
    return jsonify({
        "message": "MT5 account disconnect ho gaya, auto-trading ruk gayi hai" + metaapi_note
    })


@app.route("/api/user-status", methods=["GET"])
def user_status():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id chahiye"}), 400
    status_data = get_user_status(user_id)
    return jsonify(status_data)


@app.route("/api/trades", methods=["GET"])
def trades():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id chahiye"}), 400
    trades_data = get_user_trades(user_id)
    return jsonify({"trades": trades_data})


@app.route("/api/run-cycle", methods=["POST"])
def run_cycle():
    """
    Ye endpoint GitHub Actions (free scheduler) se har 15 minute call hoga.
    Free Render worker na hone ki wajah se, trading cycle isi web service
    ke andar chalta hai jab ye endpoint hit hota hai.

    signal_type ab hardcoded nahi - har user ki apni chuni hui strategy
    (aur apna chuna hua timeframe) market data dekh kar khud BUY/SELL/skip
    decide karti hai.
    """
    if request.headers.get("X-Cron-Secret") != CRON_SECRET:
        return jsonify({"error": "unauthorized"}), 403

    users = get_active_users()
    results = []
    for user in users:
        login_id = user.get("mt5_login", "Unknown")
        try:
            result = run_for_user(user)
            results.append({"login": login_id, "result": result})
        except Exception as e:
            results.append({"login": login_id, "error": str(e)})
    return jsonify({"checked": len(users), "results": results})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
