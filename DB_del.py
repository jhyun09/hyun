import os

db_path = os.path.join("instance", "board.db")

if os.path.exists(db_path):
    os.remove(db_path)
    print("기존 DB 파일 삭제 완료")
else:
    print("삭제할 DB 파일이 없습니다.")