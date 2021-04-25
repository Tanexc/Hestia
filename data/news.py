import datetime
import sqlalchemy
from sqlalchemy import orm
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import check_password_hash
from .db_session import SqlAlchemyBase


class News(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = "news"

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    date = sqlalchemy.Column(sqlalchemy.Date,
                             default=datetime.datetime.now().date())
    time = sqlalchemy.Column(sqlalchemy.Time,
                             default=datetime.datetime.now().time())
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    user_shortname = sqlalchemy.Column(sqlalchemy.String,
                                sqlalchemy.ForeignKey("users.shortname"))
    user = orm.relation('User')
    photo_name = sqlalchemy.Column(sqlalchemy.String, default=0)
