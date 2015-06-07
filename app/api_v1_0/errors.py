from flask import jsonify
from . import api
from app.exceptions import ValidationError


@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])


@api.errorhandler(404)
def not_found(e):
    return resource_not_found()


def bad_request(message):
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def resource_not_found():
    response = jsonify({'error': 'not found'})
    response.status_code = 404
    return response