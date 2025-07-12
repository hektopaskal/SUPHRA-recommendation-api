import os
import requests
import json
from dotenv import load_dotenv


from pydantic import BaseModel
from unstructured.partition.pdf import partition_pdf
import requests
import base64
from io import BytesIO

from semanticscholar import SemanticScholar

import typer
from typing import Optional, List
from loguru import logger

from litellm import completion
from litellm.exceptions import APIError

from api.exceptions import DOIExtractionError, PDFDownloadError, PDFParseError, SemanticScholarError, OpenAIError
from tip_generator.generate import generate_recommendations

from api.schemas import RecommendationSchema

load_dotenv()

SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
SEMANTIC_SCHOLAR_FIELDS = [
    # 'abstract',
    # 'authors',
    # 'authors.affiliations',
    # 'authors.aliases',
    # 'authors.authorId',
    # 'authors.citationCount',
    # 'authors.externalIds',
    # 'authors.hIndex',
    # 'authors.homepage',
    # 'authors.name',
    # 'authors.paperCount',
    # 'authors.url',
    'citationCount',
    # 'citationStyles',
    # 'citations',
    # 'citations.abstract',
    # 'citations.authors',
    # 'citations.citationCount',
    # 'citations.citationStyles',
    # 'citations.corpusId',
    # 'citations.externalIds',
    # 'citations.fieldsOfStudy',
    # 'citations.influentialCitationCount',
    # 'citations.isOpenAccess',
    # 'citations.journal',
    # 'citations.openAccessPdf',
    # 'citations.paperId',
    # 'citations.publicationDate',
    # 'citations.publicationTypes',
    # 'citations.publicationVenue',
    # 'citations.referenceCount',
    # 'citations.s2FieldsOfStudy',
    # 'citations.title',
    # 'citations.url',
    # 'citations.venue',
    # 'citations.year',
    # 'corpusId',
    # 'embedding',
    # 'externalIds',
    'fieldsOfStudy',
    'influentialCitationCount',
    # 'isOpenAccess',
    # 'journal',
    # 'openAccessPdf',
    # 'paperId',
    # 'publicationDate',
    'publicationTypes',
    'publicationVenue',
    # 'referenceCount',
    # 'references',
    # 'references.abstract',
    # 'references.authors',
    # 'references.citationCount',
    # 'references.citationStyles',
    # 'references.corpusId',
    # 'references.externalIds',
    # 'references.fieldsOfStudy',
    # 'references.influentialCitationCount',
    # 'references.isOpenAccess',
    # 'references.journal',
    # 'references.openAccessPdf',
    # 'references.paperId',
    # 'references.publicationDate',
    # 'references.publicationTypes',
    # 'references.publicationVenue',
    # 'references.referenceCount',
    # 'references.s2FieldsOfStudy',
    # 'references.title',
    # 'references.url',
    # 'references.venue',
    # 'references.year',
    # 's2FieldsOfStudy',
    'title',
    # 'tldr',
    'url',
    # 'venue',
    'year'
]

def fetch_metadata(doi: str):
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
    fields = {"fields": ",".join(SEMANTIC_SCHOLAR_FIELDS)}
    headers = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY}
    try:
        response = requests.get(url, params=fields, headers=headers)
        response.raise_for_status()
    except requests.exceptions as http_err:
        raise SemanticScholarError(f"Error while fetching meta data from SemanticScholar: {http_err}")
    print(response.json())
    with open("response.json", "w") as f:
        f.write(json.dumps(response.json(), indent=4))
    return response.json()

