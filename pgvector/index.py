import pandas as pd
import json

from transformers import AutoModel

import mariadb
from sqlalchemy import text, insert, func, bindparam
from sqlalchemy.orm import Session
from sqlalchemy.types import TypeDecorator, String
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.mysql import SET, ENUM, TINYINT, YEAR
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Embedding(Base):
    """
    SQLAlchemy model for the embeddings table.
    """
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True)
    emb = Column(Text)  # VECTOR(1536)

DATABASE_URL = "mariadb+mariadbconnector://thrams:addyaddy2020%%@tessa.gg01.local:3306/copy_fellmann"
# Engine for connection pool
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
try:
    engine.connect()
    print("Database connection established successfully.")
except Exception as e:
    print(f"Error connecting to the database: {e}")
    engine = None
    SessionLocal = None

session = SessionLocal()
try:
    result = session.execute(text("SELECT id, short_desc, long_desc FROM recommendation"))

    # Extract rows as list of tuples
    rows = result.fetchall()
    columns = result.keys()
    df = pd.DataFrame(rows, columns=columns)

finally:
    # Always close the session
    session.close()

short_descs = df["short_desc"].tolist()
long_descs = df["long_desc"].tolist()
recs = [f"{short}, {long}" for short, long in zip(short_descs, long_descs)]
print(f"RECS: {recs[:5]}")  # Print first 5 recommendations to verify

model_name = "jinaai/jina-embeddings-v3"
try:
    model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
    print("Model loaded successfully!")
except Exception as e:
    print("Error loading model:", e)
try:
    embeddings = model.encode(recs, convert_to_tensor=True)
    print("Embeddings encoded successfully!")
except Exception as e:
    print("Error encoding embeddings:", e)

embeddings = embeddings.numpy().tolist()
print(f"EMBEDDINGS: {embeddings[:2]}")  # Print first 5 embeddings to verify
embeddings_data = [
    {"id": int(row[0]), "emb": json.dumps(embeddings[i])} 
    for i, row in enumerate(rows)
]
print(f"EMBS: {embeddings_data[:5]}")  # Print a few entries to verify
# Build and execute the insert statement
stmt = insert(Embedding).values(
    id=bindparam("id"),
    emb=bindparam("emb")
)

session : Session = SessionLocal()
session.execute(stmt, embeddings_data)
session.commit()
session.close()
