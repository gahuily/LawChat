import json
import psycopg2
from datetime import datetime

def parse_date(date_str):
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def main():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="lawchat",
        user="wish",
        password="0000",
    )
    cur = conn.cursor()

    with open("sample_laws.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for row in data:
        law_id = row["law_id"]
        law_name_kor = row["law_name_kor"]
        law_type = row["law_type"]
        promulgation_date = parse_date(row.get("promulgation_date"))
        enforcement_date = parse_date(row.get("enforcement_date"))

        sql = """
        INSERT INTO laws
            (law_id, law_name_kor, law_type, promulgation_date, enforcement_date)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (law_id) DO NOTHING;
        """
        cur.execute(sql, (
            law_id, law_name_kor, law_type, promulgation_date, enforcement_date
        ))

    conn.commit()
    cur.close()
    conn.close()
    print("샘플 법령 데이터 PostgreSQL 적재 완료!")

if __name__ == "__main__":
    main()
