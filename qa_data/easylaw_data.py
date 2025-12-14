# load_easylaw_to_postgres.py
from datasets import load_dataset
from sqlalchemy import create_engine, text
from tqdm import tqdm

# ==========================================================
# 1) PostgreSQL 연결 (너 환경에 맞게 수정)
# ==========================================================
DB_URL = "postgresql+psycopg2://user:password@localhost:5432/lawdb"
engine = create_engine(DB_URL)

# ==========================================================
# 2) HuggingFace 데이터셋 로드
# ==========================================================
print("📥 HuggingFace easylaw_kr 데이터셋 로드 중...")
dataset = load_dataset("jiwoochris/easylaw_kr")

data = dataset['train']  # 전체 데이터가 train split에 들어 있음
print(f"총 {len(data)}개의 Q&A 데이터를 불러왔습니다.")

# ==========================================================
# 3) INSERT SQL 준비
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
        :url,
        :category,
        :question,
        :answer,
        NULL
    )
    ON CONFLICT (qna_id) DO NOTHING;
""")

# ==========================================================
# 4) 한 줄씩 PostgreSQL에 넣기
# ==========================================================
with engine.begin() as conn:
    for i, row in enumerate(tqdm(data, desc="DB 적재중")):
        qna_id = f"easy_{i+1:06d}"

        conn.execute(insert_sql, {
            "qna_id": qna_id,
            "source": "easylaw",
            "url": "",
            "category": row.get("category", None),
            "question": row.get("instruction", None),
            "answer": row.get("output", None),
        })

print("🎉 PostgreSQL legal_qna 테이블 적재 완료!")
