from flask import (
    Blueprint, render_template, request, jsonify, redirect,
    url_for, session, flash, g, current_app, send_from_directory
)
from models import db, Post, Comment, Category, User
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_login import current_user
from forms import (
    PostForm, EditCommentForm, AdminForm, DeleteUsersForm,
    DeletePostForm, DeleteCommentForm, AddCategoryForm, EditCategoryForm
)
from sqlalchemy.orm import joinedload
from werkzeug.security import check_password_hash
import os
from functools import wraps
import html
import re
from flask_wtf.csrf import generate_csrf



post_bp = Blueprint("post", __name__, url_prefix="/post")


# 로그인 + 승인 여부 확인 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        user = User.query.get(user_id)
        if not user_id or not user or (not user.is_approved and not user.is_admin):
            flash("승인된 회원만 이용 가능합니다.")
            return redirect(url_for("auth.login"))
        g.user = user  # g.user에 유저 객체 세팅
        return f(*args, **kwargs)
    return decorated_function


# 로그인 후 메인페이지
@post_bp.route("/home", endpoint="home")
def home():
    custom_categories = Category.query.filter_by(is_custom=True).all()
    default_categories = Category.query.filter_by(is_custom=False).all()
    return render_template(
        "main.html",
        custom_categories=custom_categories,
        default_categories=default_categories
    )


# 게시글 목록
@post_bp.route("/<category>")
@post_bp.route("/<category>/page/<int:page>")
@login_required
def index(category="자유게시판", page=1):
    q = request.args.get("q", "")
    per_page = 12
    query = Post.query.join(Category).filter(Category.name == category)

    if q:
        search = f"%{q}%"
        query = query.filter(Post.title.like(search))

    posts = query.order_by(Post.id.desc()).paginate(page=page, per_page=per_page)
    category_objects = {c.name: c for c in Category.query.all()}
    category_obj = category_objects.get(category)
    category_type = category_obj.type if category_obj else "text"
    is_gallery_category = category_obj.type == "photo" if category_obj else False

    for post in posts.items:
        decoded_content = html.unescape(post.content or "")
        match = re.search(r'<img[^>]+src=["\']?([^"\'>]+)["\']?', decoded_content)
        post.first_img_src = match.group(1) if match else None

    return render_template("index.html", posts=posts, category=category,
                           category_type=category_type,
                           is_gallery_category=is_gallery_category,
                           q=q,
                           category_objects=category_objects,
                           start_page=max(page - 5, 1),
                           end_page=min(page + 4, posts.pages))


# 글 작성
@post_bp.route("/write", methods=["GET", "POST"])
@login_required
def write():
    form = PostForm()
    category_name = request.args.get("category", "자유게시판")
    category_obj = Category.query.filter_by(name=category_name).first()
    is_gallery_category = category_obj.type == "photo" if category_obj else False

    if request.method == "GET":
        form.author.data = current_user.username

    if form.validate_on_submit():
        title = form.title.data.strip()
        content = form.content.data.strip()

        if not current_user.is_authenticated:
            flash("로그인 상태가 아닙니다.", "error")
            return redirect(url_for("auth.login"))

        if not category_obj:
            flash("잘못된 카테고리입니다.", "error")
            return redirect(url_for("post.index", category=category_name, page=1))

        # 이미지 처리
        image = form.image.data
        if image and image.filename:
            filename = secure_filename(image.filename)
            image_path = os.path.join("static", "uploads", filename)
            image.save(image_path)
            content += f'<br><img src="/{image_path}" alt="첨부이미지">'

        # 배경음악 처리
        bgm_file = form.bgm.data
        if bgm_file and bgm_file.filename:
            bgm_filename = secure_filename(bgm_file.filename)
            bgm_path = os.path.join("static", "music", "bgm", bgm_filename)
            os.makedirs(os.path.dirname(bgm_path), exist_ok=True)
            bgm_file.save(bgm_path)
            bgm_tag = f'<audio src="/static/music/bgm/{bgm_filename}" autoplay loop hidden></audio>'
            content = bgm_tag + content

        # 첨부파일 처리
        attachment_file = form.attachment.data
        attachment_filename = None
        attachment_original = None
        if attachment_file and attachment_file.filename:
            attachment_filename = secure_filename(attachment_file.filename)
            attachment_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment_filename)
            attachment_file.save(attachment_path)
            attachment_original = attachment_file.filename

        post = Post(
            title=title,
            content=content,
            author_id=current_user.id,
            category_id=category_obj.id,
            attachment=attachment_filename,
            attachment_original=attachment_original
        )
        db.session.add(post)
        db.session.commit()

        flash("작성 완료!", "success")
        return redirect(url_for("post.detail", post_id=post.id))

    return render_template("write.html",
                           form=form,
                           category=category_name,
                           is_gallery_category=is_gallery_category,
                           current_user=current_user,
                           post=None)


