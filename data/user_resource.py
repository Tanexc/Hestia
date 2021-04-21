import datetime
from flask import jsonify
from flask_restful import Resource, abort
from werkzeug.security import generate_password_hash
from .user_argpars import parser
from . import db_session
from .users import User


class UsersResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        return jsonify({'user': user.to_dict()})

    def delete(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        usr = session.query(User).get(user_id)
        deleted = usr.to_dict()
        session.delete(usr)
        session.commit()
        return jsonify({'success': 'OK', 'deleted_user': deleted})


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f"User with id = {user_id} not found")


class UsersListResource(Resource):
    def get(self):
        session = db_session.create_session()
        usr = session.query(User).all()
        return jsonify({'users': [item.to_dict() for item in usr]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        b = session.query(User).filter(User.email == args["email"]).first()
        if b:
            return jsonify({"error": "This email is already in use"})
        if "id" in args:
            a = session.query(User).filter(User.id == args["id"]).first()
            if a:
                return jsonify({"error": "Id already exists"})
            user = User(
                id=args["id"],
                surname=args["surname"],
                name=args["name"],
                shortname=args["shortname"],
                address=args["address"],
                email=args["email"],
                hashed_password=generate_password_hash(args["password"]))
        else:
            user = User(
                surname=args["surname"],
                name=args["name"],
                shortname=args["shortname"],
                address=args["address"],
                email=args["email"],
                hashed_password=generate_password_hash(args["password"]))
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK', 'new_user': user.to_dict()})
