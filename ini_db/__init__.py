# flask 框架部分,用于前段交互
from flask import Blueprint
from flask import request
from flask import jsonify
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_httpauth import HTTPTokenAuth

# 数据库操作部分
from sqlalchemy import Column, String, Integer, ForeignKey, create_engine, PrimaryKeyConstraint, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.sql.sqltypes import TIMESTAMP
# 异常处理部分
import sqlalchemy
from itsdangerous import SignatureExpired
from itsdangerous import BadSignature


Base = declarative_base()

engine = create_engine(
    'mysql+pymysql://root:Zhj2323864743@127.0.0.1:3306/final')
DBsession = sessionmaker(bind=engine)

session_ = DBsession()

# bp = Blueprint("mul", __name__, url_prefix="/auth")

# myauth = HTTPTokenAuth()


class auth(Base):
    __tablename__ = "user_tbl"

    user_id = Column(String, primary_key=True)
    passwd = Column(String, nullable=False)
    money = Column(Integer, default=0)
    terminal = Column(String)
    token = Column(String)

    def __repr__(self):
        return "user_id: %s, passwd: %s, money: %d, terminal: %s, token: %s" % (
            self.user_id, self.passwd, self.money, self.terminal, self.token)


class Market(Base):
    __tablename__ = 'market'
    user_id = Column(String, ForeignKey(
        'users.username'), nullable=False)
    store_id = Column(String, nullable=False, primary_key=True, index=True)
    # __dict__ = {"owner_name": owner_name, "item_id": item_id}

    def __repr__(self):
        return "store_id: %d, user_id: %d" % (
            self.store_id, self.user_id)

    # def __init__(self, item_id, owner_name):
    # 	self.item_id = item_id
    # 	self.owner_name = owner_name
    # 	self.__dict__ = {"owner_name": self.owner_name, "item_id": self.item_id}


class Order(Base):
    __tablename__ = 'order'
    order_id = Column(String, nullable=False, primary_key=True)
    price = Column(Integer, nullable=False)
    starter_id = Column(String, ForeignKey('user_tbl.user_id'), nullable=False)
    status = Column(bool, default=False)

    def __repr__(self):
        return "order_id: %s, price: %d, starter_id: %d, terminal: %s, status: %d" % (
            self.store_id, self.user_id, self.starter_id, self.terminal, self.status)


class Book(Base):
    __tablename__ = 'book'


def initDB():
    if not database_exists(engine.url):
        create_database(engine.url)
    # global DBSession
    # DBSession = sessionmaker(bind=engine)
    # global session_
    # session_ = DBSession()

    try:
        create_db_()
    except ZeroDivisionError as e:
        print('Error occurs:', e)
    finally:

        print(engine)
        print("connected")


def create_db_():
    Base.metadata.create_all(engine)
    # insert the users

    # f_users = open(
    #     r"db\user_material.csv", "r+")
    # lines_users = f_users.readlines()
    # temp_users = []
    # for i in lines_users:
    #     temp_users.append(i.split())
    # f_users.close()
    # print(utils.create_user(temp_users))
    # # insert the items
    # f_items = open(
    #     r"db\item_material.csv", "r+")
    # lines_items = f_items.readlines()
    # temp_items = []
    # for i in lines_items:
    #     i = i.split()[0]
    #     temp_items.append(i)
    # f_items.close()
    # print(utils.create_item(temp_items))
