from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
from app.api import words, settings, translate
import uvicorn

app = FastAPI(
    title="LinguaLearn API",
    description="Backend service for LinguaLearn Chrome Extension",
    version="1.0.0"
)

# CORS Configuration
# Allow all origins for extension development
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Initialize DB tables
    create_db_and_tables()

# Include Routers
app.include_router(translate.router, prefix="/api")
app.include_router(words.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "ok", "service": "LinguaLearn API"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
