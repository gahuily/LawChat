import os
from dotenv import load_dotenv

# LawChat/.env 불러오기
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

PG_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "dbname": os.getenv("PG_DB", "lawchat"),
    "user": os.getenv("PG_USER", "wish"),
    "password": os.getenv("PG_PASSWORD", "0000"),
}

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")

LAW_API_OC = os.getenv("LAW_API_OC")
LAW_API_BASE = os.getenv("LAW_API_BASE", "https://www.law.go.kr/DRF")
