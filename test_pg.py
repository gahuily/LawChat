import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="lawchat",  # docker-compose의 POSTGRES_DB
    user="wish",       # POSTGRES_USER
    password="0000"    # 방금 설정한 비밀번호
)

print("PostgreSQL 연결 성공!")
conn.close()
