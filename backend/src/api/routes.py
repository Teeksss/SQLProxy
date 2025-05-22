from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.query_service import QueryService
from db.connection import DatabaseManager

api = Blueprint('api', __name__)
db_manager = DatabaseManager()
query_service = QueryService(db_manager)

@api.route('/query', methods=['POST'])
@jwt_required
def execute_query():
    data = request.get_json()
    
    if not data or 'database' not in data or 'query' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        result = query_service.execute_query(
            data['database'],
            data['query']
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api.route('/databases', methods=['GET'])
@jwt_required
def list_databases():
    try:
        databases = db_manager.list_databases()
        return jsonify(databases)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api.route('/tables/<database>', methods=['GET'])
@jwt_required
def list_tables(database):
    try:
        tables = query_service.get_tables(database)
        return jsonify(tables)
    except Exception as e:
        return jsonify({'error': str(e)}), 400