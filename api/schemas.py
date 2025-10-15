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
    weather: Optional[str] = None
    is_basic: Optional[bool] = None
    is_advanced: Optional[bool] = None
    gender: Optional[str] = None
    
    class Config:
        from_attributes = True

class PaperSchema(BaseModel):
    title: Optional[str] = None
    reference: Optional[str] = None
    pub_year: Optional[int] = None
    pub_type: Optional[str] = None
    field_of_study: Optional[str] = None
    doi: Optional[str] = None
    hyperlink: Optional[str] = None
    pub_venue: Optional[str] = None
    citations: Optional[int] = None
    cit_influential: Optional[int] = None

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    paper: PaperSchema
    recommendations: List[RecommendationSchema]
