import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
CHECK_CHANNEL = '@MugiwaraResearcher'

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


@app.route('/')
def home():
    return {"status": "T4TSA Bot is running", "check_channel": CHECK_CHANNEL}, 200


@app.route('/api/check')
def check_membership():
    user_id_raw = request.args.get('user_id')
    
    if not user_id_raw:
        return jsonify({"joined": False, "error": "No user_id provided"}), 400

    # FIX: Convert to integer — Telegram requires this
    try:
        user_id = int(user_id_raw)
    except ValueError:
        return jsonify({"joined": False, "error": f"Invalid user_id: {user_id_raw}"}), 400

    try:
        r = requests.post(
            f"{BASE_URL}/getChatMember",
            json={"chat_id": CHECK_CHANNEL, "user_id": user_id},
            timeout=15
        )
        data = r.json()
        
        # DEBUG: Return raw Telegram response so you can see what's happening
        if not data.get('ok'):
            return jsonify({
                "joined": False,
                "telegram_error": data.get('description', 'Unknown Telegram error'),
                "user_id_used": user_id,
                "channel": CHECK_CHANNEL
            }), 200
            
        status = data['result']['status']
        is_member = status not in ['left', 'kicked']
        
        return jsonify({
            "joined": is_member,
            "status": status,
            "user_id_checked": user_id,
            "channel": CHECK_CHANNEL
        }), 200
        
    except Exception as e:
        return jsonify({
            "joined": False,
            "error": str(e),
            "user_id_used": user_id_raw
        }), 200


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
            }, timeout=10)
    
    return 'OK', 200


if __name__ == '__main__':
    if WEBHOOK_URL:
        try:
            requests.get(f"{BASE_URL}/setWebhook?url={WEBHOOK_URL}", timeout=10)
            print(f"Webhook set to: {WEBHOOK_URL}")
        except Exception as e:
            print(f"Webhook setup failed: {e}")
    
    app.run(host='0.0.0.0', port=5000)
