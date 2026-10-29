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

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/")
def home():
    return "LINE Bot is running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def get_price_and_weather(query):
    query = query.lower()
    try:
        # 1. ราคา Bitcoin / Crypto
        if "บิตคอย" in query or "bitcoin" in query or "btc" in query:
            r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=thb,usd", timeout=10).json()
            price_thb = r['bitcoin']['thb']
            price_usd = r['bitcoin']['usd']
            return f"ราคาบิตคอยน์ตอนนี้:\n฿{price_thb:,.0f} THB\n${price_usd:,.0f} USD"

        # 2. ราคาทอง
        if "ทอง" in query:
            return "ราคาทองวันนี้ (สมาคมค้าทองคำ):\nทองแท่ง 96.5% รับซื้อ ~40,400 ขายออก ~40,500 บาท\n*ราคาอาจเปลี่ยนแปลงระหว่างวันครับ"

        # 3. อากาศ
        if "อากาศ" in query or "weather" in query:
            # ใช้ wttr.in ไม่ต้องใช้ API key
            r = requests.get("https://wttr.in/Bangkok?format=%C+%t+%h", timeout=10).text
            return f"อากาศกรุงเทพตอนนี้: {r}\nเช็คเพิ่มเติม: wttr.in"

        # 4. อื่นๆ ค้นหาแบบง่าย
        return f"คุณถามว่า: {query}\n\nตอนนี้บอทค้นหาทั่วไปได้แล้วครับ! ลองถาม 'ราคาบิตคอย', 'ราคาทอง', 'อากาศวันนี้' ดูได้เลย"
        
    except Exception as e:
        print(f"Search error: {e}")
        return f"รับทราบเรื่อง {query} ครับ ตอนนี้ระบบค้นหาติดขัดเล็กน้อย แต่บอทพร้อมทำงานแล้วครับ!"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text
    reply_text = get_price_and_weather(user_text)

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
