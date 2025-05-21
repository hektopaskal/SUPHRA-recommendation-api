from loguru import logger

from opensearchpy import OpenSearch

from dotenv import load_dotenv
load_dotenv()
import os

# Connect to OpenSearch
client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9200}],
    http_auth=('admin', 'Mind2@Mind'),  # Adjust if needed
    use_ssl=True,
    verify_certs=True,
    ca_certs=os.getenv("OPENSEARCH_CERT"),  # Adjust path
    ssl_assert_hostname=False,
    ssl_show_warn=False
)

def find_matching_rec(query_text: str) -> dict:
    """
    Function to find matching recommendations based on a query text.
    This function uses a hybrid search approach combining traditional keyword search
    and neural search using OpenSearch.
    """
    
    search_body = {
        "_source": {
            "exclude": ["passage_embedding"]
        },
        "size": 5,
        "query": {
            "hybrid": {
                "queries": [
                    {
                        "match": {
                            "text": {
                                "query": query_text
                            }
                        }
                    },
                    {
                        "neural": {
                            "passage_embedding": {
                                "query_text": query_text,
                                "model_id": "Fz-n8pYBY6N441KF24tA",
                                "k": 3
                            }
                        }
                    }
                ]
            }
        }
    }
    try:
        # Execute the search with the pipeline
        response = client.search(
            index="nlp-index-recommendations",
            body=search_body,
            params={"search_pipeline": "nlp-hybrid-search-pipeline"}
        )
    except Exception as e:
        logger.error(f"Error executing search: {e}")
        return {"error": str(e)}

    results = [
        {
            "id": hit["_id"],
            "score": hit["_score"],
            "text": hit["_source"].get("text", "")
        }
        for hit in response["hits"]["hits"]
    ]
    return results
