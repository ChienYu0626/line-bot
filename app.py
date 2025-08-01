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
    price += (yuanwei // 2) * 250
    if yuanwei % 2 == 1:
        price += 130
    price += (xianggu // 2) * 300
    if xianggu % 2 == 1:
        price += 160
    return price

def generate_statistics():
    if not orders:
        return "目前沒有訂單記錄。"
    lines = []
    total_price = 0
    total_yuanwei = 0
    total_xianggu = 0
    for order in orders.values():
        name = order['name']
        y = order['order']['原味']
        x = order['order']['香菇']
        if name and (y > 0 or x > 0):
            price = calculate_price(y, x)
            total_price += price
            total_yuanwei += y
            total_xianggu += x
            lines.append(f"{name}：原味{y}斤，香菇{x}斤，共{price}元")
    summary = f"\n-\n原味總斤數：{total_yuanwei}斤\n香菇總斤數：{total_xianggu}斤\n總共：{total_price}元"
    return "目前訂單統計：\n" + "\n".join(lines) + summary

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
        orders[user_id] = {}

    lines = text.splitlines()
    success_lines = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
            name = parts[0]
            yuanwei = int(parts[1])
            xianggu = int(parts[2])
            if name not in orders[user_id]:
                orders[user_id][name] = {'原味': 0, '香菇': 0}
            orders[user_id][name]['原味'] += yuanwei
            orders[user_id][name]['香菇'] += xianggu
            success_lines.append(f"{name}：原味+{yuanwei}斤，香菇+{xianggu}斤")
    
    if success_lines:
        summary_lines = []
        total_price = 0
        total_yuanwei = 0
        total_xianggu = 0
        for name, order in orders[user_id].items():
            y = order['原味']
            x = order['香菇']
            price = calculate_price(y, x)
            total_price += price
            total_yuanwei += y
            total_xianggu += x
            summary_lines.append(f"{name}：原味{y}斤，香菇{x}斤，共{price}元")
        summary_lines.append(f"\n📊 總斤數：原味{total_yuanwei}斤，香菇{total_xianggu}斤\n💰 總金額：{total_price}元")
        reply = "✅ 已更新訂單：\n" + "\n".join(success_lines) + "\n\n📦 訂單統計：\n" + "\n".join(summary_lines)
    else:
        reply = "請輸入格式：\n名字 原味數量 香菇數量\n(例如：小美 3 4)\n可一次輸入多筆，每行一筆。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
