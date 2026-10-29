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
    return "LINE Bot 【entity-Meta¦canonical_name=Meta】 AI is running!"

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
    # ถ้ามี Key Groq ให้ใช้ 【entity-Meta¦canonical_name=Meta】 Llama 3.3 ของแท้
    if groq_key:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "คุณคือ 【entity-Meta¦canonical_name=Meta】 AI ผู้ช่วยส่วนตัวชื่อ ผู้ช่วย_789 พูดไทยเป็นกันเอง ฉลาด ตอบสั้นกระชับ ช่วยเรื่องราคาบิตคอย ทอง หุ้น ข่าว AI ธุรกิจ"},
                        {"role": "user", "content": user_text}
                    ]
                },
                timeout=20
            )
            data = r.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"Groq error: {e}")

    # ถ้าไม่มี Key ก็ตอบแบบฉลาดๆ แบบไม่ต้องเรียก API
    text_lower = user_text.lower()
    if "บิตคอย" in text_lower or "btc" in text_lower or "bitcoin" in text_lower:
        return "₿ บิตคอยน์ตอนนี้ ~2.15 ล้านบาท (~$65k)\nใส่ GROQ_API_KEY แล้วผมจะดึงราคาเรียลไทม์ให้แบบ AI เลยครับ"
    if "ทอง" in text_lower:
        return "💰 ทองแท่ง ~40,500 บาท/บาททอง\nใส่ GROQ_API_KEY แล้วผมจะเป็น AI เต็มตัวเลยครับ"
    if "สวัสดี" in text_lower or "ทำอะไร" in text_lower:
        return "สวัสดีครับ! ผมผู้ช่วย_789 🤖\nตอนนี้ผมตอบได้แล้ว ถ้าใส่ GROQ_API_KEY (ฟรีจาก console.groq.com/keys) ผมจะกลายเป็น 【entity-Meta¦canonical_name=Meta】 AI ฉลาดๆ คุยได้ทุกเรื่องเลยครับ"
    
    return f"รับทราบครับ: {user_text}\n\nใส่ GROQ_API_KEY ฟรีใน Render แล้วผมจะกลายเป็น Meta AI เต็มตัวเลยครับ ตอนนี้ผมตอบแบบพื้นฐานไปก่อนนะ"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    reply_text = ask_ai(event.message.text)
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
