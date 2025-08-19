# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, HiddenField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo, Optional
from wtforms.fields import EmailField
from flask_wtf.file import FileField, FileAllowed


class AddCategoryForm(FlaskForm):
    category_name = StringField("카테고리 이름", validators=[DataRequired()])
    category_type = SelectField("타입", choices=[("text", "일반"), ("photo", "사진")])

class PostForm(FlaskForm):
    title = StringField("제목", validators=[DataRequired()])
    author = StringField("작성자")
    content = TextAreaField("내용", validators=[DataRequired()])
    image = FileField("이미지", validators=[FileAllowed(['jpg', 'png', 'gif'], '이미지만 업로드 가능합니다.')])
    attachment = FileField('첨부파일', validators=[FileAllowed(['zip', 'ai', 'eps', 'pdf', 'xlsx', 'docx', 'xls'])])

    bgm = FileField("배경음악 업로드")  # 🎵 추가


class DeleteCategoryForm(FlaskForm):
    category_id = StringField("삭제할 게시판 ID", validators=[DataRequired()])

class EditCategoryForm(FlaskForm):
    category_id = StringField("수정할 게시판 ID", validators=[DataRequired()])
    category_type = SelectField("타입", choices=[("text", "일반"), ("photo", "사진")])

class EditCommentForm(FlaskForm):
    
    new_content = TextAreaField("내용", validators=[DataRequired()])

class AdminForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired()])
    is_active = BooleanField('활성화 여부')
    submit = SubmitField('저장하기')

class DeleteUsersForm(FlaskForm):
    user_id = HiddenField()  # 삭제할 사용자 ID
    submit = SubmitField('삭제')

class DeletePostForm(FlaskForm):
    password = PasswordField('비밀번호', validators=[DataRequired()])
    submit = SubmitField('삭제하기')    

class DeleteCommentForm(FlaskForm):
    comment_id = HiddenField()
    submit = SubmitField('삭제')

class EditAccountForm(FlaskForm):
    email = EmailField('이메일', validators=[DataRequired(), Email()])
    password = PasswordField('새 비밀번호', validators=[Optional()])
    confirm_password = PasswordField('비밀번호 확인', validators=[Optional(), EqualTo('password', message='비밀번호가 일치하지 않습니다.')])
    bio = TextAreaField('설명 및 소개', validators=[Optional()])


