from elasticsearch import Elasticsearch, helpers
import psycopg2
from psycopg2.extras import RealDictCursor

def main():
    pg_conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="lawchat",
        user="wish",
        password="0000",
    )
    pg_cur = pg_conn.cursor(cursor_factory=RealDictCursor)

    es = Elasticsearch("http://localhost:9200")

    pg_cur.execute("""
        SELECT law_id, law_name_kor, law_type,
               promulgation_date, enforcement_date
        FROM laws;
    """)
    rows = pg_cur.fetchall()

    actions = []
    for row in rows:
        actions.append({
            "_index": "laws",
            "_id": row["law_id"],
            "_source": {
                "law_id": row["law_id"],
                "law_name_kor": row["law_name_kor"],
                "law_type": row["law_type"],
                "promulgation_date": row["promulgation_date"],
                "enforcement_date": row["enforcement_date"],
            }
        })

    if actions:
        helpers.bulk(es, actions)
        print(f"{len(actions)}개의 법령 문서를 Elasticsearch에 인덱싱 완료!")
    else:
        print("인덱싱할 법령 데이터가 없습니다.")

    pg_cur.close()
    pg_conn.close()

if __name__ == "__main__":
    main()
