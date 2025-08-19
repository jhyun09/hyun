import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, redirect, url_for, render_template
from models import db, User, Post, Comment, Category
from routes import post_bp
from auth import auth_bp
from admin import admin_bp
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import current_user
from flask_login import LoginManager
from extensions import db, login_manager
from routes_account import account_bp


import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app = Flask(__name__, static_folder='static', template_folder='templates')
csrf = CSRFProtect(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///board.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = 'my_secret_key' # ✅ 반드시 고정된 값이어야 함



db.init_app(app)
app.register_blueprint(account_bp)

migrate = Migrate(app, db)

# 로그인 매니저 설정
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"  # 로그인하지 않았을 때 이동할 뷰

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ Jinja 템플릿 필터 등록
@app.template_filter("regex_search")
def regex_search(value, pattern, group=0):
    match = re.search(pattern, value)
    return match.group(group) if match else ""

# ✅ 라우트: 홈으로 접근 시 자유게시판으로 이동
@app.route("/")
def home():
    all_categories = Category.query.order_by(Category.name).all()
    default_names = ['자유 게시판', '이야기 게시판', '사진 게시판', '습작 게시판', '쭈야 게시판']

    # 갤러리 게시판 카테고리 목록
    gallery_categories_names = ['사진 게시판', '습작 게시판', '쭈야 게시판']

    # 기본 카테고리 (갤러리 게시판 포함)
    default_categories = [c for c in all_categories if c.name in default_names]

    # 갤러리 카테고리에 해당하는 카테고리들만 따로 구분
    gallery_categories = [c for c in all_categories if c.name in gallery_categories_names]

    # 사용자 정의 카테고리
    custom_categories = [c for c in all_categories if c.name not in default_names]

    return render_template("main.html", 
                           default_categories=default_categories, 
                           custom_categories=custom_categories, 
                           gallery_categories=gallery_categories)

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# 블루프린트 등록
app.register_blueprint(admin_bp)
app.register_blueprint(post_bp)
app.register_blueprint(auth_bp)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

__all__ = ['app', 'db', 'User', 'Post', 'Comment', 'Category']
