from flask import request, jsonify, current_app
from functools import wraps
import jwt
from model import Admin, Client

# 建立裝飾器，以設定走訪的API都必須帶有 Token 
def jwt_required(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization').split(' ')[1] if 'Authorization' in request.headers else None
        if not token:
            return jsonify({"message": "驗證失效"}), 401

        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms = ['HS256'], options={"verify_signature": False})
            public_id = payload['public_id']
            current_user = Admin.query.filter_by(public_id = public_id).first()

            if not current_user:
                return jsonify({"message": "找不到使用者"}), 401
            return fn(current_user, *args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token 已經過期"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "無效的 Token"}), 401
        
    return decorated

# 建立前台使用者裝飾器
def client_jwt_required(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization').split(' ')[1] if 'Authorization' in request.headers else None
        if not token:
            return jsonify({"message": "驗證失效"}), 401

        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms = ['HS256'], options={"verify_signature": False})
            public_id = payload['public_id']
            current_user = Client.query.filter_by(public_id = public_id).first()

            if not current_user:
                return jsonify({"message": "找不到使用者"}), 401
            return fn(current_user, *args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token 已經過期"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "無效的 Token"}), 401
        
    return decorated