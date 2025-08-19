from app import app, db
from models import User  # 👍 여기서 직접 User 모델을 불러오기
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():  # ✅ 애플리케이션 컨텍스트 설정
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='hyun',
                email='hyun@example.com',
                password_hash=generate_password_hash('thk0567'),
                is_admin=True,
                is_approved=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ 관리자 계정 생성 완료!")
        else:
            print("ℹ️ 관리자 계정이 이미 존재합니다.")

create_admin()