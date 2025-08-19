# 사진게시판 경로 수정 #

import re
from models import db, Post
from app import app

with app.app_context():
    posts = Post.query.all()
    updated = 0

    for post in posts:
        original = post.content

        # HTML 인코딩된 src 속성 경로 수정
        new_content = re.sub(
            r'(src=(&quot;|"))/static/uploads/unknown/([^"&]+)',
            r'\1/static/restore_images/\3',
            original
        )

        if new_content != original:
            post.content = new_content
            updated += 1

    db.session.commit()
    print(f"✅ 경로 수정 완료! 변경된 게시글 수: {updated}")