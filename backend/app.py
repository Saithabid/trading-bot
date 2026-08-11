"""
APP.PY
-------
Ye web server hai - website (frontend) isi se baat karti hai.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

from firebase_client import get_active_users, save_user_mt5_details
from mt5_engine import run_for_user

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


@app.route("/api/run-cycle", methods=["POST"])
def run_cycle():
    users = get_active_users()
    results = []
    for user in users:
        try:
            result = run_for_user(user)
        except Exception as e:
            result = {"user_id": user.get("user_id"), "status": "error", "error": str(e)}
        results.append(result)
    return jsonify({"processed": len(results), "results": results})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
