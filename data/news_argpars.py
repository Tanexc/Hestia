from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('content', required=False)
parser.add_argument('date', required=False)
parser.add_argument('time', required=False)
parser.add_argument('id', required=False, type=int)
parser.add_argument('is_private', required=False)
parser.add_argument('user_shortname', required=True)
parser.add_argument('photo_name', required=False)
