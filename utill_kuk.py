import re
from models import db, Post
from app import app

with app.app_context():
    posts = Post.query.all()
    updated = 0

    for post in posts:
        original = post.content

        # src="D:\..." 또는 src=&quot;D:\..." → src="/static/kuk/..."
        new_content = re.sub(
            r'(src=(?:&quot;|"))D:\\myboard\\parsing\\static\\kuk\\([^"&]+)',
            r'\1/static/kuk/\2',
            original
        )

        if new_content != original:
            post.content = new_content
            updated += 1

    db.session.commit()
    print(f"✅ 웹 경로로 수정 완료! 변경된 게시글 수: {updated}")