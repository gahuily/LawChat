
-- 1) 데이터베이스 생성 (이미 있으면 에러 나므로 IF NOT EXISTS 사용 불가)
-- CREATE DATABASE lawdb;

-- -----------------------------------------------------------
-- 📌 Q&A 테이블 생성
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS legal_qna (
    id              SERIAL PRIMARY KEY,
    qna_id          VARCHAR(50) UNIQUE,     -- 사이트별 고유 ID 또는 내부 ID
    source          VARCHAR(50),            -- 'easylaw', 'klac', 'etc'
    url             TEXT,
    category        VARCHAR(100),

    question        TEXT,
    answer          TEXT,

    created_at      TIMESTAMP NULL,         -- 원문 생성일
    crawled_at      TIMESTAMP DEFAULT NOW() -- 크롤링 시각
);

-- 인덱스 생성 (검색 속도 개선)
CREATE INDEX IF NOT EXISTS idx_qna_id ON legal_qna(qna_id);
CREATE INDEX IF NOT EXISTS idx_qna_category ON legal_qna(category);


-- -----------------------------------------------------------
-- 📌 예시 데이터 삽입 (옵션 - 테스트 용)
-- -----------------------------------------------------------
-- INSERT INTO legal_qna (qna_id, source, url, category, question, answer)
-- VALUES (
--     'sample001',
--     'easylaw',
--     'https://example.com/qna/sample001',
--     '근로기준법',
--     '퇴직금은 언제 지급되나요?',
--     '퇴직금은 근로기준법 제36조에 따라 퇴사일로부터 14일 이내에 지급해야 합니다.'
-- );

