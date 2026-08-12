from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_client

app = Flask(__name__)

# GitHub Pages se har kism ki request allow karne ke liye:
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "running", "message": "Bot is alive"}), 200

@app.route('/api/connect-mt5', methods=['POST', 'OPTIONS'])
def connect_mt5():
    # Browser preflight check handle karne ke liye
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Data receive nahi hua"}), 400

        # Firebase mein save karein
        if hasattr(firebase_client, 'save_user_credentials'):
            firebase_client.save_user_credentials(data)

        return jsonify({"success": True, "message": "Account Connected!"}), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
