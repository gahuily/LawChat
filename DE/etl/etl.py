import os
import requests
from tqdm import tqdm
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from elasticsearch import Elasticsearch, helpers

# -------------------- 설정 --------------------

load_dotenv()

OC = os.getenv("LAW_API_OC")
if not OC:
    raise RuntimeError("환경변수 LAW_API_OC 가 설정되지 않았습니다. (.env 확인)")

PG_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", 5432)),
    "dbname": os.getenv("PG_DB", "legaldb"),
    "user": os.getenv("PG_USER", "wish"),
    "password": os.getenv("PG_PASSWORD", "0000"),
}

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")

BASE_SEARCH_URL = "http://www.law.go.kr/DRF/lawSearch.do"   # 목록 조회 
BASE_SERVICE_URL = "http://www.law.go.kr/DRF/lawService.do" # 본문 조회


# -------------------- 공통 유틸 --------------------

def get_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def find_items_block(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    lawSearch/precSearch 응답에서 totalCnt와 목록 리스트가 들어있는 블록 찾기.
    (실제 응답 구조는 open API 문서 예시 기준. 필요하면 print로 구조 확인 후 수정)
    """
    root = data
    for v in data.values():
        if isinstance(v, dict) and "totalCnt" in v:
            root = v
            break

    for v in root.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
    return []


def get_total_cnt(data: Dict[str, Any], default: int = 0) -> int:
    for v in data.values():
        if isinstance(v, dict) and "totalCnt" in v:
            return int(v["totalCnt"])
    return default


# -------------------- PostgreSQL --------------------

def get_pg_conn():
    return psycopg2.connect(**PG_CONFIG)


def create_tables():
    conn = get_pg_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS laws (
            id              BIGSERIAL PRIMARY KEY,
            law_id          BIGINT UNIQUE,
            law_name_kor    TEXT,
            law_type        TEXT,
            promulgation_date TEXT,
            enforcement_date TEXT
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS precedents (
            id              BIGSERIAL PRIMARY KEY,
            prec_id         BIGINT UNIQUE,
            case_name       TEXT,
            case_no         TEXT,
            court_name      TEXT,
            judgment_date   TEXT,
            case_type       TEXT,
            summary         TEXT,
            body            TEXT
        );
        """
    )

    conn.commit()
    cur.close()
    conn.close()
    print("[PG] 테이블 생성 완료")


def insert_law(row: Dict[str, Any]):
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO laws (law_id, law_name_kor, law_type,
                          promulgation_date, enforcement_date)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (law_id) DO UPDATE
        SET law_name_kor = EXCLUDED.law_name_kor,
            law_type = EXCLUDED.law_type,
            promulgation_date = EXCLUDED.promulgation_date,
            enforcement_date = EXCLUDED.enforcement_date;
        """,
        (
            row.get("law_id"),
            row.get("law_name_kor"),
            row.get("law_type"),
            row.get("promulgation_date"),
            row.get("enforcement_date"),
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


def insert_prec(row: Dict[str, Any]):
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO precedents (
            prec_id, case_name, case_no,
            court_name, judgment_date, case_type,
            summary, body
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (prec_id) DO UPDATE
        SET case_name = EXCLUDED.case_name,
            case_no = EXCLUDED.case_no,
            court_name = EXCLUDED.court_name,
            judgment_date = EXCLUDED.judgment_date,
            case_type = EXCLUDED.case_type,
            summary = EXCLUDED.summary,
            body = EXCLUDED.body;
        """,
        (
            row.get("prec_id"),
            row.get("case_name"),
            row.get("case_no"),
            row.get("court_name"),
            row.get("judgment_date"),
            row.get("case_type"),
            row.get("summary"),
            row.get("body"),
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


# -------------------- ES --------------------

def get_es():
    return Elasticsearch(ES_HOST)


def create_es_indices():
    es = get_es()

    laws_body = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "korean": {
                        "type": "custom",
                        "tokenizer": "nori_tokenizer",
                        "filter": ["lowercase", "nori_part_of_speech"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "law_id": {"type": "keyword"},
                "law_name_kor": {"type": "text", "analyzer": "korean"},
                "law_type": {"type": "keyword"},
                "promulgation_date": {"type": "date", "format": "yyyyMMdd"},
                "enforcement_date": {"type": "date", "format": "yyyyMMdd"},
            }
        },
    }

    prec_body = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "korean": {
                        "type": "custom",
                        "tokenizer": "nori_tokenizer",
                        "filter": ["lowercase", "nori_part_of_speech"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "prec_id": {"type": "keyword"},
                "case_name": {"type": "text", "analyzer": "korean"},
                "case_no": {"type": "keyword"},
                "court_name": {"type": "keyword"},
                "judgment_date": {"type": "date", "format": "yyyyMMdd"},
                "case_type": {"type": "keyword"},
                "summary": {"type": "text", "analyzer": "korean"},
                "body": {"type": "text", "analyzer": "korean"},
            }
        },
    }

    es.indices.create(index="laws", body=laws_body, ignore=400)
    es.indices.create(index="precedents", body=prec_body, ignore=400)
    print("[ES] 인덱스 생성 완료")


