from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

from api import api_bp
from db import db
from auth import auth_bp

load_dotenv()

app = Flask(__name__)
CORS(app)

# Konfigürasyon
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Extensions
jwt = JWTManager(app)
db.init_app(app)

# Blueprint registrations
app.register_blueprint(api_bp, url_prefix='/api/v1')
app.register_blueprint(auth_bp, url_prefix='/auth')

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)