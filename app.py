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
    for user_orders in orders.values():
        for name, order in user_orders.items():
            y = order['原味']
            x = order['香菇']
            if y == 0 and x == 0:
                continue
            price = calculate_price(y, x)
            total_price += price
            total_yuanwei += y
            total_xianggu += x
            lines.append(f"{name}：原味{y}斤，香菇{x}斤，共{price}元")
    summary = f"\n-\n原味總斤數：{total_yuanwei}斤\n香菇總斤數：{total_xianggu}斤\n總共：{total_price}元"
    return "所有訂單統計：\n" + "\n".join(lines) + summary

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

    # 統計功能
    if text == "統計":
        reply = generate_statistics()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 初始化使用者訂單區
    if user_id not in orders:
        orders[user_id] = {}

    lines = text.splitlines()
    success_lines = []

    for line in lines:
        parts = line.strip().split()

        # 🔸 修改功能：修改 小美 3 4
        if len(parts) == 4 and parts[0] == "修改" and parts[2].isdigit() and parts[3].isdigit():
            name = parts[1]
            yuanwei = int(parts[2])
            xianggu = int(parts[3])
            orders[user_id][name] = {'原味': yuanwei, '香菇': xianggu}
            success_lines.append(f"✏已修改 {name}：原味 {yuanwei}斤，香菇 {xianggu}斤")
            continue

        # 🔸 刪除功能：刪除 小美
        if len(parts) == 2 and parts[0] == "刪除":
            name = parts[1]
            if name in orders[user_id]:
                del orders[user_id][name]
                success_lines.append(f"已刪除 {name} 的訂單")
            else:
                success_lines.append(f"查無 {name} 的訂單")
            continue

        # 🔸 新增多筆：小美 2 3
        if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
            name = parts[0]
            yuanwei = int(parts[1])
            xianggu = int(parts[2])
            if name not in orders[user_id]:
                orders[user_id][name] = {'原味': 0, '香菇': 0}
            orders[user_id][name]['原味'] += yuanwei
            orders[user_id][name]['香菇'] += xianggu
            success_lines.append(f"{name}：原味+{yuanwei}斤，香菇+{xianggu}斤")
            continue

    # 若有成功的指令
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
        summary_lines.append(f"\n總斤數：原味{total_yuanwei}斤，香菇{total_xianggu}斤\n總金額：{total_price}元")
        reply = "處理結果：\n" + "\n".join(success_lines) + "\n\n訂單統計：\n" + "\n".join(summary_lines)
    else:
        reply = "請輸入正確格式：\n- 新增：名字 原味數量 香菇數量\n- 修改：修改 名字 原味 香菇\n- 刪除：刪除 名字\n\n可一次多行輸入。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
