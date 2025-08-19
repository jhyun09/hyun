from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db
from datetime import datetime, timedelta, timezone
from flask_login import login_user, logout_user, current_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

MAX_ATTEMPTS = 5
LOCK_TIME_MINUTES = 5  # 잠금 시간 설정
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        now = datetime.now(timezone.utc)

        user = User.query.filter_by(username=username).first()

        # 사용자 존재 여부 먼저 확인
        if not user:
            flash("❌ 사용자 정보가 올바르지 않습니다.")
            return redirect(url_for("auth.login"))

        # 관리자 제외하고 잠금 여부 확인
        if not user.is_admin:
            lock_until = session.get("lock_until")
            if lock_until:
                if isinstance(lock_until, str):
                    lock_until = datetime.strptime(lock_until, DATETIME_FORMAT)
                if now < lock_until:
                    remaining = int((lock_until - now).total_seconds() // 60) + 1
                    flash(f"🔒 {remaining}분 후 다시 시도하세요.")
                    return redirect(url_for("auth.login"))

        # 비밀번호 확인
        if not check_password_hash(user.password_hash, password):
            session["failed_attempts"] = session.get("failed_attempts", 0) + 1
            if session["failed_attempts"] >= MAX_ATTEMPTS:
                lock_until = now + timedelta(minutes=LOCK_TIME_MINUTES)
                session["lock_until"] = lock_until.strftime(DATETIME_FORMAT)
                flash(f"❌ {LOCK_TIME_MINUTES}분간 잠깁니다.")
            else:
                left = MAX_ATTEMPTS - session["failed_attempts"]
                flash(f"❌ 남은 시도 횟수: {left}회")
            return redirect(url_for("auth.login"))

        # 승인 여부 확인
        if not user.is_approved and not user.is_admin:
            flash("🙅‍♂️ 관리자 승인이 필요합니다.")
            return redirect(url_for("auth.login"))

        # 로그인 성공
        session.clear()
        login_user(user, remember=True)

        # ✅ 관리자 여부 세션에 저장
        session["user_id"] = user.id
        session["username"] = user.username
        session["is_admin"] = user.is_admin

        return redirect(url_for("post.home"))

    return render_template("login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            flash("❗ 비밀번호 불일치")
            return redirect(url_for("auth.signup"))

        if User.query.filter_by(username=username).first():
            flash("❗ 이미 존재하는 사용자")
            return redirect(url_for("auth.signup"))

        hashed = generate_password_hash(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed,
            is_admin=False,
            is_approved=False
        )
        db.session.add(user)
        db.session.commit()
        flash("🎉 회원가입 완료! 관리자 승인 대기 중")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    session.clear()
    flash("👋 로그아웃 완료")
    return redirect(url_for("home"))