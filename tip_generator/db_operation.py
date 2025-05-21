from sqlalchemy import text, insert
from sqlalchemy.orm import Session
from sqlalchemy.types import String
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.mysql import SET, ENUM, TINYINT, YEAR
from sqlalchemy.ext.declarative import declarative_base

import sys
import pandas as pd
import json

import typer
from loguru import logger

from litellm import embedding

# initialize typer and loguru
app = typer.Typer()
logger.remove()
logger.add(sys.stdout, level="INFO")

Base = declarative_base()

class RecommendationORM(Base):
    __tablename__ = "recommendation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    short_desc = Column(String(128), nullable=True)
    long_desc = Column(String(500), nullable=True)
    goal = Column(ENUM('augment', 'prevent', 'recover', 'maintain'), nullable=True)
    activity_type = Column(ENUM('time management', 'exercise', 'cognitive', 'relax', 'social'), nullable=True)
    categories = Column(SET(
        'work', 'success', 'productivity', 'performance', 'focus', 'time management', 
        'happiness', 'mental', 'active reflection', 'awareness', 'well-being', 'health', 'fitness', 'social'
    ), nullable=True)
    concerns = Column(SET(
        'goal-setting', 'self-motivation', 'self-direction', 'self-discipline', 'focus', 
        'mindset', 'time management', 'procrastination', 'stress management', 'mental-health', 
        'work-life balance', 'sleep quality'
    ), nullable=True)
    daytime = Column(ENUM('any', 'morning', 'noon', 'evening', 'end of day'), nullable=True)
    weekdays = Column(ENUM('any', 'workdays', 'weekend', 'week start', 'end of workweek', 'public holiday'), nullable=True)
    season = Column(ENUM('any', 'spring', 'summer', 'autumn', 'winter', 'holiday season', 'summer vacation'), nullable=True)
    is_outdoor = Column(TINYINT(1), nullable=True)
    is_basic = Column(TINYINT(1), nullable=True)
    is_advanced = Column(TINYINT(1), nullable=True)
    gender = Column(String(50), nullable=True)
    src_title = Column(String(128), nullable=True)
    src_reference = Column(Text, nullable=True)
    src_pub_year = Column(YEAR, nullable=True)
    src_pub_type = Column(String(50), nullable=True)
    src_field_of_study = Column(String(64), nullable=True)
    src_doi = Column(String(255), nullable=True)
    src_hyperlink = Column(String(255), nullable=True)
    src_pub_venue = Column(String(255), nullable=True)
    src_citations = Column(Integer, nullable=True)
    src_cit_influential = Column(Integer, nullable=True)



class Embedding(Base):
    """
    SQLAlchemy model for the embeddings table.
    """
    __tablename__ = "emb_ada002"

    id = Column(Integer, primary_key=True)
    emb = Column(Text)  # VECTOR(1536)


def insert_into_db(
        recommendations: pd.DataFrame
):
    """
    Inserts recommendations that are stored in pandas DataFrame with already matching column names!
    """
    # build insertion statement
    rows = recommendations.to_dict(orient="records")
    try:
        from app import SessionLocal
        session : Session = SessionLocal()
    except ImportError:
        logger.error("SessionLocal not found!")
        return None
    # Bulk insert recommendations
    session.execute(insert(RecommendationORM), rows)
    logger.info("Successfully inserted recommendations into the database.")
    # Query 'id' and 'short_desc' of inserted recommendations
    result = session.execute(text("SELECT id, short_desc FROM recommendation WHERE id >= LAST_INSERT_ID()"))
    result = [tuple(row) for row in result.fetchall()]
    short_descs = [row[1] for row in result]
    try:
        # Extract embeddings
        emb = embedding(model='text-embedding-ada-002', input=short_descs)
        emb = [e["embedding"] for e in emb["data"]] # cut off metadata from response
        logger.info(f"Successfully extracted embeddings for {len(emb)} recommendations.")
        #logger.info("Successfully extracted embeddings.")
    except Exception as e:
        logger.error(f"Error while extracting embeddings: {e}")
        return None
    # Prepare the embeddings for sqlalchemy bulk insertion
    embeddings_data = [
        {"id": int(row[0]), "emb": json.dumps(emb[i])} for i, row in enumerate(result)
    ]
    # Build and execute the insert statement
    stmt = insert(Embedding).values(
        id=text(":id"),
        emb=text("Vec_FromText(:emb)")
    )
    try:
        session.execute(stmt, embeddings_data)
        logger.debug("Successfully inserted embeddings into the database.")
        session.commit()
        logger.debug("Committed the transaction.")
        logger.info("Upload completed.")
    # Return List of ids of inserted recommendations
    except Exception as e:
        raise Exception(f"DB-Operation: Error while inserting data: {e}")
    finally:
        session.close()
        logger.debug("Closed cursor after insert operation.")

# Delete recommendations by their ID? TODO

# run typer app
if __name__ == "__main__":
    app()
