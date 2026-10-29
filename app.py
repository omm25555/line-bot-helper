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

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/")
def home():
    return f"Bot OK! GROQ={bool(groq_key)}"

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
    # ลอง 3 รุ่น เผื่อรุ่นไหนดับ
    models = [
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "meta-llama/llama-4-maverick-17b-128e-instruct"
    ]
    if groq_key:
        for model_name in models:
            try:
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": "คุณคือ Meta AI ชื่อ ผู้ช่วย_789 พูดไทยเป็นกันเอง ฉลาด ตอบสั้นกระชับ"},
                            {"role": "user", "content": user_text}
                        ]
                    },
                    timeout=20
                )
                data = r.json()
                if 'choices' in data:
                    return data['choices'][0]['message']['content']
            except Exception as e:
                print(f"{model_name} failed: {e}")
                continue
    
    return "ขออภัยครับ เมื่อกี้เชื่อมต่อขัดข้อง ลองพิมพ์ใหม่ได้เลยครับ"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    reply_text = ask_ai(event.message.text)
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message_with_http_info(
            ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply_text)])
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
