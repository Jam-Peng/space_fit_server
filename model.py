from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import base64
from datetime import datetime

db = SQLAlchemy()
ma = Marshmallow()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.String(255), unique = True)
    name = db.Column(db.String(100), unique = True, nullable = False)
    password = db.Column(db.String(255), unique = True)
    email = db.Column(db.String(100))
    delete = db.Column(db.Boolean, default = False)
    admin = db.Column(db.Boolean)

    def __init__(self, public_id, name, password, email, admin):
        self.public_id = public_id
        self.name = name
        self.password = password
        self.email = email
        self.admin = admin

class Course(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    course_id = db.Column(db.String(255), unique = True)
    title = db.Column(db.String(100), nullable = False)
    category = db.Column(db.String(100), nullable = False)
    teacher = db.Column(db.String(100), nullable = False)
    class_amount = db.Column(db.String(50), nullable = False)
    open_amount = db.Column(db.String(50), nullable = False)
    price = db.Column(db.Integer, nullable = False)
    description = db.Column(db.Text())
    open_class_date = db.Column(db.DateTime, nullable = True)
    date = db.Column(db.DateTime, default = datetime.now)
    delete = db.Column(db.Boolean, default = False)
    complete = db.Column(db.Boolean)
    user_id = db.Column(db.Integer)
    images = db.relationship('CourseImage', backref = 'course', lazy = True, cascade = 'all, delete-orphan', )

    def __init__(self, course_id, title, category, teacher, class_amount, open_amount,  price, description, open_class_date, complete, user_id):
        self.course_id = course_id
        self.title = title
        self.category = category
        self.teacher = teacher
        self.class_amount = class_amount
        self.open_amount = open_amount
        self.price  = price 
        self.open_class_date  = open_class_date 
        self.description = description
        self.complete = complete
        self.user_id = user_id

class CourseImage(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False)
    image_path = db.deferred(db.Column(db.LargeBinary(length=2**24-1), nullable=False))

    def __init__(self, image_path, course_id):
        self.image_path = image_path
        self.course_id  = course_id 


# 建立序列化(資料庫模式)
class CourseImageSchema(ma.Schema):
    class Meta:
        field = ('id', 'image_path', 'course_id')

    # 解碼照片的二進制格式
    image_path = ma.Method("decode_image_data")
    def decode_image_data(self, obj):
        return base64.b64encode(obj.image_path).decode()

class CourseSchema(ma.Schema):
    images = ma.Nested(CourseImageSchema, many=True)              
    class Meta:
        fields = ('id', 'course_id', 'title', 'category', 'teacher', 'class_amount',
                'open_amount', 'price', 'description', 'complete', 'date', 'delete',
                'images', 'open_class_date')
    open_class_date = ma.DateTime(allow_none = True)  # 允許開課日期先為空值

class AdminSchema(ma.Schema):
    class Meta:
        fields = ('id', 'public_id', 'name', 'password', 'email', 'admin')

admin_schema = AdminSchema()             # 使用單筆資料時的變數
admins_schema = AdminSchema(many=True)   # 使用多筆資料時的變數設定
course_schema = CourseSchema()             
courses_schema = CourseSchema(many=True)
course_image_schema = CourseImageSchema()



# ==================  前台使用者資料模型  ================== # 

class Client(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.String(255), unique = True)
    name = db.Column(db.String(100), unique = True, nullable = False)
    password = db.Column(db.String(255), unique = True)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(100), nullable = True)
    paylod_payment = db.Column(db.Integer, default = 0)
    vip = db.Column(db.Integer)
    images = db.relationship('ClientImage', backref = 'client', lazy = True, cascade = 'all, delete-orphan')
    courses = db.relationship('ClientCourse', backref = 'client', lazy = True, cascade='all, delete-orphan')
    clientorder_id = db.Column(db.Integer, db.ForeignKey('client_order.id', ondelete='CASCADE'), nullable=True)
    date = db.Column(db.DateTime, default = datetime.now)
    delete = db.Column(db.Boolean, default = False)

    def __init__(self, public_id, name, password, email, phone, vip):
        self.public_id = public_id
        self.name = name
        self.password = password
        self.email = email
        self.phone = phone
        self.vip = vip