# 첨부파일 다운로드
@post_bp.route("/download/<filename>")
@login_required
def download_file(filename):
    post = Post.query.filter_by(attachment=filename).first()
    original_name = post.attachment_original if post else filename
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True,
        download_name=original_name
    )


# 글 수정
@post_bp.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit(post_id):
    post = Post.query.get_or_404(post_id)
    category_obj = Category.query.get(post.category_id)
    is_gallery_category = category_obj.type == "photo" if category_obj else False

    form = PostForm(obj=post)

    if form.validate_on_submit():
        post.title = form.title.data.strip()
        new_content = form.content.data.strip()

        # BGM 파일 처리
        bgm_file = form.bgm.data
        if bgm_file and bgm_file.filename:
            bgm_filename = secure_filename(bgm_file.filename)
            bgm_path = os.path.join("static", "music", bgm_filename)
            os.makedirs(os.path.dirname(bgm_path), exist_ok=True)
            bgm_file.save(bgm_path)
            bgm_tag = f'<audio src="/static/music/{bgm_filename}" autoplay loop hidden></audio>'
            new_content = bgm_tag + new_content
        else:
            if '<audio' in post.content:
                existing_bgm_tag = post.content.split('</audio>')[0] + '</audio>'
                new_content = existing_bgm_tag + new_content

        # 이미지 처리
        image = form.image.data
        if image and image.filename:
            filename = secure_filename(image.filename)
            image_path = os.path.join("static", "uploads", filename)
            image.save(image_path)
            new_content += f'<br><img src="/{image_path}" alt="첨부이미지">'

        post.content = new_content

        db.session.commit()
        flash("수정되었습니다.", "success")
        return redirect(url_for("post.detail", post_id=post.id))

    return render_template("edit.html", post=post, form=form, is_gallery_category=is_gallery_category)

# 게시글 필터링(관리자페이지)
@post_bp.route("/admin/posts")
@post_bp.route("/admin/posts/page/<int:page>")
@login_required
def admin_post_list(page=1):
    selected_category = request.args.get("category", "전체")
    q = request.args.get("q", "")
    per_page = 20

    if selected_category == "전체":
        query = Post.query
    else:
        query = Post.query.join(Category).filter(Category.name == selected_category)

    if q:
        search = f"%{q}%"
        query = query.filter(Post.title.like(search))

    posts_paginated = query.order_by(Post.id.desc()).paginate(page=page, per_page=per_page)

    # 게시판 목록 등 추가 데이터
    categories = Category.query.all()
    comments = Comment.query.all()
    users = User.query.all()

    return render_template("admin.html",
                           posts=posts_paginated.items,
                           selected_category=selected_category,
                           categories=categories,
                           comments=comments,
                           users=users,
                           csrf_token=generate_csrf())

