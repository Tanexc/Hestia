from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('file', required=True)
parser.add_argument('members', required=True)
parser.add_argument('id', required=True, type=int)
