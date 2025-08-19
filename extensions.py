from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import MetaData

# ✅ naming_convention 설정
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)

# ✅ 확장 기능 인스턴스 생성
db = SQLAlchemy(metadata=metadata)
login_manager = LoginManager()

# ✅ 선택적 설정
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'