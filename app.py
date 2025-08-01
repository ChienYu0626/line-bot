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
    text = event.message.text.strip()
    parts = text.split()

    # 刪除訂單
    if len(parts) == 2 and parts[0] == "刪除":
        target_name = parts[1]
        deleted = False
        for user_id in list(orders.keys()):
            if orders[user_id]['name'] == target_name:
                del orders[user_id]
                deleted = True
        reply = f"🗑️ 已刪除{target_name}的訂單。" if deleted else f"⚠️ 找不到{target_name}的訂單。"
        reply += "\n\n" + generate_statistics()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 修改訂單
    if len(parts) == 4 and parts[0] == "修改" and parts[2].isdigit() and parts[3].isdigit():
        target_name = parts[1]
        yuanwei = int(parts[2])
        xianggu = int(parts[3])
        modified = False
        for order in orders.values():
            if order['name'] == target_name:
                order['order']['原味'] = yuanwei
                order['order']['香菇'] = xianggu
                modified = True
        if modified:
            price = calculate_price(yuanwei, xianggu)
            reply = f"✏️ 已修改{target_name}的訂單：\n原味{yuanwei}斤，香菇{xianggu}斤，共{price}元。"
        else:
            reply = f"⚠️ 找不到{target_name}的訂單。"
        reply += "\n\n" + generate_statistics()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 新增或累加訂單
    if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        name = parts[0]
        yuanwei = int(parts[1])
        xianggu = int(parts[2])
        found = False
        for order in orders.values():
            if order['name'] == name:
                order['order']['原味'] += yuanwei
                order['order']['香菇'] += xianggu
                found = True
                break
        if not found:
            orders[name] = {'name': name, 'order': {'原味': yuanwei, '香菇': xianggu}}

        total_yuanwei = orders[name]['order']['原味']
        total_xianggu = orders[name]['order']['香菇']
        price = calculate_price(total_yuanwei, total_xianggu)
        reply = f"✅ 已更新訂單：{name}\n原味：{total_yuanwei}斤\n香菇：{total_xianggu}斤\n共{price}元"
        reply += "\n\n" + generate_statistics()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 查詢統計
    if text == "統計":
        reply = generate_statistics()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 預設提示
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="請輸入格式：\n名字 原味數量 香菇數量\n例如：小美 3 4\n\n其他指令：\n- 統計\n- 刪除 姓名\n- 修改 姓名 原味數量 香菇數量")
    )

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
