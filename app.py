import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import requests

app = Flask(__name__)
channel_secret = os.getenv('LINE_CHANNEL_SECRET', '')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
groq_key = os.getenv('GROQ_API_KEY', '').strip()

print(f"=== DEBUG START ===")
print(f"GROQ_KEY loaded: {bool(groq_key)} length: {len(groq_key)}")
print(f"LINE_SECRET loaded: {bool(channel_secret)}")
print(f"=== DEBUG END ===")

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/")
def home():
    return f"Bot running! GROQ_KEY: {bool(groq_key)}"

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
    if groq_key:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": "คุณคือ Meta AI ชื่อ ผู้ช่วย_789 พูดไทยเป็นกันเอง ตอบสั้นกระชับ"},
                        {"role": "user", "content": user_text}
                    ]
                },
                timeout=20
            )
            print(f"Groq status: {r.status_code}")
            data = r.json()
            print(f"Groq response: {data}")
            if 'choices' in data:
                return data['choices'][0]['message']['content']
            else:
                return f"Groq ตอบมาแปลกๆ: {data}"
        except Exception as e:
            print(f"Groq error: {e}")
            return f"เชื่อมต่อ Meta AI ไม่ได้: {e}"

    return f"รับทราบครับ: {user_text}\n\nใส่ GROQ_API_KEY ฟรีใน Render แล้วผมจะเป็น Meta AI เต็มตัวเลยครับ (ตอนนี้ระบบอ่าน Key ไม่เจอ เลยตอบแบบนี้)"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    reply_text = ask_ai(event.message.text)
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message_with_http_info(
            ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply_text)])
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
