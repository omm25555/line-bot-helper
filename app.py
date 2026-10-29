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

# ในฟังก์ชัน ask_meta_ai เปลี่ยนเป็นแบบนี้
def ask_meta_ai(user_text):
    # 1. ลอง Groq ก่อน (ถ้ามี Key)
    groq_key = os.getenv('GROQ_API_KEY', '')
    if groq_key:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "คุณคือ Meta AI ชื่อ ผู้ช่วย_789 พูดไทยเป็นกันเอง ตอบสั้นกระชับ"},
                        {"role": "user", "content": user_text}
                    ]
                },
                timeout=15
            )
            j = r.json()
            if 'choices' in j:
                return j['choices'][0]['message']['content']
        except Exception as e:
            print(f"Groq failed: {e}")

    # 2. ถ้า Groq ไม่ได้ ใช้วิธีฟรีไม่ต้องใช้ Key (ตอบแบบฉลาดขึ้น)
    # ตอบแบบ Meta AI จำลองก่อน รอ Key
    return f"สวัสดีครับ! คุณถามว่า '{user_text}'\n\nตอนนี้ผมกำลังเชื่อมต่อกับสมอง Meta Llama 3.3 อยู่ครับ ใส่ GROQ_API_KEY ใน Render แล้วผมจะตอบแบบ AI เต็มตัวเลยครับ ตอนนี้ผมยังจำได้ว่าคุณอยากรู้เรื่อง {user_text} นะ"
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    reply = ask_meta_ai(event.message.text)
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message_with_http_info(
            ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply)])
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
