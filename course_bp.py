from flask import Blueprint
from flask import request, jsonify, current_app
import uuid
import os
from werkzeug.utils import secure_filename
from decorators import jwt_required
from model import db, Course, CourseImage, course_schema, courses_schema 

course_bp = Blueprint('course_bp', __name__)


# 新增課程
@course_bp.route('/api/addCourse', methods=['POST'])
@jwt_required
def add_course(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        title = request.form['title']
        category = request.form['category']
        teacher = request.form['teacher']
        class_amount = request.form['class_amount']
        open_amount = request.form['open_amount']
        price = int(request.form['price'])
        description = request.form['description']
        open_class_date = request.form['open_class_date']

        # 儲存課程資料到資料庫
        course = Course(course_id = str(uuid.uuid4().hex), 
                        title = title, 
                        category = category,
                        teacher = teacher,
                        class_amount = class_amount,
                        open_amount = open_amount,
                        price = price,
                        description = description,
                        complete = False,
                        user_id = current_user.id,
                        open_class_date = open_class_date
                        )
        db.session.add(course)
        db.session.commit()

        # 儲存課程照片資料到資料庫
        images = request.files.getlist('images')
        
        dir_path = os.getcwd()+'/uploads'
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        for i, image in enumerate(images):
            filename = secure_filename(image.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{course.id}_{i + 1}_{filename}")
            image.save(file_path)

            with open(file_path, 'rb') as f:
                image_data = f.read()

            course_image = CourseImage(course_id = course.id, image_path = image_data)
            db.session.add(course_image)

        db.session.commit()

        return jsonify({
            "status": 201,
            'message': '新增成功',
            'courses': course_schema.dump(course),
            }), 201
    except Exception as e:
        print(e)
        return jsonify({"message": "新增失敗，格式有誤！"}), 400


# 取得所有的課程和照片，並篩選 delete 屬性不為 False 的資料
@course_bp.route('/api/courses', methods=['GET'])
def get_courses():
    try:
        products = Course.query.filter_by(delete=0).all()
        result = courses_schema.dump(products)

        return jsonify({
            "courses":result,
            "status": 200,
            }), 200
    except Exception as e:
        return jsonify({
            "message": "伺服器發生錯誤，請稍後再試",
            "status": 500,
            }), 500
    

# 更新課程
@course_bp.route('/api/updateCourse/<course_id>', methods=['PUT'])
@jwt_required
def update_course(current_user, course_id):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401

    try:
        course = Course.query.filter_by(course_id = course_id).first()
        if not course:
            return jsonify({'message': '無法更新課程'}), 404

        title = request.form['title']
        category = request.form['category']
        teacher = request.form['teacher']
        class_amount = request.form['class_amount']
        open_amount = request.form['open_amount']
        price = int(request.form['price'])
        description = request.form['description']
        open_class_date = request.form['open_class_date']
        complete_str  = request.form['complete']
        complete_bool = complete_str.lower() == 'true'   # 將字串轉成布林值

        # 儲存課程資料到資料庫
        course.title = title
        course.category = category
        course.teacher = teacher
        course.class_amount = class_amount
        course.open_amount = open_amount
        course.price = price
        course.description = description
        course.open_class_date = open_class_date
        course.complete = complete_bool
        
        db.session.commit()

        # 儲存更新的照片資料到資料庫
        images = request.files.getlist('images')

        dir_path = os.getcwd()+'/uploads'
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        if images :
            # 先刪除舊有的照片
            old_images = course.images
            for old_image in old_images:
                db.session.delete(old_image)
            
            # 將新的照片存入資料庫
            for i, image in enumerate(images):
                filename = secure_filename(image.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{course.id}_{i + 1}_{filename}")
                image.save(file_path)

                with open(file_path, 'rb') as f:
                    image_data = f.read()
                course_image = CourseImage(course_id = course.id, image_path = image_data)
                db.session.add(course_image)

            db.session.commit()

        return jsonify({
            "status": 200,
            'message': '更新成功',
            'courses': course_schema.dump(course),
            }), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "更新失敗，格式有誤！"}), 400


# 更新單一課程的啟用功能
@course_bp.route('/api/updateCourseCheckbox/<course_id>', methods=['PATCH'])
@jwt_required
def updateCourseCheckbox(current_user, course_id):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        course = Course.query.filter_by(course_id = course_id).first()
        if not course:
            return jsonify({'message': '功能發生異常，請使用編輯功能來啟用'}), 500

        complete = request.json.get('complete')
        if complete == True:
            complete = False
        else:
            complete = True

        course.complete = complete
        db.session.commit()

        return jsonify({
            "status": 200,
            'message': '更新成功',
            'courses': course_schema.dump(course),
            }), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "更新失敗！"}), 400


# 刪除單一課程 - 將 delete 屬性更新為 1
@course_bp.route('/api/predeleteCourse', methods=['POST'])
@jwt_required
def preDeleteCourse(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        course_id = request.json.get('course_id')
        course = Course.query.filter_by(course_id = course_id).first()
        if not course:
            return jsonify({'message': '無法刪除課程'}), 404
        
        course.delete = True
        db.session.commit()
        return jsonify({
            "status": 200,
            'message': '刪除成功',
            'courses': course_schema.dump(course),
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "更新失敗！"}), 400


# 取得所有被刪除的課程和照片，篩選 delete 屬性為 True 的資料
@course_bp.route('/api/delCourses', methods=['GET'])
def get_deletedCourse():
    try:
        products = Course.query.filter_by(delete = 1).all()
        result = courses_schema.dump(products)

        return jsonify({
            'message': '',
            "courses":result,
            "status": 200,
            }), 200
    except Exception as e:
        print(e)
        return jsonify({
            "message": "伺服器發生錯誤，請稍後再試",
            "status": 500,
            }), 500


# 取回被刪除的課程
@course_bp.route('/api/retrieveCourses', methods=['PATCH'])
@jwt_required
def retrieveCourses(current_user):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        course_id = request.json.get('course_id')
        course = Course.query.filter_by(course_id = course_id).first()
        if not course:
            return jsonify({'message': '沒有可取回的課程'}), 404

        course.delete = False
        db.session.commit()

        return jsonify({
            "status": 200,
            'message': '課程取回成功',
            'courses': course_schema.dump(course),
            }), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "取回失敗！"}), 400


# 確定刪除資料表中的資料
@course_bp.route('/api/deleteDataCourse/<course_id>', methods=['DELETE'])
@jwt_required
def deleteDataCourse(current_user, course_id):
    if not current_user:
        return jsonify({'message': '沒有使用權限'}), 401
    
    try:
        course = Course.query.filter_by(course_id = course_id).first()
        if not course:
            return jsonify({'message': '沒有此課程可以進行刪除'}), 404
        
        result = course_schema.dump(course)

        db.session.delete(course)
        db.session.commit()
        return jsonify({
            "status": 200,
            'message': "已從資料庫刪除成功",
            'courses': result
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "刪除失敗！"}), 400


# ==================  以下前台 API  ================== # 

# 取得所有的課程和照片，並篩選 delete 屬性不為 0 和 complete 為 1 的資料
@course_bp.route('/client/courses/api/v1', methods=['GET'])
def client_get_courses():
    try:
        courses = Course.query.filter_by(delete = 0, complete = 1).all()
        result = courses_schema.dump(courses)

        return jsonify({
            "status": 200,
            "courses":result,
            }), 200
    
    except Exception as e:
        return jsonify({
            "message": "伺服器發生錯誤，請稍後再試",
            "status": 500,
            }), 500
