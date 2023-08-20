from flask import Blueprint
from flask import request, jsonify
from decorators import jwt_required
from model import db, Client, ClientOrder, client_schema, client_order_schema, clients_order_schema
from datetime import datetime

echart_bp = Blueprint('echart_bp', __name__)


# 取得所有訂單分類的購買次數、價錢資料 - 這是累加所有的資料
@echart_bp.route('/api/payload_all_orders', methods=['GET'])
def payload_datas():
    try:
        # 查詢所有訂單，並取得相關的課程資料
        orders = ClientOrder.query.all()
        course_stats = {}  # 用於儲存課程統計數據
        
        for order in orders:
            for course in order.current_course:
                category = course.course_category
                price = course.course_price
                
                # 初始化課程類別的統計數據
                if category not in course_stats:
                    # course_stats[category] = {'count': 0, 'total_price': 0}   (沒有取出每個類別的課程)
                    course_stats[category] = {'count': 0, 'total_price': 0, 'courses': {}}
                
                # 更新統計數據 (沒有取出每個類別的課程)
                # course_stats[category]['count'] += 1
                # course_stats[category]['total_price'] += price

                # 更新課程數據
                if course.course_title not in course_stats[category]['courses']:
                    course_stats[category]['courses'][course.course_title] = {'count': 0, 'total_price': 0}

                # 更新統計數據
                course_stats[category]['count'] += 1
                course_stats[category]['total_price'] += price
                course_stats[category]['courses'][course.course_title]['count'] += 1
                course_stats[category]['courses'][course.course_title]['total_price'] += price

        return jsonify({
            "status": 200,
            "message": "取得訂單統計數據成功",
            "course_stats": course_stats
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({"message": "獲取訂單統計數據失敗"}), 500
    

# 取得當前日期所有訂單分類的購買次數、價錢資料 - 這條 API 棄用，改用下面有統計每個類別的課程
# @echart_bp.route('/api/current_orders', methods=['GET'])
# def current_data():
#     try:
#         current_date = datetime.now().date()  # 當日的日期（不包含時間部分）
        
#         # 查詢當日的訂單，並取得相關的課程資料
#         orders = ClientOrder.query.filter(ClientOrder.create_date >= current_date).all()
#         course_stats = {}  # 用於儲存課程統計數據
        
#         for order in orders:
#             for course in order.current_course:
#                 category = course.course_category
#                 price = course.course_price
                
#                 # 初始化課程類別的統計數據
#                 if category not in course_stats:
#                     course_stats[category] = {'count': 0, 'total_price': 0}
                
#                 # 更新統計數據
#                 course_stats[category]['count'] += 1
#                 course_stats[category]['total_price'] += price
        
#         return jsonify({
#             'date': current_date.strftime('%Y-%m-%d'),  # 將日期格式化為字符串
#             'course_statistics': course_stats
#         }), 200
    
#     except Exception as e:
#         print(e)
#         return jsonify({"message": "獲取課程統計數據失敗"}), 500
    

# 取得 "當前日期" 所有訂單分類的購買次數、價錢資料 (細分所有課程)
@echart_bp.route('/api/current_allorders', methods=['GET'])
def get_current_data():
    try:
        current_date = datetime.now().date()  # 當日的日期（不包含時間部分）
        
        # 查詢當日的訂單，並取得相關的課程資料
        orders = ClientOrder.query.filter(ClientOrder.create_date >= current_date).all()
        course_stats = {}  # 用於儲存課程統計數據
        
        for order in orders:
            for course in order.current_course:
                category = course.course_category
                price = course.course_price
                
                # 初始化課程類別的統計數據
                if category not in course_stats:
                    course_stats[category] = {'count': 0, 'total_price': 0, 'courses': {}}
                
                # 更新課程數據
                if course.course_title not in course_stats[category]['courses']:
                    course_stats[category]['courses'][course.course_title] = {'count': 0, 'total_price': 0}
                
                # 更新統計數據
                course_stats[category]['count'] += 1
                course_stats[category]['total_price'] += price
                course_stats[category]['courses'][course.course_title]['count'] += 1
                course_stats[category]['courses'][course.course_title]['total_price'] += price
        
        return jsonify({
            'date': current_date.strftime('%Y-%m-%d'),  # 將日期格式化為字符串
            'course_statistics': course_stats
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({"message": "獲取課程統計數據失敗"}), 500




# 根據查詢日期取得當天所有訂單分類的購買次數、價錢資料 (前端api `/api/search_date_orders?date=${dateParam}`)
@echart_bp.route('/api/search_date_orders', methods=['GET'])
def search_date_data():
    try:
        date_param = request.args.get('date')  # 從客戶端獲取日期參數
        if not date_param:
            return jsonify({"message": "沒有取得要查詢的日期"}), 400
        
        # 將日期參數轉換為 datetime 對象
        target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        
        # 查詢指定日期的訂單，並取得相關的課程資料
        orders = ClientOrder.query.filter(ClientOrder.create_date >= target_date).all()
        course_stats = {}  # 用於儲存課程統計數據
        
        for order in orders:
            for course in order.current_course:
                category = course.course_category
                price = course.course_price
                
                # 初始化課程類別的統計數據
                if category not in course_stats:
                    course_stats[category] = {'count': 0, 'total_price': 0}
                
                # 更新統計數據
                course_stats[category]['count'] += 1
                course_stats[category]['total_price'] += price
        
        return jsonify({
            'date': target_date.strftime('%Y-%m-%d'),  # 將日期格式化為字符串
            'course_statistics': course_stats
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({"message": "獲取課程統計數據失敗"}), 500
    

# 根據查詢日期取得當天所有訂單分類的購買次數、價錢資料 (細分其他課程)
@echart_bp.route('/api/search_date_allorder', methods=['GET'])
def search_date_alldata():
    try:
        date_param = request.args.get('date')  # 從客戶端獲取日期參數
        if not date_param:
            return jsonify({"message": "沒有取得要查詢的日期"}), 400
        
        # 將日期參數轉換為 datetime 對象
        target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        
        # 查詢指定日期的訂單，並取得相關的課程資料
        orders = ClientOrder.query.filter(ClientOrder.create_date >= target_date).all()
        course_stats = {}  # 用於儲存課程統計數據
        
        for order in orders:
            for course in order.current_course:
                category = course.course_category
                price = course.course_price
                
                # 初始化課程類別的統計數據
                if category not in course_stats:
                    course_stats[category] = {'count': 0, 'total_price': 0, 'courses': {}}
                
                # 更新課程數據
                if course.course_title not in course_stats[category]['courses']:
                    course_stats[category]['courses'][course.course_title] = {'count': 0, 'total_price': 0}
                
                # 更新統計數據
                course_stats[category]['count'] += 1
                course_stats[category]['total_price'] += price
                course_stats[category]['courses'][course.course_title]['count'] += 1
                course_stats[category]['courses'][course.course_title]['total_price'] += price
        
        return jsonify({
            'date': target_date.strftime('%Y-%m-%d'),  # 將日期格式化為字符串
            'course_statistics': course_stats
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({"message": "獲取課程統計數據失敗"}), 500


# ============================================

