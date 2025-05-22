from functools import wraps
from flask import request, jsonify
import jwt
import os

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            token = auth_header.split(' ')[1]
            jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
        except:
            return jsonify({'error': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated