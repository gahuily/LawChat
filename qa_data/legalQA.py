# load_legalqa_to_postgres.py
import os
import json
import requests
from sqlalchemy import create_engine, text
from tqdm import tqdm

# ==========================================================
# 1) PostgreSQL 연결
# ==========================================================
DB_URL = "postgresql+psycopg2://user:password@localhost:5432/lawdb"
engine = create_engine(DB_URL)

# ==========================================================
# 2) 파일 다운로드
# ==========================================================
SAVE_DIR = "data"
os.makedirs(SAVE_DIR, exist_ok=True)

URL = "https://raw.githubusercontent.com/haven-jeon/LegalQA/main/data/legalqa.jsonlines"
SAVE_PATH = os.path.join(SAVE_DIR, "legalqa.jsonl")

def download_legalqa():
    print("⬇️ LegalQA 데이터 다운로드 중...")
    resp = requests.get(URL)
    resp.raise_for_status()

    with open(SAVE_PATH, "wb") as f:
        f.write(resp.content)

    print(f"✅ 다운로드 완료: {SAVE_PATH}")

# ==========================================================
# 3) INSERT SQL
# ==========================================================
insert_sql = text("""
    INSERT INTO legal_qna (
        qna_id,
        source,
        url,
        category,
        question,
        answer,
        created_at
    ) VALUES (
        :qna_id,
        :source,
        NULL,
        :category,
        :question,
        :answer,
        NULL
    )
    ON CONFLICT (qna_id) DO NOTHING;
""")

# ==========================================================
# 4) JSONL → PostgreSQL 적재
# ==========================================================
def load_legalqa_to_db():
    print("📥 legalqa.jsonl DB 적재 시작...")

    with open(SAVE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with engine.begin() as conn:
        for row in tqdm(lines, desc="DB 적재중"):
            data = json.loads(row)

            qna_id = f"legalqa_{int(data['id']):06d}"

            conn.execute(insert_sql, {
                "qna_id": qna_id,
                "source": "legalqa",
                "category": data.get("title"),
                "question": data.get("question"),
                "answer": data.get("answer"),
            })

    print("🎉 LegalQA PostgreSQL 적재 완료!")

# ==========================================================
# 5) 실행
# ==========================================================
if __name__ == "__main__":
    download_legalqa()
    load_legalqa_to_db()