def pg_to_es():
    es = get_es()
    conn = get_pg_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # laws
    cur.execute("SELECT law_id, law_name_kor, law_type, promulgation_date, enforcement_date FROM laws;")
    laws = cur.fetchall()
    law_actions = [
        {
            "_index": "laws",
            "_id": row["law_id"],
            "_source": row,
        }
        for row in laws
    ]
    if law_actions:
        helpers.bulk(es, law_actions)
        print(f"[ES] laws {len(law_actions)}건 색인")

    # precedents
    cur.execute(
        "SELECT prec_id, case_name, case_no, court_name, judgment_date, case_type, summary, body FROM precedents;"
    )
    precs = cur.fetchall()
    prec_actions = [
        {
            "_index": "precedents",
            "_id": row["prec_id"],
            "_source": row,
        }
        for row in precs
    ]
    if prec_actions:
        helpers.bulk(es, prec_actions)
        print(f"[ES] precedents {len(prec_actions)}건 색인")

    cur.close()
    conn.close()


# -------------------- API → Python (Extract & Normalize) --------------------

def normalize_law(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "law_id": raw.get("법령ID"),
        "law_name_kor": raw.get("법령명한글"),
        "law_type": raw.get("법령구분명"),
        "promulgation_date": raw.get("공포일자"),   # YYYYMMDD
        "enforcement_date": raw.get("시행일자"),   # YYYYMMDD
    }


def fetch_all_laws(display: int = 100, max_pages: Optional[int] = None):
    page = 1
    while True:
        params = {
            "OC": OC,
            "target": "law",
            "type": "JSON",
            "display": display,
            "page": page,
        }
        data = get_json(BASE_SEARCH_URL, params)
        items = find_items_block(data)
        if not items:
            break

        for raw in items:
            yield normalize_law(raw)

        total = get_total_cnt(data, default=len(items))
        if page * display >= total:
            break
        if max_pages and page >= max_pages:
            break
        page += 1


def normalize_prec_detail(detail: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "prec_id": detail.get("판례일련번호") or detail.get("판례정보일련번호"),
        "case_name": detail.get("사건명"),
        "case_no": detail.get("사건번호"),
        "court_name": detail.get("법원명"),
        "judgment_date": detail.get("선고일자"),   # YYYYMMDD
        "case_type": detail.get("사건종류명"),
        "summary": detail.get("판결요지") or detail.get("판시사항"),
        "body": detail.get("판례내용"),
    }


def fetch_prec_detail(prec_serial: str) -> Optional[Dict[str, Any]]:
    params = {
        "OC": OC,
        "target": "prec",
        "type": "JSON",
        "ID": prec_serial,
    }
    data = get_json(BASE_SERVICE_URL, params)

    # 가장 안쪽에 판례내용이 있는 dict 찾기
    if "판례" in data and isinstance(data["판례"], dict):
        return normalize_prec_detail(data["판례"])
    for v in data.values():
        if isinstance(v, dict) and "판례내용" in v:
            return normalize_prec_detail(v)
    return None


def fetch_all_precedents(display: int = 100, max_pages: Optional[int] = None):
    page = 1
    while True:
        params = {
            "OC": OC,
            "target": "prec",
            "type": "JSON",
            "display": display,
            "page": page,
        }
        data = get_json(BASE_SEARCH_URL, params)
        items = find_items_block(data)
        if not items:
            break

        for raw in items:
            prec_serial = raw.get("판례일련번호")
            if not prec_serial:
                continue
            detail = fetch_prec_detail(str(prec_serial))
            if detail:
                yield detail

        total = get_total_cnt(data, default=len(items))
        if page * display >= total:
            break
        if max_pages and page >= max_pages:
            break
        page += 1


# -------------------- 메인 실행 --------------------

def run_etl(law_pages: Optional[int] = None, prec_pages: Optional[int] = None):
    create_tables()

    print("[ETL] 법령 수집 시작")
    for law in tqdm(fetch_all_laws(max_pages=law_pages), desc="법령 수집중"):
        if law["law_id"]:
            insert_law(law)
    print("[ETL] 법령 수집 & PG 저장 완료")

    print("[ETL] 판례 수집 시작")
    for prec in tqdm(fetch_all_precedents(max_pages=prec_pages), desc="판례 수집중"):
        if prec["prec_id"]:
            insert_prec(prec)
    print("[ETL] 판례 수집 & PG 저장 완료")

    create_es_indices()
    pg_to_es()
    print("[ETL] 전체 파이프라인 완료")


if __name__ == "__main__":
    # 처음엔 테스트 용으로 law_pages=1, prec_pages=1 만 돌려보고,
    # 잘 되면 None 으로 바꿔서 전체 수집하면 돼.
    #run_etl(law_pages=1, prec_pages=1)
    run_etl()  # 전체 페이지 수집
