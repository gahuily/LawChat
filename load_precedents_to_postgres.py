import json
import psycopg2
from datetime import datetime

def main():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="lawchat",
        user="wish",
        password="0000",
    )
    cur = conn.cursor()

    with open("sample_precedents.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for row in data:
        prec_id = row["prec_id"]
        case_no = row["case_no"]
        case_name = row["case_name"]
        court_name = row["court_name"]
        judgment_date = datetime.strptime(row["judgment_date"], "%Y-%m-%d").date()
        summary = row["summary"]
        full_text = row["full_text"]

        sql = """
        INSERT INTO precedents
            (prec_id, case_no, case_name, court_name, judgment_date, summary, full_text)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (prec_id) DO NOTHING;
        """
        cur.execute(sql, (
            prec_id, case_no, case_name, court_name,
            judgment_date, summary, full_text
        ))

    conn.commit()
    cur.close()
    conn.close()
    print("샘플 판례 데이터 PostgreSQL 적재 완료!")

if __name__ == "__main__":
    main()
