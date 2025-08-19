from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin
from extensions import db

# ✅ SQLite 호환을 위한 naming_convention 추가
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)


# 📝 게시글
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_post_author_id_user'))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    read_count = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', name='fk_post_category_id_category'))
    comments = db.relationship('Comment', backref='post', cascade='all, delete-orphan', lazy=True)
    attachment = db.Column(db.String(255))
    attachment_original = db.Column(db.String(255))
    file_path = db.Column(db.String(255))

    # ✅ 작성자 관계 추가
    author = db.relationship('User', backref='posts')

    def __repr__(self):
        return f"<Post {self.id} | {self.title}>"

# 💬 댓글
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_comment_author_id_user'))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', name='fk_comment_post_id_post'))

    def __repr__(self):
        return f"<Comment {self.id} | post_id={self.post_id}>"

# 📂 카테고리
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.String(20), default="text")
    is_custom = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='category', lazy=True)

    def __repr__(self):
        return f"<Category {self.name}>"
    
# 👤 사용자
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bio = db.Column(db.Text)  # 👈 소개 필드 추가!

    comments = db.relationship('Comment', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.id} | {self.username}>"