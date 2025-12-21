from sqlalchemy.orm import Session
from passlib.context import CryptContext
from db.models import User
import schemas

# 비밀번호 암호화 설정 (bcrypt 알고리즘 사용)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. 비밀번호 암호화 함수
def get_password_hash(password):
    return pwd_context.hash(password)

# 2. 비밀번호 검증 함수 (입력된 비번 vs 저장된 암호화 비번 비교)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 3. 유저 조회 (username으로 찾기)
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

# 4. 회원가입 (DB에 유저 저장)
def create_user(db: Session, user: schemas.UserCreate):
    # 비밀번호를 쌩으로 저장하면 불법! 반드시 암호화합니다.
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password # 암호화된 비밀번호 저장
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user