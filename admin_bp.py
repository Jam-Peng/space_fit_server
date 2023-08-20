from flask import Blueprint
from flask import request, jsonify, current_app
from decorators import jwt_required
import jwt
from model import db, Admin, admin_schema, admins_schema
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid

admin_bp = Blueprint('admin_bp', __name__)

# 登入 - 進行驗證後發送 Token
@admin_bp.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    # 檢查使用者是否有輸入使用者名稱和密碼
    if not username or not password:
        return jsonify({"message": "無法驗證"}), 401
    user = Admin.query.filter_by(name = username).first()

    if not user:
        return jsonify({"message": "帳號或密碼錯誤"}), 401

    if check_password_hash(user.password, password):
        # 因為datetime無法在dict格式中序列化，所以先拉出來做轉換成 strftime() - 測試時可以使用 2 分鐘
        date = (datetime.now()+timedelta(minutes = 30)).strftime("%Y-%m-%d %H:%M:%S")
        token = jwt.encode({
            "public_id": user.public_id, 
            "expires":  date
            },
            current_app.config["SECRET_KEY"],
            algorithm = "HS256",)
        return jsonify({
            "token": token, 
            "status": 200,
            "message": "登入成功",
            "admin": user.admin,
            "username": user.name
            })
    return jsonify({"message": "帳號或密碼錯誤"}), 401

# 產生新的 Token 
def generate_token(public_id):
    date = (datetime.now()+timedelta(minutes = 30)).strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "public_id": public_id,
        "expires":  date
    }    
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256', options={"verify_signature": False})
    return token

# Token 時效快過期，發送新的 Token
@admin_bp.route('/api/refresh_token', methods=['POST'])
def refresh_token():
    # 從請求中取得過期的 Token
    token = request.get_json().get('token')
    try:
        # 解碼過期的 Token，取得 public_id 或其他信息
        decoded_token = jwt.decode(token['token'], current_app.config['SECRET_KEY'], algorithms=['HS256'], options={"verify_signature": False})
        public_id = decoded_token.get('public_id')
        user = Admin.query.filter_by(public_id = public_id).first()

        # 重新取得新的 Token
        new_token = generate_token(public_id)
        return jsonify({
            "token": new_token, 
            "status": 200,
            "message": "登入成功",
            "admin": user.admin,
            "username": user.name
            })

    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token 已過期"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "無效的 Token"}), 401


# 更新管理者帳號、密碼 - 解析 Token 的函數
def decode_token(token):
    try:
        decoded_token = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'], options={"verify_signature": False})
        return decoded_token
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    
# 更新管理者帳號、密碼
@admin_bp.route('/api/updateAdmin', methods=['PUT'])
@jwt_required
def update_admin(current_user):
    try:
        if not current_user:                      # 不用判斷登入的使用者是否為最大權限的管理者 - 任何管理者都可以更改自己的帳密
            return jsonify({'message':'權限不足'})
        
        username = request.json.get('username')
        password = request.json.get('password')
        # 從 header 中取 Token
        auth_header = request.headers.get('Authorization') 

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "未提供有效的授權"}), 401
        token = auth_header.split(' ')[1]

    
        # 解析 Token
        decoded_token = decode_token(token)
        if not decoded_token:
            return jsonify({"message": "無效的授權或 Token 已過期"}), 401
        # 驗證取得管理者資料
        public_id = decoded_token.get('public_id')
        user = Admin.query.filter_by(public_id = public_id).first()  

        if not user:
            return jsonify({"message": "沒有這個管理者"}), 401
            
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)
        user.name = username
        user.password = hashed_password
        db.session.commit()
        return jsonify({
            "token": token, 
            "status": 200,
            "message": "更新成功",
            "admin": user.admin,
            "username": user.name
            })
    
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token已過期"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "無效的Token"}), 401


