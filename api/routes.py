#from hybrid_search.search import find_matching_rec
from fastapi import APIRouter, HTTPException
from api.schemas import RecommendationSchema, PDFEncodedBase64, PDFURL, RecommendationResponse
from fastapi.concurrency import run_in_threadpool
import base64
import io

from tip_generator.paper_class import Paper
from hybrid_search.search import find_matching_rec

from loguru import logger

#from hybrid_search.index import index_current_database

router = APIRouter()

@router.get("/")
def root():
    return {"message": "SUPHRA Recommendation API is running."}

@router.post("/match")
def match(request: str):
    try:
        res = find_matching_rec(request)
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
    return(res)

@router.post("/extract/url", response_model=RecommendationResponse)
def recommend_url(request: PDFURL):
    try:
        paper = Paper.build_from_url(url=request.url)
        response = RecommendationResponse(recommendations=paper.to_api_schemas())
        logger.info(f"Paper processed: {paper.doi}")
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
    return(response)
    
@router.post("/extract/base64", response_model=RecommendationResponse)
def recommend(request: PDFEncodedBase64):
    try:
        if request.file_base64 == "DEBUG_MODE" :
            fake_recommendations = [
                RecommendationSchema(
                    id=1,
                    short_desc="Recommendation 1 based on your paper.",
                    long_desc="Detailed description 1.",
                ),
                RecommendationSchema(
                    id=2,
                    short_desc="Recommendation 2 based on your paper.",
                    long_desc="Detailed description 2.",
                ),
            ]
            return RecommendationResponse(recommendations=fake_recommendations)
        else:
            # Decode the base64 PDF
            #pdf_bytes = base64.b64decode(request.file_base64)
            #pdf_file = io.BytesIO(pdf_bytes)
            return RecommendationResponse(recommendations=[])

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
