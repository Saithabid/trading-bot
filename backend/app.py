"""
APP.PY
-------
Ye web server hai - website (frontend) isi se baat karti hai.
Ye Render (Linux) par chalta hai - MetaTrader5 ki zarurat nahi is file mein.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

from firebase_client import save_user_mt5_details, get_user_status, get_user_trades

app = Flask(__name__)
CORS(app)


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

    save_user_mt5_details(
        user_id=data["user_id"],
        mt5_login=data["mt5_login"],
        mt5_password=data["mt5_password"],
        mt5_server=data["mt5_server"],
        symbol=data.get("symbol", "EURUSD"),
        risk_percent=data.get("risk_percent", 1.0),
    )
    return jsonify({"message": "MT5 account jorh diya gaya"})


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