# 글 삭제
@post_bp.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete(post_id):
    form = DeletePostForm()
    post = Post.query.options(joinedload(Post.category)).get_or_404(post_id)
    category_name = post.category.name
    user = User.query.get(session.get("user_id"))

    if not form.validate_on_submit():
        flash("비밀번호를 입력해주세요.", "error")
        return redirect(url_for("post.detail", post_id=post_id))

    if not user.check_password(form.password.data):
        flash("비밀번호가 틀렸습니다.", "error")
        return redirect(url_for("post.detail", post_id=post_id))

    if not user.is_admin and post.author_id != user.id:
        flash("작성자만 삭제할 수 있습니다.", "error")
        return redirect(url_for("post.detail", post_id=post_id))

    # 관리자 아니면 비밀번호 확인 (post.password 컬럼에 비밀번호가 따로 저장되어 있다면 체크)
    if not user.is_admin and post.password:
        if not check_password_hash(post.password, form.password.data):
            flash("비밀번호가 틀렸습니다.", "danger")
            return redirect(url_for("post.detail", post_id=post.id))

    db.session.delete(post)
    db.session.commit()

    flash("관리자 권한으로 삭제되었습니다." if user.is_admin else "삭제 완료!", "success")
    return redirect(url_for("post.index", category=category_name, page=1))


# 관리자 페이지 보기
@post_bp.route("/admin")
@login_required
def admin():
    user = User.query.get(session["user_id"])
    if not user.is_admin:
        flash("관리자 전용 페이지입니다.")
        return redirect(url_for("post.home"))

    form = AdminForm()
    add_form = AddCategoryForm()
    delete_form = DeletePostForm()
    edit_form = EditCategoryForm()
    delete_users_form = DeleteUsersForm()

    selected_category = request.args.get("category", "전체")
    categories = Category.query.order_by(Category.id.asc()).all()

    if selected_category == "전체":
        posts = Post.query.order_by(Post.id.desc()).all()
        comments = Comment.query.order_by(Comment.id.desc()).all()
    else:
        posts = Post.query.join(Category).filter(Category.name == selected_category).order_by(Post.id.desc()).all()
        comments = Comment.query.join(Post).join(Category).filter(Category.name == selected_category).order_by(Comment.id.desc()).all()

    users = User.query.order_by(User.created_at.desc()).all()

    return render_template(
        "admin_dashboard.html",
        posts=posts,
        comments=comments,
        users=users,
        categories=categories,
        selected_category=selected_category,
        form=form,
        add_form=add_form,
        delete_form=delete_form,
        edit_form=edit_form,
        delete_users_form=delete_users_form
    )


# 게시글 다중 삭제
@post_bp.route("/bulk_delete_post", methods=["POST"])
@login_required
def bulk_delete_post():
    user = User.query.get(session["user_id"])
    if not user.is_admin:
        flash("관리자 권한이 필요합니다.")
        return redirect(url_for("post.home"))

    post_ids = request.form.getlist("post_ids")
    if post_ids:
        Post.query.filter(Post.id.in_(post_ids)).delete(synchronize_session=False)
        db.session.commit()
        flash(f"{len(post_ids)}개의 게시글이 삭제되었습니다.", "success")
    else:
        flash("선택된 게시글이 없습니다.", "error")

    return redirect(url_for("post.admin"))


# 회원 승인, 삭제, 권한 변경 일괄 처리
@post_bp.route("/admin/bulk_action", methods=["POST"])
@login_required
def bulk_action():
    user = current_user

    if not user.is_admin:
        return jsonify(success=False, message="권한 없음")

    data = request.get_json()
    action = data.get("action")
    user_ids = data.get("user_ids", [])

    if not user_ids:
        return jsonify(success=False, message="선택된 사용자 없음")

    if action == "approve":
        User.query.filter(User.id.in_(user_ids)).update(
            {User.is_approved: True}, synchronize_session=False
        )
    elif action == "reject":
        User.query.filter(User.id.in_(user_ids)).update(
            {User.is_approved: False}, synchronize_session=False
        )
    elif action == "delete":
        User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)
    elif action == "set_master":
        if not user.is_master:
            return jsonify(success=False, message="마스터 계정만 설정 가능")
        User.query.filter(User.id.in_(user_ids)).update(
            {User.is_master: True, User.is_admin: True}, synchronize_session=False
        )
    elif action == "unset_master":
        if not user.is_master:
            return jsonify(success=False, message="마스터 계정만 해제 가능")
        if user.id in user_ids:
            return jsonify(success=False, message="자기 자신은 마스터 해제 불가")
        User.query.filter(User.id.in_(user_ids)).update(
            {User.is_master: False, User.is_admin: False}, synchronize_session=False
        )
    else:
        return jsonify(success=False, message="알 수 없는 작업")

    db.session.commit()
    return jsonify(success=True)


