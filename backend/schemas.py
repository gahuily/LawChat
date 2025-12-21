from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str # 유저 ID 역할
    email: EmailStr | None = None
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    
    class Config:
        from_attributes = True # ORM 객체를 Pydantic 모델로 변환 허용

class Token(BaseModel):
    access_token: str
    token_type: str