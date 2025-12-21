from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from jose import jwt

from db import models, database
import schemas, crud
# from db.database import engine

# 1. 보안 및 토큰 설정
SECRET_KEY = "super-secret-key-lawchat"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# 2. DB 테이블 자동 생성
models.Base.metadata.create_all(bind=database.engine)

# 3. FastAPI 앱 인스턴스
app = FastAPI(
    title="Legal Chatbot Backend",
    description="판례 및 법률 정보를 제공하는 RAG 기반 챗봇 API",
    version="0.1.0"
)

# 4. 의존성 함수
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 5. 토큰 생성 함수
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ==============================
# [API 엔드포인트 정의]
# ==============================

# 1. 기본 헬스 체크 (서버 살아있는지 확인용)
@app.get("/")
def read_root():
    return {"message": "Welcome to Legal Chatbot API", "status": "running"}

# 2. 회원가입 (Sign Up)
@app.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 사용자입니다.")
    return crud.create_user(db=db, user=user)

# 3. 로그인(Login) -> 성공 시 토큰 발급
@app.post("/login", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not crud.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
