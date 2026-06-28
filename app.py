import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ========== CONFIG ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
CHECK_CHANNEL = '@MugiwaraResearcher'

if not BOT_TOKEN or not WEB_APP_URL:
    raise ValueError("Set BOT_TOKEN and WEB_APP_URL as environment variables!")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ========== API: CHECK MEMBERSHIP ==========
@app.route('/api/check')
def check_membership():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "No user_id"}), 400

    payload = {"chat_id": CHECK_CHANNEL, "user_id": user_id}
    
    try:
        r = requests.post(f"{BASE_URL}/getChatMember", json=payload, timeout=10)
        data = r.json()
        
        if not data.get('ok'):
            return jsonify({"joined": False}), 200
            
        status = data['result']['status']
        is_member = status not in ['left', 'kicked']
        
        return jsonify({"joined": is_member, "status": status})
        
    except Exception as e:
        return jsonify({"joined": False, "error": str(e)}), 200


# ========== WEBHOOK: HANDLE TELEGRAM MESSAGES ==========
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    if update and 'message' in update:
        msg = update['message']
        chat_id = msg['chat']['id']
        
        if msg.get('text') == '/start':
            keyboard = {
                "inline_keyboard": [[
                    {
                        "text": "🎬 Open T4TSA App",
                        "web_app": {"url": WEB_APP_URL}
                    }
                ]]
            }
            
            requests.post(f"{BASE_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": "👋 Welcome! Click below to open the app.",
                "reply_markup": keyboard
            })
    
    return 'OK', 200


# ========== HOME PAGE ==========
@app.route('/')
def home():
    return "T4TSA Bot is running!", 200


# ========== SET WEBHOOK ON STARTUP ==========
if __name__ == '__main__':
    if WEBHOOK_URL:
        requests.get(f"{BASE_URL}/setWebhook?url={WEBHOOK_URL}")
        print(f"Webhook set to: {WEBHOOK_URL}")
    
    app.run(host='0.0.0.0', port=5000)
