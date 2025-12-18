# retriever_bm25.py

import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")


class BM25Retriever:
    """
    Elasticsearch BM25 기반 판례 검색기.
    etl.py에서 만든 'precedents' 인덱스를 사용한다.
    """

    def __init__(self, index: str = "precedents", es_host: str = ES_HOST):
        self.index = index
        self.es = Elasticsearch(es_host)

    def retrieve(self, query: str, size: int = 5) -> List[Dict[str, Any]]:
        """
        문장형 질의를 넣으면, ES에서 BM25 기반으로 상위 N개 판례를 찾아서 반환.
        """
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "case_name^3",  # 사건명 가중치 높게
                        "summary^2",    # 요약
                        "body"          # 본문
                    ]
                }
            },
            "size": size
        }

        res = self.es.search(index=self.index, body=body)

        hits = res["hits"]["hits"]
        results = []
        for h in hits:
            source = h["_source"]
            source["_score"] = h["_score"]
            results.append(source)
        return results


if __name__ == "__main__":
    retriever = BM25Retriever(index="precedents")

    # 테스트용 질의: 여기 원하는 문장형 질의 아무거나 넣어봐도 됨
    test_query = "전세보증금을 돌려받지 못한 경우 임대인의 책임"
    results = retriever.retrieve(test_query, size=3)

    print(f"질의: {test_query}")
    print("=== 검색 결과 상위 3개 ===")
    for i, r in enumerate(results, start=1):
        print(f"\n[{i}] 사건명: {r.get('case_name')}")
        print(f"    사건번호: {r.get('case_no')}")
        print(f"    법원: {r.get('court_name')}")
        print(f"    선고일자: {r.get('judgment_date')}")
        print(f"    점수: {r.get('_score')}")
        summary = (r.get("summary") or "").strip()
        if summary:
            print(f"    요지: {summary[:150]}{'...' if len(summary) > 150 else ''}")
