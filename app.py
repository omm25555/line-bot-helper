from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import requests

app = Flask(__name__)

# อ่านจาก Environment Variables (ปลอดภัยกว่า)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def search_info(query):
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&pretty=1"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('AbstractText'):
            return data['AbstractText']
        topics = data.get('RelatedTopics', [])
        if topics and len(topics) > 0:
            first = topics[0]
            if isinstance(first, dict):
                return first.get('Text', f"เจอข้อมูลเกี่ยวกับ {query} ครับ")
        return f"รับทราบครับ คุณถามเรื่อง '{query}' ผมกำลังหาข้อมูลให้นะครับ"
    except Exception as e:
        return f"รับทราบเรื่อง {query} ครับ (ระบบค้นหาติดขัดนิดหน่อย: {e})"

@app.route("/", methods=['GET'])
def home():
    return "LINE Bot is running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Error: {e}")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    reply_text = search_info(user_text)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
