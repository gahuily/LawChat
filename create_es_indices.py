from elasticsearch import Elasticsearch

def create_precedents_index(es: Elasticsearch):
    body = {
        "settings": {
            "analysis": {
                "tokenizer": {
                    "korean_tokenizer": {
                        "type": "nori_tokenizer"
                    }
                },
                "analyzer": {
                    "korean_analyzer": {
                        "type": "custom",
                        "tokenizer": "korean_tokenizer",
                        "filter": [
                            "lowercase",
                            "nori_part_of_speech"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "prec_id":      {"type": "keyword"},
                "case_no":      {"type": "keyword"},
                "case_name":    {"type": "text", "analyzer": "korean_analyzer"},
                "court_name":   {"type": "keyword"},
                "judgment_date":{"type": "date"},
                "summary":      {"type": "text", "analyzer": "korean_analyzer"},
                "full_text":    {"type": "text", "analyzer": "korean_analyzer"}
            }
        }
    }
    es.indices.create(index="precedents", body=body, ignore=400)
    print("precedents 인덱스 생성 (또는 이미 존재).")

def create_laws_index(es: Elasticsearch):
    body = {
        "settings": {
            "analysis": {
                "tokenizer": {
                    "korean_tokenizer": {
                        "type": "nori_tokenizer"
                    }
                },
                "analyzer": {
                    "korean_analyzer": {
                        "type": "custom",
                        "tokenizer": "korean_tokenizer",
                        "filter": [
                            "lowercase",
                            "nori_part_of_speech"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "law_id":          {"type": "keyword"},
                "law_name_kor":    {"type": "text", "analyzer": "korean_analyzer"},
                "law_type":        {"type": "keyword"},
                "promulgation_date":{"type": "date"},
                "enforcement_date":{"type": "date"}
            }
        }
    }
    es.indices.create(index="laws", body=body, ignore=400)
    print("laws 인덱스 생성 (또는 이미 존재).")

if __name__ == "__main__":
    es = Elasticsearch("http://localhost:9200")
    print(es.info())
    create_precedents_index(es)
    create_laws_index(es)
