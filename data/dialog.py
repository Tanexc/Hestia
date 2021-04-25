import datetime
import sqlalchemy
from sqlalchemy import orm
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import check_password_hash
from .db_session import SqlAlchemyBase


class Dialog(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "dialogs"

    id = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    label = sqlalchemy.Column(sqlalchemy.String, default="_")
    members = sqlalchemy.Column(sqlalchemy.String)
    modified_date = sqlalchemy.Column(sqlalchemy.String, default=datetime.datetime.now)
    file = sqlalchemy.Column(sqlalchemy.String)
