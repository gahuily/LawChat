import json
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
import requests

from .config import PG_CONFIG, LAW_API_OC, LAW_API_BASE

def parse_date(s: str | None):
    if not s:
        return None
    # "20240110" 형식이라고 가정
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except ValueError:
        return None

def get_pg_conn():
    return psycopg2.connect(**PG_CONFIG)

def fetch_prec_list(page: int = 1, query: str | None = None):
    """
    판례 목록 가져오기 (지금은 '절도' 같은 키워드로 일부만)
    """
    if not LAW_API_OC:
        raise RuntimeError("LAW_API_OC가 설정되어 있지 않습니다.")

    params = {
        "OC": LAW_API_OC,
        "target": "prec",
        "type": "JSON",
        "page": page,
    }
    if query:
        params["query"] = query

    url = f"{LAW_API_BASE}/lawSearch.do"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # ⚠️ 여기 부분은 test_api 출력 보고 맞추자
    # 예시1: data["PrecSearch"]["prec"]
    # 예시2: data["법령정보"]["판례목록"]
    # 일단 여러 후보 중 되는 것 하나 쓰기
    cand = None
    if "PrecSearch" in data and "prec" in data["PrecSearch"]:
        cand = data["PrecSearch"]["prec"]
    elif "법령정보" in data and "판례목록" in data["법령정보"]:
        cand = data["법령정보"]["판례목록"]
    elif "prec" in data:
        cand = data["prec"]

    if cand is None:
        print("판례 목록을 찾지 못했습니다. 응답:", json.dumps(data, ensure_ascii=False)[:500])
        return []

    # 만약 단일 dict로 나오는 경우 list로 감싸기
    if isinstance(cand, dict):
        return [cand]
    return cand

def upsert_precedent(cur, prec: dict, full_text: str | None = None):
    # 응답의 실제 키 이름에 맞게 조정
    prec_id = int(prec["판례일련번호"])
    case_no = prec.get("사건번호")
    case_name = prec.get("사건명")
    court_name = prec.get("법원명")
    judgment_date = parse_date(prec.get("선고일자"))
    summary = prec.get("판시사항") or prec.get("판결요지")
    full_text = full_text or prec.get("판례내용")

    sql = """
    INSERT INTO precedents
        (prec_id, case_no, case_name, court_name,
         judgment_date, summary, full_text)
    VALUES
        (%(prec_id)s, %(case_no)s, %(case_name)s, %(court_name)s,
         %(judgment_date)s, %(summary)s, %(full_text)s)
    ON CONFLICT (prec_id) DO UPDATE SET
        case_no = EXCLUDED.case_no,
        case_name = EXCLUDED.case_name,
        court_name = EXCLUDED.court_name,
        judgment_date = EXCLUDED.judgment_date,
        summary = EXCLUDED.summary,
        full_text = EXCLUDED.full_text;
    """
    cur.execute(sql, {
        "prec_id": prec_id,
        "case_no": case_no,
        "case_name": case_name,
        "court_name": court_name,
        "judgment_date": judgment_date,
        "summary": summary,
        "full_text": full_text,
    })

def run_prec_etl(max_pages: int = 1, query: str = "절도"):
    """
    처음에는 page=1만, query='절도'만 넣어보자.
    나중에 max_pages를 늘리거나 query를 여러 개로 돌리면 됨.
    """
    conn = get_pg_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    for page in range(1, max_pages + 1):
        print(f"[ETL] page={page}, query={query}")
        prec_list = fetch_prec_list(page=page, query=query)
        if not prec_list:
            print("더 이상 판례가 없거나 응답이 비었습니다.")
            break

        for prec in prec_list:
            try:
                upsert_precedent(cur, prec)
            except KeyError as e:
                print("키 에러 발생, 이 레코드는 건너뜀:", e, prec)
        conn.commit()

    cur.close()
    conn.close()
    print("ETL 완료")

if __name__ == "__main__":
    run_prec_etl(max_pages=1, query="절도")
