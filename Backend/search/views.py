from django.http import JsonResponse
from django.views import View
from elasticsearch import Elasticsearch

# 가장 단순하게: 여기에서 바로 ES 클라이언트 생성
es = Elasticsearch("http://localhost:9200")


class SearchPrecedentsView(View):
    def get(self, request):
        # 쿼리 파라미터 q 가져오기: /search?q=...
        query = request.GET.get("q")

        if not query:
            return JsonResponse({"error": "q 파라미터를 입력하세요. 예: /search?q=전세보증금"}, status=400)

        # Elasticsearch 검색 요청 내용 (Top 3)
        body = {
            "size": 3,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["case_name^3", "summary^2", "full_text"],
                }
            },
        }

        try:
            res = es.search(index="precedents", body=body)
        except Exception as e:
            # ES에 문제 있을 때 에러 반환
            return JsonResponse({"error": f"Elasticsearch error: {e}"}, status=500)

        hits = []
        for hit in res["hits"]["hits"]:
            src = hit["_source"]
            hits.append({
                "prec_id": src.get("prec_id"),
                "case_no": src.get("case_no"),
                "case_name": src.get("case_name"),
                "court_name": src.get("court_name"),
                "judgment_date": src.get("judgment_date"),
                "summary": src.get("summary"),
                "score": hit.get("_score"),
            })

        return JsonResponse({"results": hits}, json_dumps_params={"ensure_ascii": False})
