from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# 1. 사용자(User) 테이블 설계도
class User(Base):
    __tablename__ = "users"  # 실제 DB에 저장될 테이블 이름

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)  # 유저 이름 (중복 금지)
    password = Column(String)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow) # 가입 시간

    # 관계 설정: 유저(1) <-> 채팅기록(N)
    chats = relationship("ChatHistory", back_populates="owner")

# 2. 대화 기록(ChatHistory) 테이블 설계도
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # 외래키: users 테이블의 id를 참조
    
    question = Column(Text, nullable=False)  # 사용자 질문 (길 수 있으므로 Text)
    answer = Column(Text, nullable=False)    # AI 답변
    created_at = Column(DateTime, default=datetime.utcnow) # 대화 생성 시간

    # 관계 설정: 채팅기록(N) <-> 유저(1)
    owner = relationship("User", back_populates="chats")