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
groq_key = os.getenv('GROQ_API_KEY', '')

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/")
def home():
    return "LINE Bot Meta AI is running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def ask_meta_ai(user_text):
    if not groq_key:
        return "ใส่ GROQ_API_KEY ใน Render ก่อนนะครับ แล้วผมจะเป็น 【entity-Meta¦canonical_name=Meta】 AI เต็มตัวเลย"

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",  # ของ Meta แท้ๆ 100%
                "messages": [
                    {"role": "system", "content": "คุณคือ Meta AI ผู้ช่วยส่วนตัวชื่อ ผู้ช่วย_789 พูดไทย เป็นกันเอง ตอบสั้นกระชับ ช่วยเรื่องบิตคอย ทอง หุ้น ข่าว AI ธุรกิจได้"},
                    {"role": "user", "content": user_text}
                ]
            },
            timeout=20
        ).json()
        return r['choices'][0]['message']['content']
    except Exception as e:
        print(e)
        return f"AI พักครู่นึงครับ: {user_text}"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    reply = ask_meta_ai(event.message.text)
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message_with_http_info(
            ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply)])
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
