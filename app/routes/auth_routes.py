from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

from app import db
from app.models.user import User
from app.models.blacklisted_token import BlacklistedToken
from app.middleware.auth import token_required, cleanup_blacklisted_tokens

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['POST', 'OPTIONS'])
def signup():
    if request.method == 'OPTIONS':
        # Allows OPTIONS request for CORS
        return {}, 200

    data = request.get_json()

    if not data or not all(k in data for k in ['email', 'password', 'name']):
        return jsonify({'error': 'Name, email, and password are required'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long'}), 400

    hashed_password = generate_password_hash(
        data['password'], method='pbkdf2:sha256')
    new_user = User(
        email=data['email'],
        password=hashed_password,
        name=data['name'],
        # Default to 'user' if role not specified
        role=data.get('role', 'user')
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if 'email' in data and 'password' in data:
        email = data.get('email').lower()
        password = data.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            token = jwt.encode({
                'user_id': user.id,
                'role': user.role,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'email': user.email,
                    'name': user.name,
                    'role': user.role
                }
            })
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    else:
        return jsonify({'message': 'Invalid credentials'}), 401


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    try:
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            
            return jsonify({'error': 'No authorization token provided'}), 401

        token = auth_header.split(' ')[1]
        
        # Decode the token to get its expiration time
        token_data = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )

        # Calculate token expiration time
        exp_timestamp = token_data['exp']
        expires_at = datetime.fromtimestamp(exp_timestamp)

        # Add the token to blacklist
        blacklisted_token = BlacklistedToken(
            token=token,
            expires_at=expires_at
        )
        print(" authorization token provided wlkin lghalb lah ")
        db.session.add(blacklisted_token)
        db.session.commit()
        print(" authorization token provided wlkin lghalb lah 2")
        # Clean up old blacklisted tokens
        cleanup_blacklisted_tokens()
        print(" authorization token provided wlkin lghalb lah 3")
        return jsonify({
            'message': 'Successfully logged out',
            'status': 'success'
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 401


@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify if a token is valid and return user info"""
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({'valid': False, 'message': 'No token provided'}), 401

    try:
        token = auth_header.split(' ')[1]

        # Check if token is blacklisted
        blacklisted = BlacklistedToken.query.filter_by(token=token).first()
        if blacklisted:
            return jsonify({'valid': False, 'message': 'Token has been invalidated'}), 401

        # Decode token
        data = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )

        # Get user
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'valid': False, 'message': 'User not found'}), 401

        return jsonify({
            'valid': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.role
            }
        })

    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'valid': False, 'message': str(e)}), 401
