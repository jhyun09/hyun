@echo off
echo [🔧] 가상환경 확인 중...

REM 가상환경이 없으면 생성
IF NOT EXIST venv (
    echo [🛠️] 가상환경 생성 중...
    python -m venv venv
)

REM 가상환경 활성화
call venv\Scripts\activate

echo [📦] 패키지 설치 중...
pip install --upgrade pip
pip install -r requirements.txt

echo [🚀] Flask 서버 실행 중...
python app.py

pause