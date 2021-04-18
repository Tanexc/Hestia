import datetime
import sqlalchemy
from sqlalchemy import orm
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import check_password_hash
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = "users"

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True,
                           autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String)
    shortname = sqlalchemy.Column(sqlalchemy.String, unique=True, default=id)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    last_seen = sqlalchemy.Column(sqlalchemy.DateTime)
    address = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    confirmed = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    photo_path = sqlalchemy.Column(sqlalchemy.String, unique=True)
    avatar_id = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return f"<Colonist> {self.id} {self.surname} {self.name}"

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

