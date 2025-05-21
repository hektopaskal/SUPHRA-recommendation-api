import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import shutil

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

from tip_generator.generate import generate_recommendations

load_dotenv()

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
    def from_url(cls, url: str):
        """
        Create a Paper object from a URL that points to a PDF file.
        """
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/pdf",
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status() # Raises an HTTPError for bad responses
        logger.info(f"PDF downloaded from {url[:50]}...")
        pdf_buffer = BytesIO() # Create a BytesIO buffer object to hold the PDF content
        for chunk in response.iter_content(chunk_size=8192): # Read in chunks (8KB)
            if chunk:
                pdf_buffer.write(chunk)
        pdf_buffer.seek(0)  # Rewind the buffer to the beginning
        logger.info("Extracting text from PDF...")
        try:
            elements = partition_pdf(file=pdf_buffer)
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            return None
        # Access the text content
        text = "\n".join([str(el) for el in elements])
        logger.info("PDF Object initialized.")
        return cls(cls.get_doi(text), text)

    
    @classmethod
    def from_base64(cls, base64_string: str):
        """
        Create a Paper object from a base64-encoded PDF string.
        """
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
        except Exception as e:
            logger.error(f"Error extracting DOI: {e}")
            return None

    def add_meta_data(self) -> bool:
        sch = SemanticScholar(api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY"))
        try:
            meta_data = sch.get_paper(self.doi, fields=SEMANTIC_SCHOLAR_FIELDS)
        except Exception as e:
            logger.error(f"Semantic-Scholar-API-Error occured: {e} - Skipping this file!")
            return False
        
        # Insert attribute values from Semantic Scholar object
        self.title = getattr(meta_data, "title"),
        #"src_reference"
        self.pub_year = getattr(meta_data, "year"),
        #"src_is_journal"
        self.pub_type = getattr(meta_data, "publicationTypes"),
        self.field_of_study = getattr(meta_data, "fieldsOfStudy"),
        #"src_doi"
        self.hyperlink = getattr(meta_data, "url"),
        self.pub_venue = json.loads(str(getattr(meta_data, "publicationVenue")).replace("'", '"'))["name"] if not getattr(meta_data, "publicationVenue") == None else "None" ,
        self.citations = getattr(meta_data, "citationCount"),
        self.cit_influential = getattr(meta_data, "influentialCitationCount")
        return True
    
    def generate_recommendations(self) -> int:
         # Generate recommendations
        try:
            recommendations = generate_recommendations(
                input_text=self.content
            )
        except Exception as e:
            logger.error(f"Generate-Function: {e} - Skipping this file!\n")
            return None
        # Map recommendations from llm response to self.recommendations
        self.recommendations = [self.Recommendation(**rec["recommendation_set"][0]) for rec in recommendations["output"]]
        # Return number of generated recommendations, if 'None' process failed
        return len(self.recommendations)

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

    def extract_recommendations(self):
        """
        Extract recommendations from the paper's content.
        """


    def add_recommendation(self, text, page_number=None):
        recommendation = self.Recommendation(text, page_number)
        self.recommendations.append(recommendation)

    def list_recommendations(self):
        return self.recommendations