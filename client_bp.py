import uuid
from flask import Blueprint
from flask import request, jsonify, current_app
from decorators import client_jwt_required, jwt_required
import jwt
from model import db, Client, ClientImage, client_schema
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import base64

client_bp = Blueprint('client_bp', __name__)

# 登入 - 進行發送 Token
@client_bp.route('/client/login/api/v1', methods=['POST'])
def login():
    try:
        username = request.json.get('username')
        password = request.json.get('password')

        # 檢查使用者是否有輸入使用者名稱和密碼
        if not username or not password:
            return jsonify({"message": "資料不完整"}), 401
        
        user = Client.query.filter_by(name = username).first()
        if not user:
            return jsonify({"message": "尚未註冊"}), 401

        if check_password_hash(user.password, password):
            # 因為datetime無法在dict格式中序列化，所以先拉出來做轉換成 strftime() - 測試時可以使用 2 分鐘
            date = (datetime.now()+timedelta(minutes = 2)).strftime("%Y-%m-%d %H:%M:%S")
            token = jwt.encode({
                "public_id": user.public_id, 
                "expires":  date
                },
                current_app.config["SECRET_KEY"],
                algorithm = "HS256")
            result = client_schema.dump(user)
            
            # 將照片解析後放回
            decoded_images = []
            for image in user.images:
                if image.image_path:
                    image_data = base64.b64encode(image.image_path).decode()
                    decoded_images.append(image_data)
            result["images"] = decoded_images

            return jsonify({
                "token": token, 
                "status": 200,
                "message": "登入成功",
                "client_data": result
                })
        return jsonify({"message": "帳號或密碼錯誤"}), 401
    except Exception as e:
        print(e)
        return jsonify({
            "message": "伺服器維修中，請稍後再試",
            "status": 503,
            }), 503
    
# 註冊
@client_bp.route('/client/register/api/v1', methods=['POST'])
def create_client():
    data = {}
    try:
        data = request.get_json()

        client = Client.query.filter_by(name = data['username']).first()
        if client:
            return jsonify({"message": "帳號已註冊"}), 409

        hashed_password = generate_password_hash(data['password'], method='scrypt') 
        new_user = Client(public_id = str(uuid.uuid4().hex), name = data['username'], password = hashed_password,
                        email = data['email'], phone = data['phone'], vip = 0 )

        db.session.add(new_user)
        db.session.commit()

        result = client_schema.dump(new_user)
        return jsonify({
                "status": 200,
                "message": "註冊成功",
                "data": result,
                }), 200
    except Exception as e:
        print(e)
        return jsonify({
            "message": "伺服器忙線中，請稍後再試",
            "status": 503,
            }), 503

# 產生新的 Token 
def generate_token(public_id):
    date = (datetime.now()+timedelta(minutes = 30)).strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "public_id": public_id,
        "expires":  date
    }    
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token

# Token 時效快過期，發送新的 Token
@client_bp.route('/client/refresh_token/api/v1', methods=['POST'])
def refresh_token():
    # 從請求中取得快過期的 Token
    token = request.get_json().get('token')
    try:
        # 解碼過期的 Token，取得 public_id 或其他信息
        decoded_token = jwt.decode(token['token'], current_app.config['SECRET_KEY'], algorithms=['HS256'])
        public_id = decoded_token.get('public_id')
        user = Client.query.filter_by(public_id = public_id).first()

        # 重新解析加載客戶大頭照的影像再回傳
        client_data = client_schema.dump(user) 
        decoded_images = []
        for image in user.images:
            if image.image_path:
                image_data = base64.b64encode(image.image_path).decode()
                decoded_images.append(image_data)
        client_data["images"] = decoded_images

        # 重新取得新的 Token
        new_token = generate_token(public_id)
        
        return jsonify({
            "token": new_token, 
            "status": 200,
            "message": "登入成功",
            "client_data": client_data ,
            })

    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token 已過期"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "無效的 Token"}), 401


