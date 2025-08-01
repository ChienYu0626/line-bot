from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 用你自己的 Channel Access Token 和 Secret
line_bot_api = LineBotApi('你的 Channel Access Token')
handler = WebhookHandler('你的 Channel Secret')

# 使用者狀態和訂單資料
user_states = {}
user_orders = {}

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
    msg = event.message.text.strip()
    
    # 初始化狀態
    if user_id not in user_states:
        user_states[user_id] = None

    # 預定流程
    if msg == "預定":
        user_states[user_id] = "waiting_for_amounts"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請問你要訂幾斤原味？幾斤香菇？\n範例：2 3")
        )
        return

    # 回覆預定數量
    elif user_states.get(user_id) == "waiting_for_amounts":
        try:
            parts = list(map(int, msg.split()))
            if len(parts) == 2:
                yuanshu = parts[0]
                xianggu = parts[1]
                user_orders[user_id] = {"原味": yuanshu, "香菇": xianggu}
                user_states[user_id] = None
                reply = f"✅ 已記錄你的訂單：\n原味 {yuanshu} 斤\n香菇 {xianggu} 斤"
            else:
                reply = "請輸入兩個數字，例如：2 3（代表原味2斤、香菇3斤）"
        except:
            reply = "格式錯誤，請輸入兩個數字，例如：2 3"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )
        return

    # 查看統計
    elif msg == "查看統計":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=count_orders())
        )
        return

    # 其他情況
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入「預定」開始訂購，或「查看統計」查看目前總量")
        )

def count_orders():
    total = {"原味": 0, "香菇": 0}
    for order in user_orders.values():
        for k in total:
            total[k] += order.get(k, 0)
    return f"📦 目前統計：\n原味：{total['原味']} 斤\n香菇：{total['香菇']} 斤"

if __name__ == "__main__":
    app.run()
