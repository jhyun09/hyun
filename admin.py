from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from models import Post, Comment, User, Category, db
from werkzeug.security import generate_password_hash
from functools import wraps
from forms import DeleteUsersForm, AddCategoryForm, DeleteCategoryForm, EditCategoryForm, AdminForm, DeleteCommentForm, DeletePostForm
from flask import jsonify
from forms import AddCategoryForm, DeleteCategoryForm, EditCategoryForm


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 관리자 권한 체크
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            flash('관리자만 접근할 수 있습니다.')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# IP 제한
def ip_restricted(allowed_prefixes):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = request.remote_addr
            if not any(client_ip.startswith(prefix) for prefix in allowed_prefixes):
                flash(f'허용되지 않은 IP({client_ip})에서의 접근입니다.')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

# 관리자 대시보드
@admin_bp.route('/')
@admin_required
@ip_restricted(['127.', '192.168.'])
def admin_dashboard():
    add_form = AddCategoryForm()
    delete_form = DeleteCategoryForm()
    edit_form = EditCategoryForm()
    delete_users_form = DeleteUsersForm()
    delete_post_form = DeletePostForm()
    delete_comment_form = DeleteCommentForm()

    master_form = AdminForm()
    reject_form = AdminForm()
    
    categories = Category.query.order_by(Category.name).all()
    selected_category = request.args.get('category', '전체')

    if selected_category == '전체':
        posts = Post.query.order_by(Post.id.desc()).all()
    else:
        category_obj = Category.query.filter_by(name=selected_category).first()
        posts = Post.query.filter_by(category_id=category_obj.id).order_by(Post.id.desc()).all()

    post_ids = [p.id for p in posts]
    comments = Comment.query.filter(Comment.post_id.in_(post_ids)).order_by(Comment.id.desc()).all()
    pending_users = User.query.filter_by(is_approved=False).order_by(User.created_at.desc()).all()
    all_users = User.query.order_by(User.created_at.desc()).all()

    return render_template('admin_dashboard.html',
                           posts=posts,
                           comments=comments,
                           categories=categories,
                           selected_category=selected_category,
                           pending_users=pending_users,
                           users=all_users,
                           form=master_form,  # 마스터 계정 및 거절 버튼에 넘김
                           add_form=add_form,
                           delete_form=delete_form,
                           edit_form=edit_form,
                           delete_users_form=delete_users_form)



# 비밀번호 변경
@admin_bp.route('/change_password', methods=['GET', 'POST'])
@admin_required
@ip_restricted(['127.', '192.168.'])
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')

        user_id = session.get('user_id')
        user = User.query.get(user_id)

        if not user or not user.check_password(current_pw):
            flash('현재 비밀번호가 올바르지 않습니다.')
            return redirect(url_for('admin.change_password'))

        if new_pw != confirm_pw:
            flash('새 비밀번호와 확인 비밀번호가 일치하지 않습니다.')
            return redirect(url_for('admin.change_password'))

        user.password_hash = generate_password_hash(new_pw)
        db.session.commit()
        flash('비밀번호가 성공적으로 변경되었습니다.')
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin_change_password.html')

# 게시판 추가
@admin_bp.route('/add_category', methods=['POST'])
@admin_required
@ip_restricted(['127.', '192.168.'])
def add_category():
    name = request.form.get('category_name')
    category_type = request.form.get('category_type')

    if not name:
        flash('게시판 이름을 입력하세요.')
        return redirect(url_for('admin.admin_dashboard'))

    if Category.query.filter_by(name=name).first():
        flash('이미 존재하는 게시판입니다.')
        return redirect(url_for('admin.admin_dashboard'))

    new_category = Category(name=name, type=category_type)
    db.session.add(new_category)
    db.session.commit()
    flash(f'{name} 게시판이 추가되었습니다.')
    return redirect(url_for('admin.admin_dashboard'))

# 게시판 삭제
@admin_bp.route('/delete_category', methods=['POST'])
@admin_required
@ip_restricted(['127.', '192.168.'])
def delete_category():
    cat_id = request.form.get('category_id')
    category = Category.query.get(cat_id)

    if not category:
        flash('해당 게시판이 존재하지 않습니다.')
        return redirect(url_for('admin.admin_dashboard'))

    Post.query.filter_by(category_id=cat_id).delete()
    db.session.delete(category)
    db.session.commit()
    flash(f"'{category.name}' 게시판이 삭제되었습니다.")
    return redirect(url_for('admin.admin_dashboard'))

# 게시판 타입 수정
@admin_bp.route('/edit_category', methods=['POST'])
@admin_required
@ip_restricted(['127.', '192.168.'])
def edit_category():
    category_id = request.form.get('category_id')
    category_type = request.form.get('category_type')
    category = Category.query.get(category_id)

    if category:
        category.type = category_type
        db.session.commit()
        flash(f"{category.name} 타입이 '{category_type}'로 변경되었습니다.")
    else:
        flash("해당 게시판이 존재하지 않습니다.")
    return redirect(url_for('admin.admin_dashboard'))

# 사용자 승인 처리
from flask import jsonify  # 꼭 import 추가!

@admin_bp.route('/approve_user/<int:user_id>', methods=['POST'])
@admin_required
@ip_restricted(['127.', '192.168.'])
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    return jsonify(success=True)

# 사용자 거절 (삭제)
@admin_bp.route('/reject_user/<int:user_id>', methods=['POST'])
@admin_required
@ip_restricted(['127.', '192.168.'])
def reject_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'{user.email} 사용자 가입이 거절되었습니다.')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/set_master_account/<int:user_id>', methods=['POST'])
@admin_required
@ip_restricted(['127.', '192.168.'])
def set_master_account(user_id):
    user = User.query.get_or_404(user_id)

    if user.is_admin:
        flash(f"{user.username}은(는) 이미 관리자입니다.")
    else:
        user.is_admin = True
        db.session.commit()
        flash(f"{user.username}을(를) 관리자(마스터 계정)로 지정했습니다.")

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/delete_users', methods=['POST'])
@admin_required
@ip_restricted(['127.', '192.168.'])
def delete_users():
    ids_to_delete = request.form.getlist('delete_ids')

    if ids_to_delete:
        users = User.query.filter(User.id.in_(ids_to_delete)).all()
        for user in users:
            if user.is_admin:
                continue  # 관리자 계정은 삭제 방지
            db.session.delete(user)
        db.session.commit()
        flash(f"{len(ids_to_delete)}명 삭제 완료!")
    else:
        flash("삭제할 계정을 선택하세요.")

    return redirect(url_for('admin.admin_dashboard'))


# 회원가입 승인 필터
@admin_bp.route('/bulk_action', methods=['POST'])
@admin_required
@ip_restricted(['127.', '192.168.'])
def bulk_action():
    data = request.get_json()
    action = data.get('action')
    user_ids = data.get('user_ids', [])

    if not action or not user_ids:
        return jsonify(success=False, error="잘못된 요청입니다."), 400

    updated = 0
    for uid in user_ids:
        user = User.query.get(uid)
        if not user:
            continue

        if action == 'approve':
            user.is_approved = True
        elif action == 'reject':
            db.session.delete(user)
        elif action == 'master':
            user.is_admin = True
        updated += 1

    db.session.commit()
    return jsonify(success=True, updated=updated)