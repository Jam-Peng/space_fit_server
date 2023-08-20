import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from model import db, ma
from admin_bp import admin_bp
from course_bp import course_bp
from client_bp import client_bp
from order_bp import order_bp
from echart_bp import echart_bp

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
HOST = os.getenv('HOST')
DB_USER = os.getenv('DB_USER')
DB_PWD = os.getenv('DB_PWD')
DB_NAME = os.getenv('DB_NAME')

app = Flask(__name__)
# CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:5173"}})
CORS(app)

# 初始化 SQLAlchemy
app.config["SECRET_KEY"] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PWD}@{HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)
ma.init_app(app)

# 註冊藍圖
app.register_blueprint(admin_bp)
app.register_blueprint(course_bp)
app.register_blueprint(client_bp)
app.register_blueprint(order_bp)
app.register_blueprint(echart_bp)

# 解決上下文問題
with app.app_context():
    db.create_all()


if __name__=='__main__':
    app.run(debug=False)