# 이미지 업로드
@post_bp.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    file = (
        request.files.get('upload') or
        request.files.get('ckfinder') or
        next(iter(request.files.values()), None)
    )

    if not file:
        return jsonify({"error": {"message": "파일이 첨부되지 않았습니다"}}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join('static', 'uploads', filename)

    try:
        file.save(save_path)
        url = url_for('static', filename=f'uploads/{filename}')
        return jsonify({"url": url})
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500


# 글 상세보기 및 댓글 작성
@post_bp.route("/detail/<int:post_id>", methods=["GET", "POST"], endpoint="detail")
@login_required
def detail(post_id):
    post = Post.query.get_or_404(post_id)
    category_obj = Category.query.get(post.category_id)
    is_gallery_category = category_obj.type == "photo" if category_obj else False

     # ✅ 조회수 증가 (관리자 포함)
    if request.method == "GET":
        post.read_count += 1
        db.session.commit()
 
    if request.method == "POST":
        user_id = session.get("user_id")
        comment = Comment(
            author_id=user_id,
            content=request.form["content"],
            post_id=post.id
        )
        db.session.add(comment)
        db.session.commit()
        flash("댓글이 등록되었습니다.", "success")
        return redirect(url_for("post.detail", post_id=post.id))    

    return render_template("detail.html", post=post, is_gallery_category=is_gallery_category)

# 댓글 수정
@post_bp.route("/comment/<int:comment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    user_id = session.get("user_id")

    if comment.author_id != user_id and not g.user.is_admin:
        flash("수정 권한이 없습니다.", "error")
        return redirect(url_for("post.detail", post_id=comment.post_id))

    form = EditCommentForm()

    if request.method == "POST":
        comment.content = form.new_content.data.strip()
        db.session.commit()
        flash("댓글이 수정되었습니다.", "success")
        return redirect(url_for("post.detail", post_id=comment.post_id))

    form.new_content.data = comment.content
    return render_template("edit_comment.html", comment=comment, form=form)


# 여러 댓글 삭제
@post_bp.route("/comments/delete", methods=["POST"])
@login_required
def delete_comments():
    comment_ids = request.form.getlist("comment_ids")
    user_id = session.get("user_id")

    if not comment_ids:
        flash("삭제할 댓글을 선택하세요.", "error")
        return redirect(request.referrer or url_for("post.admin"))

    comment_ids = [int(cid) for cid in comment_ids if cid.isdigit()]
    comments = Comment.query.filter(Comment.id.in_(comment_ids)).all()

    deleted_count = 0
    for comment in comments:
        if comment.author_id == user_id or g.user.is_admin:
            db.session.delete(comment)
            deleted_count += 1

    db.session.commit()
    flash(f"{deleted_count}개의 댓글이 삭제되었습니다.", "success")
    return redirect(request.referrer or url_for("post.admin"))


# 단일 댓글 삭제
@post_bp.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    user_id = session.get("user_id")

    if comment.author_id != user_id and not g.user.is_admin:
        flash("삭제 권한이 없습니다.", "error")
        return redirect(url_for("post.detail", post_id=comment.post_id))

    db.session.delete(comment)
    db.session.commit()
    flash("댓글이 삭제되었습니다.", "success")
    return redirect(url_for("post.detail", post_id=comment.post_id))
