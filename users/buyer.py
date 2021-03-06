from flask import Blueprint
from flask import request
from flask import jsonify
import time
import json
# 数据库操作部分
from sqlalchemy import Column, String, Integer, ForeignKey, create_engine, PrimaryKeyConstraint, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from ini_db import db
from users import auth

from ini_db.db import session
from users import tools
import time
import datetime

# 注：标注有很长的-------------------------------的地方说明还需要修改


# Base = declarative_base()

# engin = create_engine('mysql+pymysql://root:Zhj2323864743@127.0.0.1:3306/final')



def testIfOK(user_id,password):
    user = session.query(db.auth).filter(db.auth.user_id==user_id,db.auth.passwd==password).first()
    if user is None:
        return False
    else:
        return True



bp = Blueprint("buyer", __name__, url_prefix="/buyer")



@bp.route("/new_order", methods=['POST'])
# 下单
def new_order():
    if request.method == 'POST':
        # 从post body中获取请求
        # data = request.get_data()
        # json_data = json.load(data.decode("utf-8"))
        # user_id = json_data.get("user_id")
        # store_id = json_data.get("store_id")
        # books = json_data.get("books")
        user_id = request.json.get("user_id")
        store_id = request.json.get("store_id")
        books = request.json.get("books")
    code, msg, order_id = do_order(user_id, store_id, books)
    return jsonify({ "msg": msg, "order_id": order_id}),code


def do_order(user_id, store_id, books):
    order_id = datetime.datetime.now().strftime("%d/%m/%Y  %H:%M:%S:%f")
    # order_id = time.strftime("%d/%m/%Y  %H:%M:%S:%f")
    # 用当前时间作为ID，不可能重复
    theSum = 0 #表示需要支付的钱
    try:
        session.query(db.auth).filter(db.auth.user_id==user_id).one()
    except:
        session.rollback()
        code = 501
        msg = "买家用户ID不存在"
        return code, msg, order_id
    try:
        session.query(db.Market).filter(db.Market.store_id==store_id).one()
    except:
        session.rollback()
        code = 502
        msg = "商铺ID不存在"
        return code, msg, order_id
    try:
        for i in books:
            the_book = session.query(db.BookinStore).filter(db.BookinStore.store_id==store_id, db.BookinStore.book_id == i["id"]).one()
            if(i["count"] > the_book.stock):
                code = 504
                msg = "商品库存不足"
                return code, msg, order_id
            theSum += i["count"] * the_book.price
    except:
        session.rollback()
        code = 503
        msg = "购买的图书不存在"
        return code, msg, order_id
    temp = db.order(order_id=order_id, user_id=user_id, store_id=store_id, price = theSum,status=0)
    session.add(temp)

    '''
    创建新的订单
    默认状态为0（未支付）
    '''
    # status = 0
    # amount=theSum
    # tools.insertOneOrder(order_id=order_id,store_id=store_id,user_id=user_id,books=books,
    #                                         amount=amount,status=status)
    # timeStamp = int(time.time())
    '''
    创建一个待删除的表
    根据当前时间计算出endTime
    后端运行一个进程时刻检查是否到达需要被删除的时间，如果到了就删除
    '''
    timeStamp = int(time.time())
    endTime = tools.calTimeStamp(startTimeStamp=timeStamp)
    tools.insertOneOderToCheck(order_id=order_id,endTime=endTime)             

    #返回成功                           
    code = 200
    msg = "下单成功"
    session.commit()
    return code, msg, order_id



@bp.route("/payment", methods=['POST'])
# 付款
def payment():
    if request.method == 'POST':
        # 从post body中获取请求
        data = request.get_data()
        json_data = json.loads(data.decode("utf-8"))
        user_id = json_data.get("user_id")
        order_id = json_data.get("order_id")
        password = json_data.get("password")
        verified = testIfOK(user_id,password)
        if verified:
            code, msg = do_pay(user_id, order_id)
        else:
            code = 401
            msg = "用户名或者密码错误错误"
        return jsonify({ "msg": msg}),code

    
def do_pay(user_id, order_id):
    try:
        the_order = session.query(db.order).filter(db.order.order_id==order_id).one()
    except:
        session.rollback()
        code = 502
        msg = "无效参数"
        
        return code, msg
    else:
        if(the_order.status != 0):
            code = 503
            msg = "订单已支付"
            return code, msg
        the_sum  = the_order.price
        #----------------------------------------------------------------------------------------------------------------
        #直接调用oder表中的数据，需要修改
        #----------------------------------------------------------------------------------------------------------------
        try:
             the_user = session.query(db.auth).filter(db.auth.user_id==user_id).one()
        except:
            session.rollback()
            code = 510
            msg = "用户错误"
            return code, msg
        has_money = the_user.money
        if the_sum > has_money:
            code = 501
            msg = "账户余额不足"
            
            return code, msg
        else:
            the_user.money -= the_sum
            the_order.status = 1
            session.commit()
            code = 200
            msg = "付款成功"
            
            return code, msg

