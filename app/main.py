from fastapi import FastAPI, Request
import time
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
from app.api import words, settings, translate
import uvicorn

app = FastAPI(
    title="LinguaLearn API",
    description="Backend service for LinguaLearn Chrome Extension",
    version="1.0.0"
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

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
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
