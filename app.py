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
groq_key = os.getenv('GROQ_API_KEY', '').strip()

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/")
def home():
    return f"Bot OK! GROQ_KEY exists={bool(groq_key)} len={len(groq_key)}"

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
    if not groq_key:
        return "ยังไม่เจอ GROQ_API_KEY ใน Render ครับ"
    
    # เช็คว่า Key ขึ้นต้นถูกไหม
    if not groq_key.startswith("gsk_"):
        return f"Key ที่ใส่มาไม่ขึ้นต้นด้วย gsk_ นะครับ ตอนนี้ขึ้นต้นด้วย {groq_key[:10]}... ไปก็อปใหม่จาก console.groq.com/keys นะครับ"

    models = ["llama-3.1-8b-instant", "llama3-70b-8192"]
    
    last_error = ""
    for model_name in models:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "คุณคือผู้ช่วย_789 ตอบสั้นเป็นกันเอง"},
                        {"role": "user", "content": user_text}
                    ]
                },
                timeout=25
            )
            data = r.json()
            print(f"MODEL {model_name} STATUS {r.status_code} DATA {data}")
            
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            
            # ถ้าไม่มี choices ให้เก็บ error ไว้บอก user
            last_error = str(data)
            
        except Exception as e:
            print(f"EXCEPTION {model_name}: {e}")
            last_error = str(e)
            continue

    # ถ้าลองหมดแล้วยังพัง จะบอกสาเหตุจริงๆ
    return f"Groq ตอบมาว่า: {last_error}\n\nลองไปเช็คที่ console.groq.com ว่า Key หมดอายุไหมครับ"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    reply_text = ask_ai(event.message.text)
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message_with_http_info(
            ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply_text)])
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
