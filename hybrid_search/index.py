from opensearchpy import OpenSearch, helpers
import requests
from requests.auth import HTTPBasicAuth
import json

import numpy as np
import pandas as pd

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from loguru import logger
import sys
import ast
# Initialize logger
logger.remove()
logger.add(sys.stdout, level="INFO")

import os
from dotenv import load_dotenv
load_dotenv()

OPENS_URL = "localhost"
OPENS_AUTH=("admin", "Mind2@Mind")

DATABASE_URL = os.environ.get("DATABASE_URL")
table_name = 'recommendation' # emb_ada002 emb_jina3 emb_bert
ca_certs_path = os.environ.get("OPENSEARCH_CERT")

# Create the client with SSL/TLS enabled, but hostname verification disabled.
client = OpenSearch(
    hosts = [{'host': OPENS_URL, 'port': 9200}],
    http_compress = True, # enables gzip compression for request bodies
    http_auth = OPENS_AUTH,
    use_ssl = True,
    verify_certs = True,
    ssl_assert_hostname = False,
    ssl_show_warn = False,
    ca_certs = ca_certs_path
)



# Create DB connection pool
DATABASE_URL = os.getenv("DATABASE_URL")
# Engine for connection pool
logger.info("Initializing database connection pool")
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=False
    )
    # SessionLocal hands out a session from the pool when needed
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"Failed to initialize database connection pool: {e}")
    engine = None
    SessionLocal = None



def index_current_database():
    try:
        session : Session = SessionLocal()
    except ImportError:
        logger.error("SessionLocal not found!")
        return None
    
    # retrieve id, tip from database
    try:
        result = session.execute(text("SELECT id, short_desc, long_desc FROM recommendation"))
        
        rows = result.fetchall()
        columns = result.keys()
        df = pd.DataFrame(rows, columns=columns)
    finally:
        session.close()

    # short_descs = df["short_desc"].tolist()
    input =[]

    for short, long in zip(df["short_desc"].tolist(), df['long_desc'].tolist()):
        input.append(f'{short} {long}')
    print(input[0])
    print(input[2])
    print(df)

    # Build the bulk request body
    bulk_actions = [
        {
            "_op_type": "index",
            "_index": "nlp-index-recommendations",
            "_id": row["id"],
            "_source": {
                "text": f"{row['short_desc']} {row['long_desc']}",
            },
            "pipeline": "nlp-ingest-pipeline"  # This is key for embedding
        }
        for _, row in df.iterrows()
    ]
    
    # 4. Execute bulk insert
    response = helpers.bulk(client, bulk_actions)
    print("Inserted:", response)

try:
    index_current_database()
except Exception as e:
    logger.error(f"Failed to index current database: {e}")
    raise