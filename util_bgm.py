# 게시판 파싱 후 기존 링크 음악파일 .mp3로 변환 새로운 링크로 수정
# 2025년 8월 6일 픽스.

import re
import html
from models import db, Post
from app import app

def convert_embed_to_audio(content: str) -> str:
    def replacer(match):
        src = match.group('src')
        if not src:
            return match.group(0)

        # 경로 변환: mms:// → /static/music/bgm/
        src = re.sub(
            r'mms://wm-001\.cafe24\.com/jhyun09/bgm/',
            '/static/music/',
            src,
            flags=re.IGNORECASE
        )

        # 확장자 변환: .wma, .asx → .mp3
        mp3_src = re.sub(r'\.(wma|asx|asf)$', '.mp3', src, flags=re.IGNORECASE)

        # 최종 변환된 <audio> 태그 반환
        return f'<audio src="{mp3_src}" autoplay loop hidden></audio>'

    # .wma 또는 .asx 확장자를 가진 <embed> 태그 찾기
    pattern = re.compile(
        r'<embed[^>]*src=(?P<quote>["\'])(?P<src>[^"\']+\.(wma|asx|asf))(?P=quote)[^>]*/?>',
        re.IGNORECASE
    )

    return pattern.sub(replacer, content)


with app.app_context():
    posts = Post.query.all()
    updated = 0

    for post in posts:
        original = post.content
        new_content = original

        # 1. HTML 엔티티 복원 (예: &amp;lt; → <)
        new_content = html.unescape(new_content)

        # 2. <embed> 태그를 <audio> 태그로 변환 (cafe24 경로 포함)
        new_content = convert_embed_to_audio(new_content)

        # 3. 변경된 경우만 업데이트
        if new_content != original:
            post.content = new_content
            updated += 1

    db.session.commit()
    print(f"✅ 게시글 배경음악 링크 변환 완료! 변경된 게시글 수: {updated}")