# 註冊新增管理者
@admin_bp.route('/api/register', methods=['POST'])
@jwt_required
def register_Admin(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        data = request.get_json()

        admin = Admin.query.filter_by(name = data['username']).first()
        if admin:
            return jsonify({"message": "帳號已註冊"}), 409

        hashed_password = generate_password_hash(data['password'], method="pbkdf2:sha256", salt_length=8) 
        new_admin = Admin(public_id = str(uuid.uuid4().hex), name = data['username'], password = hashed_password,
                        email = data['email'], admin = False)

        db.session.add(new_admin)
        db.session.commit()

        admin_data = admin_schema.dump(new_admin)
        return jsonify({
                "status": 200,
                "message": "註冊成功",
                'admin_data': admin_data
                }), 200
    
    except Exception as e:
        print(e)
        return jsonify({
            "message": "伺服器忙線中，請稍後再試",
            "status": 503,
            }), 503


# 取得全部管理者
@admin_bp.route('/api/admins', methods=['GET'])
@jwt_required
def get_Admins(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        admins = Admin.query.filter_by(delete = 0).all()

        admin_datas = admins_schema.dump(admins)

        return jsonify({
            "status": 200,
            "message": "取得資料成功",
            'admin_data': admin_datas
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({
            "message": "伺服器忙線中，請稍後再試",
            "status": 503,
            }), 503


# 將管理者放到待刪除中 - delete設為 1
@admin_bp.route('/api/setDeleteAdmin', methods=['POST'])
@jwt_required
def setDeleteAdmin(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        public_id  = request.json.get('public_id')
        admin = Admin.query.filter_by(public_id = public_id).first()
        if not admin:
            return jsonify({'message': '無此管理者資料'}), 404
        
        admin.delete = True
        db.session.commit()

        admin_data = admin_schema.dump(admin)

        return jsonify({
            "status": 200,
            'message': '刪除成功',
            'admin_data': admin_data
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "刪除失敗！"}), 400


# 更改管理者權限的功能
@admin_bp.route('/api/updateAdminAuth/<public_id>', methods=['PATCH'])
@jwt_required
def updateCourseCheckbox(current_user, public_id):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        admin_data = Admin.query.filter_by(public_id = public_id).first()
        if not admin_data:
            return jsonify({'message': '無此管理者資料'}), 404

        admin = request.json.get('admin')
        if admin == False:
            admin = True
        else:
            admin = False

        admin_data.admin = admin
        db.session.commit()

        return jsonify({
            "status": 200,
            'message': '權限更新成功',
            'admin_data': admin_schema.dump(admin_data),
            }), 200
    
    except Exception as e:
        print(e)
        return jsonify({"message": "更新失敗！"}), 400
    

# 取得所有被加到待刪除區的管理員
@admin_bp.route('/api/delAdmins', methods=['GET'])
def get_deletedAdmins():
    try:
        admins = Admin.query.filter_by(delete = 1).all()
        admin_datas = admins_schema.dump(admins)
        
        return jsonify({
            "status": 200,
            'message': '取得成功',
            'admin_data': admin_datas
            }), 200
    
    except Exception as e:
        print(e)
        return jsonify({
            "message": "伺服器發生錯誤，請稍後再試",
            "status": 500,
            }), 500

# 取回待刪除區的管理員
@admin_bp.route('/api/retrieveAdmins', methods=['PATCH'])
@jwt_required
def retrieveClients(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        public_id = request.json.get('public_id')
        admin = Admin.query.filter_by(public_id = public_id).first()
        if not admin:
            return jsonify({'message': '無此管理者資料'}), 404

        admin.delete = False
        db.session.commit()

        admin_data = admin_schema.dump(admin)
        return jsonify({
            "status": 200,
            'message': '管理員取回成功',
            'admin_data': admin_data,
            }), 200
    
    except Exception as e:
        print(e)
        return jsonify({"message": "取回失敗！"}), 400
    

# 確定刪除資料表中的管理員
@admin_bp.route('/api/deleteDataAdmin/<public_id>', methods=['DELETE'])
@jwt_required
def deleteDataClient(current_user, public_id):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        admin = Admin.query.filter_by(public_id = public_id).first()
        if not admin:
            return jsonify({'message': '沒有管理員可以進行刪除'}), 404
        
        db.session.delete(admin)
        db.session.commit()

        admin_data = admin_schema.dump(admin)
        return jsonify({
            "status": 200,
            'message': "已從資料庫刪除成功",
            'admin_data': admin_data
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "刪除失敗！"}), 400
