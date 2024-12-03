from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
import traceback
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

'''
def GPT_response(text):
    # 接收回應
    response = openai.Completion.create(model="gpt-3.5-turbo-instruct", prompt=text, temperature=0.5, max_tokens=500)
    print(response)
    # 重組回應
    answer = response['choices'][0]['text'].replace('。','')
    return answer
    '''

#N
def GPT_response(text):
    retries = 3  # Retry up to 3 times
    delay = 1    # Initial delay in seconds
    for attempt in range(retries):
        try:
            response = openai.Completion.create(
                model="gpt-3.5-turbo-instruct",
                prompt=text,
                temperature=0.5,
                max_tokens=500
            )
            print(response)
            # Extract and clean the response
            answer = response['choices'][0]['text'].strip()
            return answer
        except openai.error.RateLimitError:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise  # Re-raise if all retries fail


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

'''
# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    try:
        GPT_answer = GPT_response(msg)
        print(GPT_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))
    except:
        print(traceback.format_exc())
        line_bot_api.reply_message(event.reply_token, TextSendMessage('你所使用的OPENAI API key額度可能已經超過，請於後台Log內確認錯誤訊息'))
        '''
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    try:
        GPT_answer = GPT_response(msg)
        print(GPT_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))
    except openai.error.RateLimitError:
        line_bot_api.reply_message(event.reply_token, TextSendMessage('目前請求過多，請稍後再試！'))
    except Exception:
        print(traceback.format_exc())
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage('發生錯誤，請稍後再試或聯繫管理員檢查系統。')
        )
        

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)
    
if not all([os.getenv('CHANNEL_ACCESS_TOKEN'), os.getenv('CHANNEL_SECRET'), os.getenv('OPENAI_API_KEY')]):
    raise ValueError("Environment variables CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET, and OPENAI_API_KEY must be set.")
    
@app.route("/health", methods=["GET"])
def health_check():
    return "Server is running!", 200



@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)

@lru_cache(maxsize=100)
def GPT_cached_response(text):
    return GPT_response(text)

# In `handle_message`:
GPT_answer = GPT_cached_response(msg)



        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
