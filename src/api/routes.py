from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

api = Blueprint('api', __name__, url_prefix='/api/v1')

@api.route('/query', methods=['POST'])
@jwt_required
def execute_query():
    # Query execution logic
    pass

@api.route('/databases', methods=['GET'])
@jwt_required
def list_databases():
    # List available databases
    pass

@api.route('/tables/<database>', methods=['GET'])
@jwt_required
def list_tables(database):
    # List tables in database
    pass