from elasticsearch import Elasticsearch, helpers
import psycopg2
from psycopg2.extras import RealDictCursor

from .config import PG_CONFIG, ES_HOST

def main():
    # PostgreSQL 연결
    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cur = pg_conn.cursor(cursor_factory=RealDictCursor)

    # Elasticsearch 연결
    es = Elasticsearch(ES_HOST)

    # precedents 테이블에서 데이터 가져오기
    pg_cur.execute("""
        SELECT prec_id, case_no, case_name, court_name,
               judgment_date, summary, full_text
        FROM precedents;
    """)
    rows = pg_cur.fetchall()

    actions = []
    for row in rows:
        actions.append({
            "_index": "precedents",
            "_id": row["prec_id"],
            "_source": {
                "prec_id": row["prec_id"],
                "case_no": row["case_no"],
                "case_name": row["case_name"],
                "court_name": row["court_name"],
                "judgment_date": row["judgment_date"],
                "summary": row["summary"],
                "full_text": row["full_text"],
            }
        })

    if actions:
        helpers.bulk(es, actions)
        print(f"{len(actions)}개 판례를 Elasticsearch에 인덱싱 완료!")
    else:
        print("인덱싱할 판례 데이터가 없습니다.")

    pg_cur.close()
    pg_conn.close()

if __name__ == "__main__":
    main()
