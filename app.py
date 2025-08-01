from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi('vMPuJGJbs0UGNOGBK270lDB+DL573GT70hDwopzzGvPhJUB9MSEbSLRpvTUQ57wHhn3og3GJCXVxeBSTggRxcE AUAbcptZeiQ8b9Ldwk8mVEV9kqJ0BGluqLtzjfoz5Ke4HLwe1zO1CkwjDm2i8dvwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('edd0043bc79b1e457dc90b0ddf04f896')

orders = {}  # 統一記錄所有名字的訂單，不分 user_id

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
    for name, order in orders.items():
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
    text = event.message.text.strip()
    
    lines = text.splitlines()
    success_lines = []

    for line in lines:
        parts = line.strip().split()

        # 🔸 修改功能：修改 小美 3 4
        if len(parts) == 4 and parts[0] == "修改" and parts[2].isdigit() and parts[3].isdigit():
            name = parts[1]
            yuanwei = int(parts[2])
            xianggu = int(parts[3])
            orders[name] = {'原味': yuanwei, '香菇': xianggu}
            success_lines.append(f"已修改 {name}：原味 {yuanwei}斤，香菇 {xianggu}斤")
            continue

        # 🔸 刪除功能：刪除 小美
        if len(parts) == 2 and parts[0] == "刪除":
            name = parts[1]
            if name in orders:
                del orders[name]
                success_lines.append(f"已刪除 {name} 的訂單")
            else:
                success_lines.append(f"查無 {name} 的訂單")
            continue

        # 🔸 新增功能：小美 2 3
        if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
            name = parts[0]
            yuanwei = int(parts[1])
            xianggu = int(parts[2])
            if name not in orders:
                orders[name] = {'原味': 0, '香菇': 0}
            orders[name]['原味'] += yuanwei
            orders[name]['香菇'] += xianggu
            success_lines.append(f"{name}：原味+{yuanwei}斤，香菇+{xianggu}斤")
            continue

        # 🔸 統計指令（不與其它一起執行）
        if line.strip() == "統計":
            reply = generate_statistics()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
            return

    # 若有新增/修改/刪除動作成功，回傳結果 + 統計
    if success_lines:
        reply = "處理結果：\n" + "\n".join(success_lines) + "\n\n" + generate_statistics()
    else:
        reply = "請輸入正確格式：\n\n- 新增：名字 原味數量 香菇數量\n- 修改：修改 名字 原味 香菇\n- 刪除：刪除 名字\n- 統計"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

