from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 데이터베이스 접속 주소 (URL)
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# 2. 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. 세션 생성기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 모델 베이스 클래스
Base = declarative_base()