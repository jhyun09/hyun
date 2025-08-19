# 옛날제로보드 게시판 .xml백업 파일 파씽 (2025년 8월 4일) 자유, 이야기,사진, 습작 게시판, 등
# 복원 경로수정포함(댓글이 딴게시글에 있는게 몇개 보임), 파싱 꼬일시 db파일 삭제후 마이그레이션/업그레이드 후
# crete_admin.py 관리자 아이디 만든 후 파싱파일 새로 실행하면 됨. 폼 바뀌면 다시 코드 수정해야 함.

import xml.etree.ElementTree as ET
import base64
import os
from datetime import datetime
from html import unescape
from bs4 import BeautifulSoup
from werkzeug.security import generate_password_hash

from app import app, db
from models import User, Post, Comment, Category


def b64(text):
    try:
        return base64.b64decode(text).decode("utf-8")
    except:
        return ""

def decode_content_with_images(encoded_html):
    decoded = b64(encoded_html)
    decoded = unescape(unescape(decoded))  # 이중 디코딩

    soup = BeautifulSoup(decoded, "html.parser")

    # 이미지 경로 보정
    for img in soup.find_all("img"):
        src = img.get("src")
        if src and not src.startswith("/"):
            img["src"] = f"/static/restore_images/{src.strip()}"

    return str(soup)

def get_or_create_category(name):
    category = Category.query.filter_by(name=name).first()
    if not category:
        category = Category(name=name)
        db.session.add(category)
        db.session.flush()
        print(f"📁 새 카테고리 생성: {name}")
    return category

def get_or_create_user(username):
    username = username.strip() or "익명"
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            password_hash=generate_password_hash("default1234")  # 기본 비밀번호 반드시 설정
        )
        db.session.add(user)
        db.session.flush()
    return user

def parse_board_xml(file_path, category_name):
    tree = ET.parse(file_path)
    root = tree.getroot()

    category = get_or_create_category(category_name)

    for item in root.findall(".//post"):
        title = b64(item.findtext("title", ""))
        author_name = b64(item.findtext("nick_name", "")) or b64(item.findtext("user_id", ""))
        date_str = b64(item.findtext("regdate", ""))
        read_count = int(b64(item.findtext("readed_count", "0")) or 0)

        try:
            date_obj = datetime.strptime(date_str, "%Y%m%d%H%M%S")
        except:
            date_obj = datetime.now()

        encoded_content = item.findtext("content", "")
        content = decode_content_with_images(encoded_content)

        author = get_or_create_user(author_name)

        post = Post(
            title=title.strip(),
            author_id=author.id,
            content=content.strip(),
            date=date_obj,
            read_count=read_count,
            category_id=category.id
        )
        db.session.add(post)
        db.session.flush()

        comment_list = item.find("comments")
        if comment_list is not None:
            for c in comment_list.findall("comment"):
                try:
                    c_author_name = b64(c.findtext("nick_name", "")) or b64(c.findtext("user_id", ""))
                    c_author = get_or_create_user(c_author_name)

                    c_content = b64(c.findtext("content", ""))
                    c_date_str = b64(c.findtext("regdate", ""))
                    try:
                        c_date_obj = datetime.strptime(c_date_str, "%Y%m%d%H%M%S")
                    except:
                        c_date_obj = datetime.now()

                    comment = Comment(
                        author_id=c_author.id,
                        content=c_content.strip(),
                        created_at=c_date_obj,
                        post_id=post.id
                    )
                    db.session.add(comment)
                except Exception as e:
                    print("⚠️ 댓글 처리 중 오류:", e)

def parse_all_xml_in_folder(folder_path, category_name):
    for filename in os.listdir(folder_path):
        if filename.endswith(".xml"):
            file_path = os.path.join(folder_path, filename)
            print(f"📦 파싱 중: {filename}")
            parse_board_xml(file_path, category_name)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # 필요에 따라 아래 주석 해제해서 여러 게시판 파싱 가능
        parse_all_xml_in_folder(r"D:\myboard\parsing\g1", "사진 게시판")
       #  parse_all_xml_in_folder(r"D:\myboard\parsing\g2", "습작 게시판")
       #  parse_board_xml("module_freeboard.000001.xml", "자유 게시판")
       #  parse_board_xml("module_story1.000001.xml", "이야기 게시판")
        # parse_board_xml("module_galleryboard.000001.xml", "사진 게시판")
        parse_board_xml("module_happy.000001.xml", "쭈야 게시판")

        db.session.commit()
        print("🎉 XML 파싱 + 저장 완료!")
