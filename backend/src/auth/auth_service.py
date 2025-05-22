from datetime import datetime, timedelta
from typing import Optional, Dict
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from db.models import User, db

class AuthService:
    def __init__(self):
        self.token_expires = timedelta(hours=24)
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            access_token = create_access_token(
                identity=username,
                expires_delta=self.token_expires
            )
            return {
                'token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }
        return None

    def register(self, username: str, email: str, password: str) -> Dict:
        if User.query.filter_by(username=username).first():
            raise ValueError('Username already exists')
            
        if User.query.filter_by(email=email).first():
            raise ValueError('Email already exists')
            
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        return {'message': 'User created successfully'}