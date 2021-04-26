import datetime
from flask import jsonify
from flask_restful import Resource, abort
from werkzeug.security import generate_password_hash
from .news_argpars import parser
from . import db_session
from .news import News


class NewsResource(Resource):
    def get(self, news_id):
        abort_if_new_not_found(news_id)
        session = db_session.create_session()
        new = session.query(News).get(news_id)
        return jsonify({'new': new.to_dict()})

    def delete(self, news_id):
        abort_if_new_not_found(news_id)
        session = db_session.create_session()
        new = session.query(News).get(news_id)
        deleted = new.to_dict()
        session.delete(new)
        session.commit()
        return jsonify({'success': 'OK', 'deleted_new': deleted})


def abort_if_new_not_found(news_id):
    session = db_session.create_session()
    new = session.query(News).get(news_id)
    if not new:
        abort(404, message=f"News with id = {news_id} not found")


class NewsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        new = session.query(News).all()
        return jsonify({'news': [item.to_dict() for item in new]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        if "id" in args:
            a = session.query(News).filter(News.id == args["id"]).first()
            if a:
                return jsonify({"error": "Id already exists"})
        news = News(
            id=args["id"],
            title=args["title"],
            content=args["content"] if 'content' in args else '',
            is_private=args["is_private"] if 'is_private' in args else False,
            user_shortname=args["user_shortname"],
            photo_name=args["photo_name"] if 'photo_name' in args else '0')
        session.add(news)
        session.commit()
        return jsonify({'success': 'OK', 'new_news': news.to_dict()})