@bp.route("/add_funds", methods=['POST'])
# 充钱
def add_funds():
    if request.method == 'POST':
        # 从post body中获取请求
        data = request.get_data()
        json_data = json.loads(data.decode("utf-8"))
        user_id = json_data.get("user_id")
        add_value = json_data.get("add_value")
        password = json_data.get("password")
        # 判断token是否过期或者错误:
        verified = testIfOK(user_id,password)
        # token正确:
        if verified:
            code, msg = do_add_funds(user_id, add_value)
        # token错误,返回报错
        else:
            code = 401
            msg = "token过期或用户名错误"
        return jsonify({ "msg": msg}),code


def do_add_funds(user_id, add_value):
    the_user = session.query(db.auth).filter(db.auth.user_id==user_id).first()
    if the_user is None:
        code = 501
        msg = "用户错误"
    else:
        the_user.money += add_value
        code = 200
        msg = "充值成功"
        session.commit()
    return code, msg

#取消订单路由函数order
@bp.route("/cancel",methods=['POST'])
def cancel():
    '''order
    取消订单逻辑：
    1.判断token是否过关
    2.执行cancel操作
    '''
    if request.method=='POST':
        #获取用户数据
        user_id = request.json.get("user_id")
        order_id = request.json.get("order_id")
        password = request.json.get("password")
        #检查token是否正确：
        ifVerified = testIfOK(user_id,password)
        if ifVerified:
            code, msg = doCancel(user_id,order_id)
        else:
            code = 401
            msg = "用户名或者token错误"
        return jsonify( {"msg": msg}),code

def doCancel(user_id,order_id):
    '''
    doCancel逻辑：
    1.检查orderid和用户名是否错误
    2.检查status 是否为0或1
        2.1 如果是0或1，则修改为-2，返回成功
        2.2如果是2或3，订单已经发出，返回失败
        2.3其他情况则说明订单已经被取消，返回失败
    '''

    try:
        myDoc = session.query(db.order).filter(db.order.order_id==order_id, db.order.user_id == user_id).one()
    except:
        session.rollback()
        code = 501
        msg = "订单号错误"
        return code, msg
    else:
        status = myDoc.status
        if status==0 or status==1:
            myDoc.status=-1
            session.commit()
            code = 200
            msg = "取消订单成功"
        elif status==2 or status==3:
            code = 402
            msg = "订单已经发出"
        else:
            code = 403
            msg = "订单已无效"
        return code, msg

    

    #搜索历史订单路由
@bp.route("/search",methods=['POST'])
def searchOrder():
    if request.method=='POST':
        #获取用户数据
        user_id = request.json.get("user_id")
        password = request.json.get("password")
    #检查token是否正确：
        ifVerified = testIfOK(user_id,password)
        if ifVerified:
            code, historyOrder = doSearch(user_id)
            return jsonify({"ordersits":historyOrder}),code
        else:
            code = 401
            msg = "用户名或者tokenits"
            return code,msg

def doSearch(user_id):
    #如果玩家名字错误，则报错
    try:
        historyOrder = session.query(db.order).filter(db.order.user_id==user_id).all()
    except:
        session.rollback()
        code = 510
        msg = "user_id错误"
        return code, msg
    #获取历史order的ID并且返回
    orderList = []
    for order in historyOrder:
        orderList.append(order.order_id)
    code = 200
    return code, orderList
    
#买家收货
@bp.route("/receive",methods=['POST'])
def receive():
    if request.method=='POST':
        #获取用户数据
        user_id = request.json.get("user_id")
        order_id = request.json.get("order_id")
        password = request.json.get("password")
        #检查token是否正确：
        ifVerified = testIfOK(user_id,password)
        if ifVerified:
            code, msg = doReceive(user_id,order_id)
        else:
            code = 403
            msg = "登出失败，用户名或者token错误"
        return jsonify( {"msg": msg}),code

def doReceive(user_id,order_id):
    #首先判断订单是否存在
    try:
        the_order = session.query(db.order).filter(db.order.order_id==order_id).one()
    except:
        session.rollback()
        code = 501
        msg = "找不到订单"
        return code, msg

    #判断订单状态是否为已发货
    status = the_order.status
    if status != 2:
        code = 502
        msg = "订单状态异常"
        return code, msg

    #判断该订单是否属于该用户
    the_owner = the_order.user_id
    if the_owner != user_id:
        code = 503
        msg = "该订单不属于您"
        return code, msg
    
    the_order.status = 3
    session.commit()
    code = 200
    msg = "成功！"
    return code ,msg




