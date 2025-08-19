from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from extensions import db
from forms import EditAccountForm

# Blueprint 생성
account_bp = Blueprint('account', __name__, url_prefix='/account')

# 계정 수정 라우트
@account_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_account():
    form = EditAccountForm()

    if request.method == 'GET':
        form.email.data = current_user.email
        form.bio.data = current_user.bio

    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.bio = form.bio.data

        if form.password.data:
            current_user.password_hash = generate_password_hash(form.password.data)

        db.session.commit()
        flash('계정 정보가 수정되었습니다.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('account_edit.html', form=form)