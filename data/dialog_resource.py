import datetime
from flask import jsonify
from flask_restful import Resource, abort
from .dialog_argpars import parser
from . import db_session
from .dialog import Dialog


class DialogsResource(Resource):
    def get(self, dialog_id):
        abort_if_dialog_not_found(dialog_id)
        session = db_session.create_session()
        dialog = session.query(Dialog).get(dialog_id)
        return jsonify({'dialog': dialog.to_dict()})

    def delete(self, dialog_id):
        abort_if_dialog_not_found(dialog_id)
        session = db_session.create_session()
        dialog = session.query(Dialog).get(dialog_id)
        deleted = dialog.to_dict()
        session.delete(dialog)
        session.commit()
        return jsonify({'success': 'OK', 'deleted_dialog': deleted})


def abort_if_dialog_not_found(dialog_id):
    session = db_session.create_session()
    dlg = session.query(Dialog).get(dialog_id)
    if not dlg:
        abort(404, message=f"Dialog with id = {dialog_id} not found")


class DialogsListResource(Resource):
    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        a = session.query(Dialog).filter(Dialog.id == args["id"]).first()
        if a:
            return jsonify({"error": "Id already exists"})
        dialog = Dialog(
            id=args["id"],
            members=args["members"],
            file=args["file"])
        session.add(dialog)
        session.commit()
        return jsonify({'success': 'OK', 'new_dialog': dialog.to_dict()})
