# setup/setup_hybrid_search.py
from opensearchpy import OpenSearch
import os
from dotenv import load_dotenv
import time

from loguru import logger

load_dotenv()

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_auth=("admin", "Mind2@Mind"),
    use_ssl=True,
    verify_certs=True,
    ca_certs=os.getenv("OPENSEARCH_CERT"),
    ssl_assert_hostname=False,
    ssl_show_warn=False
)

index_name = "nlp-index-recommendations"
model_id = None


def set_cluster_settings():
    settings_body = {
        "persistent": {
            "plugins.ml_commons.only_run_on_ml_node": "false",
            "plugins.ml_commons.model_access_control_enabled": "true",
            "plugins.ml_commons.native_memory_threshold": "99"
        }
    }
    try:
        client.cluster.put_settings(body=settings_body)
        logger.info("Cluster settings updated to enable model management.")
    except Exception as e:
        logger.error(f"Failed to set cluster settings: {e}")
        return

def wait_for_model_registration(task_id: str, timeout=60, interval=10):
    """Poll the task until model is ready or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = client.transport.perform_request("GET", f"/_plugins/_ml/tasks/{task_id}")
            state = response.get("state")
            if state == "COMPLETED":
                return True
            elif state == "FAILED":
                logger.error(f"Model registration failed: {response.get('error')}")
                return False
            else:
                logger.info(f"Task state: {state}, waiting...")
        except Exception as e:
            logger.warning(f"Error checking task status: {response} Error: {e}")
        time.sleep(interval)
    logger.error("Timed out waiting for model registration.")
    return False

def register_model():
    global model_id

    try:
        response = client.transport.perform_request(
            method="POST",
            url="/_plugins/_ml/models/_register",
            body={
                "name": "huggingface/sentence-transformers/msmarco-distilbert-base-tas-b",
                "version": "1.0.2",
                "model_format": "TORCH_SCRIPT"
            }
        )
        task_id = response.get("task_id")
        logger.info(f"Model registration initiated with task ID: {task_id}")
    except Exception as e:
        logger.error(f"Failed to register model: {response} Error: {e}")
        return
    wait_for_model_registration(task_id)
    try:
        response = client.transport.perform_request(
            method="GET",
            url=f"/_plugins/_ml/tasks/{task_id}"
        )
        model_id = response.get("model_id")
        print(response)
        logger.info(f"Model registered with ID: {model_id}")
    except Exception as e:
        logger.error(f"Failed to get task status: {response} Error: {e}")
        return



def create_ingest_pipeline():
    pipeline_body = {
        "description": "Ingest pipeline for text embedding",
        "processors": [
            {
                "text_embedding": {
                    "model_id": model_id,
                    "field_map": {
                        "text": "passage_embedding"
                    }
                }
            }
        ]
    }
    try:
        client.ingest.put_pipeline(id="nlp-ingest-pipeline", body=pipeline_body)
        logger.info("Ingest pipeline 'nlp-ingest-pipeline' created.")
    except Exception as e:
        logger.error(f"Failed to create ingest pipeline: {e}")
        return

def create_index():
    if client.indices.exists(index=index_name):
        logger.info(f"Index '{index_name}' already exists.")
        return

    mapping = {
        "settings": {
            "index.knn": "true",
            "default_pipeline": "nlp-ingest-pipeline"
        },
        "mappings": {
            "properties": {
            "id": {
                "type": "text"
            },
            "passage_embedding": {
                "type": "knn_vector",
                "dimension": 768,
                "space_type": "l2"
            },
            "text": {
                "type": "text"
            }
            }
        }
    }
    
    try:
        client.indices.create(index=index_name, body=mapping)
        logger.info(f"Created index '{index_name}'")
    except Exception as e:
        logger.error(f"Failed to create index '{index_name}': {e}")
        return


def deploy_model():
    global model_id

    if not model_id:
        logger.error("No model_id found to deploy.")
        return

    deploy_url = f"/_plugins/_ml/models/{model_id}/_deploy"
    response = client.transport.perform_request("POST", deploy_url)
    logger.info(f"Deployment response: {response}")

    # Wait for deployment to complete
    time.sleep(5)
    status_url = f"/_plugins/_ml/models/{model_id}"
    try:
        status = client.transport.perform_request("GET", status_url)
        logger.info(f"Model status: {status.get('model_state')}")
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        return


def create_search_pipeline():
    pipeline_body = {
        "description": "Post processor for hybrid search",
        "phase_results_processors": [
            {
                "normalization-processor": {
                    "normalization": {
                        "technique": "min_max"
                    },
                    "combination": {
                        "technique": "arithmetic_mean",
                        "parameters": {
                            "weights": [0.3, 0.7]
                        }
                    }
                }
            }
        ]
    }

    try:
        client.transport.perform_request(
            method="PUT",
            url="/_search/pipeline/nlp-hybrid-search-pipeline",
            body=pipeline_body
        )
        logger.info("Search pipeline 'nlp-hybrid-search-pipeline' created.")
    except Exception as e:
        logger.error(f"Failed to create search pipeline: {e}")
        return


if __name__ == "__main__":
    set_cluster_settings()
    time.sleep(5)  # Wait for the cluster settings to take effect
    register_model()
    time.sleep(5)  # Wait for the model to be registered
    create_ingest_pipeline()
    time.sleep(5)  # Wait for the ingest pipeline to be created
    create_index()
    time.sleep(5)  # Wait for the model to be deployed
    deploy_model()
    time.sleep(5)  # Wait for the index to be created
    create_search_pipeline()
    logger.info("Hybrid search setup complete.")