class Paper(BaseModel):
    doi: str # Main identifier!
    content: str # Full text of the paper
    title: Optional[str] = None
    reference: Optional[str] = None
    pub_year: Optional[int] = None
    pub_type: Optional[str] = None
    field_of_study: Optional[str] = None
    hyperlink: Optional[str] = None
    pub_venue: Optional[str] = None
    citations: Optional[int] = None
    cit_influential: Optional[int] = None
    recommendations: List["Recommendation"] = []

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True


    def __repr__(self):
        return f"<Paper: DOI: {self.doi}, Content: {self.content[:50]}...>"
    
    @classmethod
    def build_from_url(cls, url: str) -> Optional["Paper"]:
        """
        Combining methods for better workflow.
        """
        p = cls.init_from_url(url).add_meta_data().generate_recommendations()
        """if p is None:
            logger.error("Failed to initialize Paper from URL.")
            return None
        if not p.add_meta_data():
            logger.error("Failed to add metadata to Paper.")
            return None
        if p.generate_recommendations() is None:
            logger.error("Failed to generate recommendations for Paper.")
            return None
        logger.info("Paper object successfully created with metadata and recommendations.")"""
        return p


    @classmethod
    def init_from_url(cls, url: str) -> Optional["Paper"]:
        """
        Create a Paper object from a URL that points to a PDF file.
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0"
                "AppleWebKit/537.36"
                "Chrome/123.0.0.0"
            ),
            "Accept": "application/pdf",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive", 
        }
        try:
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status() # Raises an exceptions for bad responses
        except requests.exceptions as http_err:
            raise PDFDownloadError(f"Failed to download PDF: {http_err}", status_code=response.status_code)
        except requests.RequestException as req_err:
            raise PDFDownloadError(f"Network error while downloading PDF: {req_err}")
        logger.info(f"Response Content-Type: {response.headers.get('Content-Type')}")
        logger.info(f"PDF downloaded from {url[:30]}...")
        pdf_buffer = BytesIO() # Create a BytesIO buffer object to hold the PDF content
        for chunk in response.iter_content(chunk_size=8192): # Read in chunks (8KB)
            if chunk:
                pdf_buffer.write(chunk)
        pdf_buffer.seek(0)  # Rewind the buffer to the beginning
        logger.info("Extracting text from PDF...")
        try:
            elements = partition_pdf(file=pdf_buffer)
        except Exception as e:
            raise PDFParseError(f"Failed to parse PDF: {e}")
        # Access the text content
        text = "\n".join([str(el) for el in elements])
        logger.info("PDF Object initialized.")
        return cls(doi=cls.get_doi(text), content=text)

    
    @classmethod
    def from_base64(cls, base64_string: str) -> "Paper":
        """
        Create a Paper object from a base64-encoded PDF string.
        """
        # TODO Exception handling
        # Decode the base64 string
        pdf_bytes = base64.b64decode(base64_string)
        # Wrap it in a BytesIO object
        pdf_stream = BytesIO(pdf_bytes)
        # Extract text from the PDF
        try:
            elements = partition_pdf(file=pdf_stream)
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            return None
        # Access the text content
        text = "\n".join([str(el) for el in elements])
        return cls(cls.get_doi(text), text)

    @staticmethod
    def get_doi(text) -> str:
        """
        Extract the DOI from a scientific paper's fulltext.
        """
        try:
            response = completion(
                model="gpt-4o-mini",
                messages=[
                    {'role': 'system',
                    'content': "You are analyzing scientific papers. Read the text and extract the DOI of the paper. Your output should either be the DOI (e.g. 10.1000/182) and nothing else or 'DOI_not_found' if the DOI is not available in the text."},
                    {'role': 'user', 'content': f'Analyze the following text and find its DOI: {text}'}
                ],
                temperature=0.0,
                top_p=0.0
            )
            doi = response.choices[0].message.content
            logger.info(f"DOI: {doi}")
            return doi
        except APIError as e:
            logger.error(f"Error extracting DOI: {e}")
            raise DOIExtractionError(str(e)) from e

    def add_meta_data(self) -> "Paper":
        logger.info(f"Fetching metadata for DOI {self.doi}...")
        meta_data = fetch_metadata(self.doi)
        logger.info(f"Metadata fetched for DOI {self.doi}.")
        
        self.title = meta_data.get("title")
        self.pub_year = meta_data.get("year")
        self.pub_type = ", ".join(meta_data.get("publicationTypes"))
        self.field_of_study = ", ".join(meta_data.get("fieldsOfStudy"))
        self.hyperlink = meta_data.get("url")
        self.pub_venue = meta_data.get("publicationVenue", {}).get("name", "None")
        self.citations = meta_data.get("citationCount")
        self.cit_influential = meta_data.get("influentialCitationCount")
        
        logger.info(f"Metadata added successfully for DOI {self.doi}.")
        return self

    def generate_recommendations(self) -> int:
        """
        Generate recommendations based on the paper's content using a language model.
        """
        try:
            recommendations = generate_recommendations(
                input_text=self.content
            )
        except APIError as e:
            logger.error(f"Generate-Function: {e} - Skipping this file!\n")
            raise OpenAIError(f"Failed to generate recommendations: {e}")
        # Map recommendations from llm response to self.recommendations
        self.recommendations = [self.Recommendation(**rec["recommendation_set"][0]) for rec in recommendations["output"]]
        # Return number of generated recommendations, if 'None' process failed
        return len(self.recommendations)

    def to_api_schemas(self) -> List[RecommendationSchema]:
        return [
            RecommendationSchema(
                short_desc=r.short_desc,
                long_desc=r.long_desc,
                goal=r.goal,
                activity_type=r.activity_type,
                categories=r.categories,
                concerns=r.concerns,
                daytime=r.daytime,
                weekdays=r.weekdays,
                season=r.season,
                is_outdoor=r.is_outdoor,
                is_basic=r.is_basic,
                is_advanced=r.is_advanced,
                gender=r.gender,
                src_title=self.title,
                src_reference=self.reference,
                src_pub_year=self.pub_year,
                src_pub_type=self.pub_type,
                src_field_of_study=self.field_of_study,
                src_doi=self.doi,
                src_hyperlink=self.hyperlink,
                src_pub_venue=self.pub_venue,
                src_citations=self.citations,
                src_cit_influential=self.cit_influential
            )
            for r in self.recommendations
        ]
    

    class Recommendation(BaseModel):
        short_desc: str
        long_desc: str
        goal: str
        activity_type: str
        categories: List[str]
        concerns: List[str]
        daytime: str
        weekdays: str
        season: str
        is_outdoor: bool
        is_basic: bool
        is_advanced: bool
        gender: str

        def __repr__(self):
            return f"<Recommendation: {self.short_desc[:50]}...>"
        
        @classmethod
        def from_dict(cls, rec_dict : dict):
            """
            Create a Recommendation object from a dictionary.
            """
            return cls(**rec_dict)
