from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi('vMPuJGJbs0UGNOGBK270lDB+DL573GT70hDwopzzGvPhJUB9MSEbSLRpvTUQ57wHhn3og3GJCXVxeBSTggRxcE AUAbcptZeiQ8b9Ldwk8mVEV9kqJ0BGluqLtzjfoz5Ke4HLwe1zO1CkwjDm2i8dvwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('edd0043bc79b1e457dc90b0ddf04f896')

orders = {}

def calculate_price(yuanwei, xianggu):
    price = 0
    if yuanwei == 1:
        price += 130
    elif yuanwei == 2:
        price += 250
    elif yuanwei > 2:
        price += 250 + (yuanwei - 2) * 130
    if xianggu == 1:
        price += 160
    elif xianggu == 2:
        price += 300
    elif xianggu > 2:
        price += 300 + (xianggu - 2) * 160
    return price

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    if user_id not in orders:
        orders[user_id] = {'name': None, 'order': {'原味': 0, '香菇': 0}}

    parts = text.split()
    if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        name = parts[0]
        yuanwei = int(parts[1])
        xianggu = int(parts[2])
        price = calculate_price(yuanwei, xianggu)
        orders[user_id] = {'name': name, 'order': {'原味': yuanwei, '香菇': xianggu}}
        reply = f"✅ 已記錄訂單：{name}\n原味 {yuanwei} 斤，香菇 {xianggu} 斤\n共 {price} 元"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    if text == "查看統計":
        if not orders:
            reply = "目前沒有訂單記錄。"
        else:
            lines = []
            for order in orders.values():
                if order['name']:
                    name = order['name']
                    y = order['order']['原味']
                    x = order['order']['香菇']
                    price = calculate_price(y, x)
                    lines.append(f"{name}，原味 {y} 斤，香菇 {x} 斤，共 {price} 元")
            reply = "📦 目前訂單統計：\n" + "\n".join(lines) if lines else "目前沒有訂單。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入格式：名字 原味數量 香菇數量\n或輸入「查看統計」"))

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

