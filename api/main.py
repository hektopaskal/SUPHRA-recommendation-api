from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="SUPHRA Recommendation API",
    description="Send a paper and get tailored recommendations.",
    version="0.1.0"
)

app.include_router(router)
