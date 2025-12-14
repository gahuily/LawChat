import os
import requests

SAVE_DIR = "data"
os.makedirs(SAVE_DIR, exist_ok=True)

URL = "https://raw.githubusercontent.com/haven-jeon/LegalQA/main/data/legalqa.jsonlines"
SAVE_PATH = os.path.join(SAVE_DIR, "legalqa.jsonl")  # jsonlines → 보통 확장자 .jsonl

def download_legalqa():
    print("⬇️ LegalQA 데이터 다운로드 중...")

    resp = requests.get(URL)
    if resp.status_code == 200:
        with open(SAVE_PATH, "wb") as f:
            f.write(resp.content)
        print(f"✅ 저장 완료: {SAVE_PATH}")
    else:
        print(f"❌ 다운로드 실패 (status code: {resp.status_code})")

if __name__ == "__main__":
    download_legalqa()
