from fastapi import FastAPI
from db import models
from db.database import engine

# DB 테이블 생성
models.Base.metadata.create_all(bind=engine)

# FastAPI 인스턴스 생성
app = FastAPI(
    title="Legal Chatbot Backend",
    description="판례 및 법률 정보를 제공하는 RAG 기반 챗봇 API",
    version="0.1.0"
)

# 기본 헬스 체크용 엔드포인트
@app.get("/")
def read_root():
    return {"message": "Welcome to Legal Chatbot API", "status": "running"}
