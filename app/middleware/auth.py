from functools import wraps
from flask import request, jsonify, current_app
import jwt
from app.models.user import User
from app.models.blacklisted_token import BlacklistedToken


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            token = auth_header.split(' ')[1]

            # Check if token is blacklisted
            blacklisted = BlacklistedToken.query.filter_by(token=token).first()
            if blacklisted:
                return jsonify({'message': 'Token has been invalidated'}), 401

            # Decode token
            data = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            current_user = User.query.get(data['user_id'])

            if not current_user:
                return jsonify({'message': 'User not found'}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'message': str(e)}), 401

        return f(current_user, *args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'message': 'Admin privileges required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

from app import db

def cleanup_blacklisted_tokens():
    """Remove expired tokens from the blacklist to keep the database clean"""
    from datetime import datetime
    expired_tokens = BlacklistedToken.query.filter(
        BlacklistedToken.expires_at < datetime.utcnow()).all()
    for token in expired_tokens:
        db.session.delete(token)
    db.session.commit()
