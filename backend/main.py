from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, transcribe
from database import Base, engine
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(title="Whisper Transcription API")

# Allow frontend access (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Register routes
app.include_router(auth.router)
app.include_router(transcribe.router)

@app.get("/")
def root():
    return {"message": "Welcome to Whisper API 🚀"}
