from sqlalchemy import create_engine, text
from elasticsearch import Elasticsearch
import elasticsearch
from tqdm import tqdm

# ==========================================================
# 1) PostgreSQL 연결
# ==========================================================
DB_URL = "postgresql+psycopg2://user:password@localhost:5432/lawdb"
engine = create_engine(DB_URL)

# ==========================================================
# 2) Elasticsearch 연결
# ==========================================================
es = Elasticsearch("http://localhost:9200")
INDEX_NAME = "legal_qna"

# 버전 확인
print(f"Elasticsearch 버전: {es.info()['version']['number']}")
print(f"elasticsearch-py 버전: {elasticsearch.__version__}")

# ==========================================================
# 3) 인덱스 삭제 후 재생성
# ==========================================================
# 기존 인덱스가 있으면 삭제
if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)
    print("🗑️  기존 인덱스 삭제")

# 새 인덱스 생성
try:
    es.indices.create(
        index=INDEX_NAME,
        body={
            "mappings": {
                "properties": {
                    "qna_id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "category": {"type": "text"},
                    "question": {"type": "text"},
                    "answer": {"type": "text"}
                }
            }
        }
    )
    print("✅ Elasticsearch 인덱스 생성 완료")
except Exception as e:
    print(f"❌ 인덱스 생성 오류: {e}")
    exit(1)

# ==========================================================
# 4) PostgreSQL 데이터 조회
# ==========================================================
select_sql = text("""
    SELECT qna_id, source, category, question, answer
    FROM legal_qna
""")

with engine.connect() as conn:
    rows = conn.execute(select_sql).fetchall()

print(f"📊 총 {len(rows)}개의 데이터를 인덱싱합니다.")

# ==========================================================
# 5) Elasticsearch에 인덱싱
# ==========================================================
for row in tqdm(rows, desc="Elasticsearch 인덱싱 중"):
    doc = {
        "qna_id": row.qna_id,
        "source": row.source,
        "category": row.category,
        "question": row.question,
        "answer": row.answer,
    }

    try:
        es.index(
            index=INDEX_NAME,
            id=row.qna_id,
            document=doc
        )
    except Exception as e:
        print(f"❌ 인덱싱 오류 (qna_id: {row.qna_id}): {e}")

print("🎉 Elasticsearch 인덱싱 완료!")