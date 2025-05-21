from pydantic import BaseModel
from typing import List, Optional

class PDFEncodedBase64(BaseModel):
    file_base64: str

class PDFURL(BaseModel):
    url: str

class RecommendationSchema(BaseModel):
    id: Optional[int] = None
    short_desc: Optional[str] = None
    long_desc: Optional[str] = None
    goal: Optional[str] = None
    activity_type: Optional[str] = None
    categories: Optional[List[str]] = None
    concerns: Optional[List[str]] = None
    daytime: Optional[str] = None
    weekdays: Optional[str] = None
    season: Optional[str] = None
    is_outdoor: Optional[bool] = None
    is_basic: Optional[bool] = None
    is_advanced: Optional[bool] = None
    gender: Optional[str] = None
    src_title: Optional[str] = None
    src_reference: Optional[str] = None
    src_pub_year: Optional[int] = None
    src_pub_type: Optional[str] = None
    src_field_of_study: Optional[str] = None
    src_doi: Optional[str] = None
    src_hyperlink: Optional[str] = None
    src_pub_venue: Optional[str] = None
    src_citations: Optional[int] = None
    src_cit_influential: Optional[int] = None

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationSchema]
