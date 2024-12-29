from flask import Flask 
app = Flask(__name__)

from flask import request, abort, render_template
from linebot import LineBotApi, WebhookHandler
from flask_sqlalchemy import SQLAlchemy
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage,TextSendMessage,ImageSendMessage,StickerSendMessage,LocationSendMessage,QuickReply,QuickReplyButton, MessageAction,TemplateSendMessage,ImageCarouselTemplate, ImageCarouselColumn,ImageSendMessage,MessageTemplateAction,PostbackTemplateAction,URITemplateAction, ConfirmTemplate, PostbackTemplateAction
from urllib.parse import parse_qsl
from sqlalchemy import text

import os

line_bot_api = LineBotApi(os.environ.get('Channel_Access_Token'))
handler = WebhookHandler(os.environ.get('Channel_Secret'))


# 定義 PostgreSQL 連線字串
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:123456@127.0.0.1:5432/hotel'
db = SQLAlchemy(app)
liffid = '2006721883-5MM6Xo0G'



# 重置資料庫
@app.route('/createdb')
def createdb():
    sql = """
    DROP TABLE IF EXISTS hoteluser, booking;

    CREATE TABLE hoteluser (
    id serial NOT NULL,
    uid character varying(50) NOT NULL,
    PRIMARY KEY (id));

    CREATE TABLE booking (
    id serial NOT NULL,
    bid character varying(50) NOT NULL,
    roomtype character varying(20) NOT NULL,
    roomamount character varying(5) NOT NULL,
    datein character varying(20) NOT NULL,
    dateout character varying(20) NOT NULL,
    PRIMARY KEY (id))
    """
    db.session.execute(text(sql))
    db.session.commit()  
    return "資料表建立成功！"

#LIFF靜態頁面
@app.route('/page')
def page():
	return render_template('index.html', liffid = liffid)

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
    mtext = event.message.text
    user_id = event.source.user_id
    sql_cmd = "select * from hoteluser where uid='" + user_id + "'"
    query_data = db.session.execute(text(sql_cmd)).fetchall()
  
    if len(list(query_data)) == 0:
        sql_cmd = "insert into hoteluser (uid) values('" + user_id + "');"
        db.session.execute(text(sql_cmd))
        db.session.commit()

    mtext = event.message.text
    
    if mtext == '品牌介紹':
        try:
            message = TextSendMessage(text = "日本藏壽司創辦人田中社長小時候家裡是蔬果店，除蔬果外還賣有許多東西，某日社長被要求要細心地擦拭芥草（日本用來祭拜祖先或是神明的一種植物），與祖母兩人花費了半天的時間擦拭幾萬枚的芥草，對於幼年的社長來說十分痛苦，經過了一個小時後，就開始偷懶了，看到這個樣子的社長，平常很慈祥的祖母便很嚴厲地詢問社長「你是從哪裡出生的呢？因為有你的父親和母親，還有祖先們的存在，才會有現在的你不是嗎？這個芥草是客人們為了感謝祖先們的象徵，賣給客人用沾有泥巴的芥草去供養祖先，難道不會對客人感到抱歉嗎？」社長認為這是日本人的良心，但這個良心在現在的世道已經漸漸消失了，許多的公司也是這樣，只要不觸法就覺得做什麼都可以。社長認為日本本來的文化是對於看不見的東西，也十分重視，因此希望透過日本食物文化代表的壽司，再次的建立那美好的日本，並且向世界傳遞。")
            line_bot_api.reply_message(event.reply_token,message)
        except:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤!'))
    
    elif mtext[:3] == '###' and len(mtext) > 3:
         manageForm(event, mtext)
         
    elif mtext[:6] == '123456' and len(mtext) > 6:  #推播給所有顧客
         pushMessage(event, mtext)
    
    
    elif mtext =='菜單':
        try: 
            message = ImageSendMessage(
                original_content_url = "https://i.imgur.com/tvuknHu.jpeg",
                preview_image_url = "https://i.imgur.com/tvuknHu.jpeg"
            )
            line_bot_api.reply_message(event.reply_token,message)
        except:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤!'))
    
    
    elif mtext =='傳送位置':
        try: 
            message = LocationSendMessage(
                title='藏壽司郎',
                address='231新北市新店區中興路三段70號6樓',
                latitude=24.979500345293797, #緯度
                longitude=121.54634925521825 #經度
            )
            line_bot_api.reply_message(event.reply_token, message)
        except:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤!'))
    if mtext == '五星好評':
        try:
            message = TextSendMessage(
                text = '請幫我們評分',
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=MessageAction(label="一顆星", text="一顆星")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="兩顆星", text="兩顆星")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="三顆星", text="三顆星")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="四顆星", text="四顆星")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="五顆星", text="五顆星")
                        )
                    ]
                )
            )
            line_bot_api.reply_message(event.reply_token, message)
        except:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤!'))
    elif mtext == '推薦餐點':
         sendImgCarousel(event)
         
def pushMessage(event, mtext):  ##推播訊息給所有顧客
    try:
        msg = mtext[6:]  #取得訊息
        sql_cmd = "select * from hoteluser"
        query_data = db.session.execute(text(sql_cmd)).fetchall()
        userall = list(query_data)
        for user in userall:  #逐一推播
            message = TextSendMessage(
                text = msg
            )
            line_bot_api.push_message(to=user[1], messages=[message])  #推播訊息
    except:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤！'))

         


def sendImgCarousel(event): #圖片轉盤
            try:
             message = TemplateSendMessage(
             alt_text='圖片轉盤樣板',
             template=ImageCarouselTemplate(
             columns=[
             ImageCarouselColumn(
             image_url='https://i.imgur.com/9fgiedd.jpeg',
             action=MessageTemplateAction(
             label='點我看名稱',
             text='蝦子壽司'
             )
             ),
             ImageCarouselColumn(
             image_url='https://i.imgur.com/Tb5Kd65.png',
             action=MessageTemplateAction(
             label='點我看名稱',
             text='經典牛排壽司'
             )
             ),
             ImageCarouselColumn(
             image_url='https://i.imgur.com/g3BwrvP.jpeg',
             action=MessageTemplateAction(
             label='點我看名稱',
             text='明太子壽司'
             )
             )
             ]
             )
             )
             line_bot_api.reply_message(event.reply_token,message)
            except:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤！'))
                
def manageForm(event,mtext):
    try:
        flist = mtext[3:].split('/')
        text1='姓名:'+flist[0]+'\n'
        text1+='日期:'+flist[1]+'\n' 
        text1+='包廂:'+flist[2]+'\n'
        message=TextSendMessage(text=text1)
        line_bot_api.reply_message(event.reply_token,message)
    except:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤！'))
        
      
if __name__ =='__main__':
    app.run(debug=False)            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            