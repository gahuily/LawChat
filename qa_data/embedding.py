from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import time

# ==========================================================
# 설정
# ==========================================================
DB_URL = "postgresql+psycopg2://user:password@localhost:5432/lawdb"
MODEL_NAME = 'jhgan/ko-sroberta-multitask'
BATCH_SIZE = 8  # CPU에서는 작은 배치 사이즈 사용

# ==========================================================
# 초기화
# ==========================================================
engine = create_engine(DB_URL)

print("📦 모델 로딩 중... (첫 실행 시 다운로드 필요)")
model = SentenceTransformer(MODEL_NAME, device='cpu')
print(f"✅ 모델 로드 완료: {MODEL_NAME}")
print(f"📏 임베딩 차원: {model.get_sentence_embedding_dimension()}")

# ==========================================================
# 테이블 준비
# ==========================================================
with engine.begin() as conn:
    conn.execute(text("""
        ALTER TABLE legal_qna 
        ADD COLUMN IF NOT EXISTS question_embedding vector(768),
        ADD COLUMN IF NOT EXISTS answer_embedding vector(768);
    """))
    print("✅ 테이블 준비 완료")

# ==========================================================
# 데이터 조회
# ==========================================================
with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT qna_id, question, answer
        FROM legal_qna
        WHERE question_embedding IS NULL
    """)).fetchall()

total_count = len(rows)
print(f"📊 총 {total_count}개 데이터 임베딩 시작")

if total_count == 0:
    print("⚠️  임베딩할 데이터가 없습니다.")
    exit(0)

# 예상 시간 계산 (대략 1개당 0.1초 기준)
estimated_minutes = (total_count * 0.1 * 2) / 60  # question + answer
print(f"⏱️  예상 소요 시간: 약 {estimated_minutes:.1f}분")

# ==========================================================
# 임베딩 및 저장
# ==========================================================
update_sql = text("""
    UPDATE legal_qna
    SET question_embedding = CAST(:q_embedding AS vector),
        answer_embedding = CAST(:a_embedding AS vector)
    WHERE qna_id = :qna_id
""")

start_time = time.time()
processed_count = 0

with engine.begin() as conn:
    for i in tqdm(range(0, len(rows), BATCH_SIZE), desc="임베딩 진행 중"):
        batch = rows[i:i + BATCH_SIZE]
        
        try:
            # 배치 데이터 추출
            questions = [row.question for row in batch]
            answers = [row.answer for row in batch]
            
            # 임베딩 생성
            q_embeddings = model.encode(
                questions, 
                convert_to_numpy=True,
                show_progress_bar=False  # tqdm과 충돌 방지
            )
            a_embeddings = model.encode(
                answers, 
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # DB 저장
            for row, q_emb, a_emb in zip(batch, q_embeddings, a_embeddings):
                q_vec_str = '[' + ','.join(map(str, q_emb.tolist())) + ']'
                a_vec_str = '[' + ','.join(map(str, a_emb.tolist())) + ']'
                
                conn.execute(update_sql, {
                    "qna_id": row.qna_id,
                    "q_embedding": q_vec_str,
                    "a_embedding": a_vec_str
                })
            
            processed_count += len(batch)
            
            # 진행률 표시 (매 100개마다)
            if processed_count % 100 == 0:
                elapsed = time.time() - start_time
                speed = processed_count / elapsed
                remaining = (total_count - processed_count) / speed / 60
                print(f"  → {processed_count}/{total_count} 완료 | "
                      f"속도: {speed:.1f}개/초 | "
                      f"남은 시간: {remaining:.1f}분")
                
        except Exception as e:
            print(f"❌ 배치 오류 (인덱스 {i}): {e}")
            continue

# ==========================================================
# 완료 통계
# ==========================================================
elapsed_time = time.time() - start_time
print(f"\n✅ 임베딩 완료!")
print(f"   총 처리: {processed_count}개")
print(f"   소요 시간: {elapsed_time/60:.1f}분")
print(f"   평균 속도: {processed_count/elapsed_time:.2f}개/초")

# ==========================================================
# 인덱스 생성
# ==========================================================
print("\n🔨 인덱스 생성 중...")
with engine.begin() as conn:
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS legal_qna_question_embedding_idx 
        ON legal_qna 
        USING ivfflat (question_embedding vector_cosine_ops) 
        WITH (lists = 100);
        
        CREATE INDEX IF NOT EXISTS legal_qna_answer_embedding_idx 
        ON legal_qna 
        USING ivfflat (answer_embedding vector_cosine_ops) 
        WITH (lists = 100);
    """))
    print("✅ 인덱스 생성 완료")

print("\n🎉 모든 작업 완료!")