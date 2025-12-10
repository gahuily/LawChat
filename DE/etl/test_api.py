import requests
from .config import LAW_API_OC, LAW_API_BASE

def main():
    if not LAW_API_OC:
        print("LAW_API_OC가 .env에 설정되어 있지 않습니다.")
        return

    params = {
        "OC": LAW_API_OC,
        "target": "prec",     # 판례
        "type": "JSON",       # JSON으로 받기
        "page": 1,
        "query": "절도",      # '절도' 관련 판례만 먼저 테스트
    }

    url = f"{LAW_API_BASE}/lawSearch.do"
    print("요청 URL:", url)
    resp = requests.get(url, params=params, timeout=30)
    print("HTTP status:", resp.status_code)

    data = resp.json()
    # 응답 구조를 대충 보기 위해 키만 찍어보자
    print("최상위 키들:", list(data.keys()))
    print("대충 내용 예시:", str(data)[:1000])  # 앞부분만 잘라서 출력

if __name__ == "__main__":
    main()
