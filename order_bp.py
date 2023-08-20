from flask import Blueprint
from flask import request, jsonify
import uuid
from decorators import client_jwt_required, jwt_required
from model import db, ClientCourse, ClientOrder, Client, ClientCourse \
    , client_schema, client_order_schema, client_course_schema, clients_order_schema
from client_bp import generate_token
import base64

order_bp = Blueprint('order_bp', __name__)


# 新增訂單
@order_bp.route('/client/order/<public_id>/api/v1', methods=['POST'])
@client_jwt_required
def add_orders(current_user, public_id):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        datas = request.get_json()
        orders = datas.get('order')
        option = datas.get('payment_option')

        user = Client.query.filter_by(public_id = public_id).first()

        # 建立訂單
        order_id = str(uuid.uuid4().hex)
        order = ClientOrder(
            order_id = order_id,
            payment_option = option,
            client_id = user.id,
        )
        db.session.add(order)
        db.session.commit()

        # 儲存課程到使用者的 ClientCourse 模型內
        purchased_courses = []  # 用於儲存所購買的課程
        current_courses = []  # 用於儲存目前的課程（訂單內的課程）

        for order_data in orders:
            course = ClientCourse(
                public_id = str(uuid.uuid4().hex),
                course_title = order_data['title'],
                course_category = order_data['category'],
                course_teacher = order_data['teacher'],
                course_price = order_data['price'],
                course_amount = order_data['amount'],
                course_id = order_data['course_id'],
                client_id = current_user.id,
                order_id = order.id,
            )
            user.paylod_payment += order_data['price']  # 累計當前使用者購買的金額
            db.session.add(course)
            purchased_courses.append(course)  # 將課程添加到所購買的課程列表中
            current_courses.append(course)    # 將課程添加到目前的課程列表中

        if user.paylod_payment >= 10000:
            user.vip = 1
        else:
            user.vip = 0

        db.session.commit()

        # 每次訂單的課程都會去替換之前的當前課程 
        order.current_course = current_courses
        db.session.add(order)
        db.session.commit()


        # 使用序列化器將數據轉換成適當格式
        client_data = client_schema.dump(user)          
        # 將目前購買的課程資料新增一個新屬性到使用者資料中 (這個屬性只存在localStorage)
        purchased_courses_data = client_course_schema.dump(purchased_courses, many=True)
        client_data['purchased_courses'] = purchased_courses_data


        # 取得訂單資料
        order_data = client_order_schema.dump(order)
        # 取得與訂單關聯的使用者資料
        order_client_data = client_schema.dump(client_data)
        # 將訂單的使用者資料指定給 order_data 的 client 屬性
        order_data['client'] = order_client_data

        # 修正客戶大頭照的影像資料來源
        decoded_images = []
        for image in user.images:
            if image.image_path:
                image_data = base64.b64encode(image.image_path).decode()
                decoded_images.append(image_data)
        client_data["images"] = decoded_images

        # 重新產生新的 Token
        new_token = generate_token(public_id)

        return jsonify({
            "token": new_token, 
            "status": 200,
            "message": "新增訂單成功",
            "client_data": client_data,
            "order": order_data,
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({
            "message": "伺服器維修中，請稍後再試",
            "status": 503,
            }), 503
    

# 取得使用者的訂單
@order_bp.route('/client/orders/api/v1', methods=['POST'])
@client_jwt_required
def getAllOrders(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        client_id = request.json.get('client_id')

        orders = ClientOrder.query.filter_by(client_id=client_id, delete=0).all()

        order_datas = clients_order_schema.dump(orders)

        for order_data in order_datas:
            user = Client.query.filter_by(id = order_data['client_id']).first()
            # 將照片解析後放回
            decoded_images = []
            for image in user.images:
                if image.image_path:
                    image_data = base64.b64encode(image.image_path).decode()
                    decoded_images.append(image_data)

            # 序列化資料
            client_data = client_schema.dump(user)  
            client_data["images"] = decoded_images
            order_data['client'] = client_data

        return jsonify({
            "status": 200,
            "message": "取得訂單成功",
            "orders": order_datas
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({
            "message": "伺服器維修中，請稍後再試",
            "status": 503,
            }), 503
    

# ==================  以下後台 API  ================== # 

# 取得全部訂單
@order_bp.route('/api/orders', methods=['GET'])
@jwt_required
def get_orders(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        orders = ClientOrder.query.all()
        order_datas = clients_order_schema.dump(orders)

        for order_data in order_datas:
            user = Client.query.filter_by(id = order_data['client_id']).first()
            # 將照片解析後放回
            decoded_images = []
            for image in user.images:
                if image.image_path:
                    image_data = base64.b64encode(image.image_path).decode()
                    decoded_images.append(image_data)

            # 序列化資料
            client_data = client_schema.dump(user)  
            client_data["images"] = decoded_images
            order_data['client'] = client_data

        return jsonify({
            "status": 200,
            "message": "取得訂單成功",
            "orders": order_datas
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({
            "message": "伺服器維修中，請稍後再試",
            "status": 503,
            }), 503

# 刪除訂單
@order_bp.route('/api/deleteorder', methods=['DELETE'])
@jwt_required
def delete_order_one(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        order_id = request.json.get('order_id')
        order = ClientOrder.query.filter_by(order_id = order_id).first()
        if not order:
            return jsonify({'message': '查無訂單可以進行刪除'}), 404
        
        order_datas = client_order_schema.dump(order)

        # 在刪除訂單之前獲取關聯的會員
        client_id = order.client_id

        if client_id:
            client = Client.query.get(client_id)
            if client:
                # 扣除訂單中所有課程金額
                total_course_amount = sum(course.course_price for course in order.current_course)
                client.paylod_payment -= total_course_amount
                db.session.commit()

        if client.paylod_payment >= 10000:
            client.vip = 1
        else:
            client.vip = 0
            
        db.session.delete(order)
        db.session.commit()

        return jsonify({
            "status": 200,
            'message': "已從資料庫刪除成功",
            'orders': order_datas
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({"message": "刪除失敗！"}), 400
    