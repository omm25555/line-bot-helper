import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import requests

app = Flask(__name__)
channel_secret = os.getenv('LINE_CHANNEL_SECRET', '').strip()
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '').strip()
gemini_key = os.getenv('GEMINI_API_KEY', '').strip()

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/")
def home():
    return "Bot OK Gemini 2.5"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def ask_ai(user_text):
    if not gemini_key:
        return "ยังไม่เจอ GEMINI_API_KEY ครับ"
    # ลองทุกรุ่นที่ฟรีตอนนี้
    models = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"]
    for model_name in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
            payload = {"contents": [{"parts": [{"text": f"คุณคือผู้ช่วย_789 พูดไทยเป็นกันเอง ตอบสั้นๆ: {user_text}"}]}]}
            r = requests.post(url, json=payload, timeout=20)
            data = r.json()
            print(f"TRY {model_name} -> {data}")
            if 'candidates' in data:
                return data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"{model_name} error {e}")
            continue
    return f"Gemini ตอบว่า: {data}"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    reply_text = ask_ai(event.message.text)
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message_with_http_info(
            ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply_text)])
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
