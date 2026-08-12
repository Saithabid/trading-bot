"""
APP.PY
-------
Ye web server hai - website (frontend) isi se baat karti hai.
Ye Render (Linux) par chalta hai - is liye ismein MetaTrader5 ki
zarurat nahi (wo sirf Windows par chalti hai). Asal trading wala kaam
alag se "windows-worker" folder mein hai, jo Windows laptop/VPS par chalega.

Endpoints:
  POST /api/connect-mt5   -> user apna MT5 login/password/server bhejta hai, Firebase mein save hota hai
  GET  /api/status        -> bot zinda hai ya nahi, check karne ke liye
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

from firebase_client import save_user_mt5_details

app = Flask(__name__)
CORS(app)


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({"status": "bot zinda hai"})


@app.route("/api/connect-mt5", methods=["POST"])
def connect_mt5():
    """
    Website se aayega jab user apna MT5 add kare. Body (JSON):
    {
      "user_id": "firebase-user-ka-id",
      "mt5_login": 12345678,
      "mt5_password": "xxxx",
      "mt5_server": "Exness-MT5Trial7",
      "symbol": "EURUSD",
      "risk_percent": 1.0
    }
    """
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
