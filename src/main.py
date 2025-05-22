from flask import Flask, request, jsonify
from sqlalchemy import create_engine
import os
import json
from typing import Dict, Any

app = Flask(__name__)

# Database configuration
class DatabaseConfig:
    def __init__(self, config_file: str = 'config/database.json'):
        self.config = self._load_config(config_file)

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def get_connection_string(self, db_name: str) -> str:
        if db_name in self.config:
            db_config = self.config[db_name]
            return f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        raise ValueError(f"Database configuration not found for {db_name}")

# SQL Proxy class
class SQLProxy:
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        self.engines = {}

    def get_engine(self, db_name: str):
        if db_name not in self.engines:
            connection_string = self.db_config.get_connection_string(db_name)
            self.engines[db_name] = create_engine(connection_string)
        return self.engines[db_name]

    def execute_query(self, db_name: str, query: str) -> Dict[str, Any]:
        try:
            engine = self.get_engine(db_name)
            with engine.connect() as connection:
                result = connection.execute(query)
                return {
                    'status': 'success',
                    'data': [dict(row) for row in result]
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

# Initialize database configuration
db_config = DatabaseConfig()
sql_proxy = SQLProxy(db_config)

@app.route('/query', methods=['POST'])
def execute_query():
    data = request.get_json()
    
    if not data or 'database' not in data or 'query' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Missing required parameters: database and query'
        }), 400

    result = sql_proxy.execute_query(data['database'], data['query'])
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))