class ClientImage(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    filename = db.Column(db.String(255), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id', ondelete='CASCADE'), nullable=False)
    image_path = db.deferred(db.Column(db.LargeBinary(length=2**24-1), nullable=False))

    def __init__(self, filename, image_path, client_id):
        self.filename  = filename 
        self.image_path = image_path
        self.client_id  = client_id

class ClientCourse(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.String(255), unique = True)
    course_id = db.Column(db.String(255), unique = False)
    course_title = db.Column(db.String(100), nullable = False)
    course_category = db.Column(db.String(100), nullable = False)
    course_teacher = db.Column(db.String(100), nullable = False)
    course_price = db.Column(db.Integer, nullable = False)
    course_amount = db.Column(db.Integer, nullable = False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id', ondelete='CASCADE'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('client_order.id'))

    def __init__(self, public_id, course_title, course_category, course_teacher, course_price, course_amount, course_id, client_id, order_id):
        self.public_id = public_id
        self.course_id  = course_id 
        self.course_title  = course_title 
        self.course_category  = course_category 
        self.course_teacher  = course_teacher 
        self.course_price  = course_price 
        self.course_amount  = course_amount 
        self.client_id  = client_id 
        self.order_id  = order_id 

# 訂單模型
class ClientOrder(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    order_id = db.Column(db.String(255), unique = True, nullable = False)
    payment_option = db.Column(db.String(255), nullable = False)
    create_date = db.Column(db.DateTime, default = datetime.now)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id', ondelete='CASCADE'), nullable=False)
    current_course = db.relationship('ClientCourse', backref = 'client_order', lazy = True, cascade='all, delete-orphan')
    delete = db.Column(db.Boolean, default = False)

    def __init__(self, order_id, payment_option, client_id):
        self.order_id = order_id
        self.payment_option = payment_option
        self.client_id = client_id


# 建立序列化(資料庫模式)
class ClientImageSchema(ma.Schema):
    class Meta:
        field =('id', 'client_id', 'filename', 'image_path') 

class ClientCourseSchema(ma.Schema):
    class Meta:
        fields = ('id', 'public_id', 'course_id', 'course_title', 'course_category', 'course_teacher', 
                'course_price', 'course_amount', 'client_id', 'order_id')

class ClientSchema(ma.Schema):
    courses = ma.Nested(ClientCourseSchema, many=True)

    # 添加 decoded_images 到 fields 中
    decoded_images = ma.List(ma.String(), dump_only=True)

    # 使用 ma.Method 來定義解碼圖片數據的方法
    images = ma.Nested(ClientImageSchema, many=True)

    # 解析照片的方法移到client_bp中的“更新會員資料” 為了讓'images', 'decoded_images'必須同時存在
    # def decode_images(self, obj):
    #     decoded_images = []
    #     for image in obj.images:
    #         if image.image_path:
    #             image_data = base64.b64encode(image.image_path).decode()
    #             decoded_images.append(image_data)
    #     return decoded_images
    
    class Meta:
        fields = ('id', 'public_id', 'name', 'password', 'email', 'phone', 'date', 'paylod_payment',
                'delete', 'vip', 'clientorder_id', 'courses', 'images', 'decoded_images')
        
class ClientOrderSchema(ma.Schema):
    client = ma.Nested(ClientSchema, many=True)
    current_course = ma.Nested(ClientCourseSchema, many=True)

    class Meta:
        fields = ('id', 'order_id', 'payment_option', 'create_date', 'client_id', 'current_course', 'delete') 
        

client_schema = ClientSchema()             
clients_schema = ClientSchema(many=True)
client_course_schema = ClientCourseSchema()
client_image_schema = ClientImageSchema()
client_order_schema = ClientOrderSchema()
clients_order_schema = ClientOrderSchema(many=True)