# 更新會員資料
@client_bp.route('/client/update_account/<public_id>/api/v1', methods=['PUT'])
@client_jwt_required
def update_account(current_user, public_id):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        client = Client.query.filter_by(public_id = public_id).first()
        if not client:
            return jsonify({'message': '查無此會員資料'}), 404
        
        oldPassword = request.form.get('oldPassword')
        newPassword = request.form.get('newPassword')

        # 進行更新
        if oldPassword:
            if not check_password_hash(client.password, oldPassword):
                return jsonify({'message': '舊密碼輸入錯誤'}), 400
            hashed_password = generate_password_hash(newPassword , method='scrypt')
            client.password = hashed_password
            db.session.commit()
        
        images = request.files.getlist('images')
        # 影像判斷 - 先刪除舊照片再儲存新照片
        if images:
            if client.images:
                for image in client.images:
                    db.session.delete(image)

            # 儲存新的圖片
            for image in images:
                filename = secure_filename(image.filename)
                image_binary = image.read()
                new_image = ClientImage(filename=filename, image_path=image_binary, client_id=client.id)

                db.session.add(new_image)

        db.session.commit()

        # 重新產生新的 Token
        new_token = generate_token(public_id)

        client_data = client_schema.dump(client)

        # 使用自定義方法來獲取解碼的圖片數據，並填充到decoded_images字段中
        decoded_images = []
        for image in client.images:
            if image.image_path:
                image_data = base64.b64encode(image.image_path).decode()
                decoded_images.append(image_data)
        client_data["images"] = decoded_images
        # client_data["decoded_images"] = decoded_images

        return jsonify({
            "token": new_token, 
            "status": 200,
            'message': '更新成功',
            'client_data': client_data
        }), 200
        
    except Exception as e:
        print(e)
        return jsonify({"message": "更新失敗，格式有誤！"}), 400


# ==================  以下後台 API  ================== # 

# 取得全部會員
@client_bp.route('/api/clients', methods=['GET'])
@jwt_required
def get_clients(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        clients = Client.query.filter_by(delete=0).all()

        client_datas = []
        for client in clients:
            # 將照片解析後放回
            decoded_images = []
            for image in client.images:
                if image.image_path:
                    image_data = base64.b64encode(image.image_path).decode()
                    decoded_images.append(image_data)

            client_data = client_schema.dump(client)
            client_data["images"] = decoded_images

            # 將更新後的 client_data 加入 client_datas
            client_datas.append(client_data)

        return jsonify({
            "status": 200,
            "message": "取得所有會員資料成功",
            'client_data': client_datas
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({
            "message": "伺服器忙線中，請稍後再試",
            "status": 503,
            }), 503
    
# 將會員加入黑名單 - delete設為 1
@client_bp.route('/api/setDeleteOne', methods=['POST'])
@jwt_required
def setDeleteClient(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        public_id  = request.json.get('public_id')
        client = Client.query.filter_by(public_id = public_id).first()
        if not client:
            return jsonify({'message': '無此會員資料'}), 404
        
        client.delete = True
        db.session.commit()

        client_data = client_schema.dump(client)

        return jsonify({
            "status": 200,
            'message': '加入黑名單成功',
            'client_data': client_data
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "加入失敗！"}), 400

# 取得所有黑名單的會員
@client_bp.route('/api/delClients', methods=['GET'])
def get_deletedClients():
    try:
        clients = Client.query.filter_by(delete = 1).all()
        
        client_datas = []
        for client in clients:
            # 將照片解析後放回
            decoded_images = []
            for image in client.images:
                if image.image_path:
                    image_data = base64.b64encode(image.image_path).decode()
                    decoded_images.append(image_data)

            client_data = client_schema.dump(client)
            client_data["images"] = decoded_images

            # 將更新後的 client_data 加入 client_datas
            client_datas.append(client_data)

        return jsonify({
            "status": 200,
            'message': '取得黑名單成功',
            'client_data': client_datas
            }), 200
    
    except Exception as e:
        print(e)
        return jsonify({
            "message": "伺服器發生錯誤，請稍後再試",
            "status": 500,
            }), 500

# 取回黑名單的會員
@client_bp.route('/api/retrieveClients', methods=['PATCH'])
@jwt_required
def retrieveClients(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        public_id = request.json.get('public_id')
        client = Client.query.filter_by(public_id = public_id).first()
        if not client:
            return jsonify({'message': '沒有可取回的會員'}), 404

        client.delete = False
        db.session.commit()

        return jsonify({
            "status": 200,
            'message': '會員取回成功',
            'client_data': client_schema.dump(client),
            }), 200
    
    except Exception as e:
        print(e)
        return jsonify({"message": "取回失敗！"}), 400
    

# 確定刪除資料表中的會員資料
@client_bp.route('/api/deleteDataClient/<public_id>', methods=['DELETE'])
# @jwt_required
def deleteDataClient( public_id):
    # if not current_user:
    #     return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        client = Client.query.filter_by(public_id = public_id).first()
        if not client:
            return jsonify({'message': '沒有此會員可以進行刪除'}), 404
        
        client_data = client_schema.dump(client)

        db.session.delete(client)
        db.session.commit()

        return jsonify({
            "status": 200,
            'message': "已從資料庫刪除成功",
            'client_data': client_data
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "刪除失敗！"}), 400
