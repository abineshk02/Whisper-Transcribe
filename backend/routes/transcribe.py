import os
import asyncio
import datetime
import logging
import pathlib
import aiohttp
import yt_dlp
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import TranscriptionRecord
from whisper_utils import load_model

router = APIRouter(prefix="/transcribe", tags=["Transcription"])
logger = logging.getLogger(__name__)

# Directories
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load Whisper model
logger.info("Loading Whisper model...")
model = load_model("small")
logger.info("Whisper model loaded successfully.")


# -------------------------------
# Helper: Transcribe audio
# -------------------------------
def transcribe_audio_sync(file_path, model):
    return model.transcribe(file_path)["text"]


# -------------------------------
# URL Transcription
# -------------------------------
class URLTranscriptionRequest(BaseModel):
    file_url: str
    user_id: int = 0


@router.post("/transcribe-url")
async def transcribe_from_url(request: URLTranscriptionRequest, db: Session = Depends(get_db)):
    file_url = request.file_url.strip()
    user_id = request.user_id

    try:
        # Convert YouTube Shorts URLs to standard watch URLs
        if "youtube.com/shorts/" in file_url:
            video_id = file_url.split("/shorts/")[1].split("?")[0]
            file_url = f"https://www.youtube.com/watch?v={video_id}"

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        local_file_path = os.path.join(UPLOAD_DIR, f"download_{timestamp}.mp3")
        local_file_path = str(pathlib.Path(local_file_path).resolve())  # absolute path

        # Case 1: Direct audio/video file
        if any(file_url.lower().endswith(ext) for ext in [".mp3", ".wav", ".m4a", ".mp4", ".aac", ".ogg", ".flac"]):
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as resp:
                    if resp.status != 200:
                        return JSONResponse(status_code=400, content={"error": "Failed to download file"})
                    content = await resp.read()
                    if not content:
                        return JSONResponse(status_code=400, content={"error": "Downloaded file is empty"})
                    with open(local_file_path, "wb") as f:
                        f.write(content)

        # Case 2: YouTube or other video links
        else:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": local_file_path.replace("\\", "/"),
                "quiet": True,
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([file_url])
            except Exception as e:
                return JSONResponse(status_code=400, content={"error": f"yt-dlp failed: {str(e)}"})

        # Verify file exists
        if not os.path.exists(local_file_path):
            return JSONResponse(status_code=400, content={"error": "Local file not found for transcription"})

        # Transcribe asynchronously
        loop = asyncio.get_event_loop()
        transcript_text = await loop.run_in_executor(None, transcribe_audio_sync, local_file_path, model)

        # Save transcript
        transcript_filename = f"transcription_{timestamp}.txt"
        transcript_file_path = os.path.join(OUTPUT_DIR, transcript_filename)
        with open(transcript_file_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)

        # Store in DB
        with open(local_file_path, "rb") as f:
            uploaded_bytes = f.read()

        record = TranscriptionRecord(
            user_id=user_id,
            file_name=os.path.basename(local_file_path),
            uploaded_file=uploaded_bytes,
            transcript_file=transcript_text.encode("utf-8")
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "message": "Transcription completed successfully",
            "transcript": transcript_text,
            "transcript_filename": transcript_filename
        }

    except Exception as e:
        logger.exception("Error during URL transcription")
        return JSONResponse(status_code=500, content={"error": str(e)})


# -------------------------------
# File Upload Transcription
# -------------------------------
@router.post("/transcribe-file")
async def transcribe_file(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        local_file_path = os.path.join(UPLOAD_DIR, file.filename)
        local_file_path = str(pathlib.Path(local_file_path).resolve())  # Absolute path

        # Save uploaded file
        with open(local_file_path, "wb") as f:
            f.write(await file.read())

        if not os.path.exists(local_file_path):
            return JSONResponse(status_code=400, content={"error": "Uploaded file not saved"})

        # Transcribe
        loop = asyncio.get_event_loop()
        transcript_text = await loop.run_in_executor(None, transcribe_audio_sync, local_file_path, model)

        # Save transcript
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        transcript_filename = f"transcription_{timestamp}.txt"
        transcript_file_path = os.path.join(OUTPUT_DIR, transcript_filename)
        with open(transcript_file_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)

        # Store in DB
        with open(local_file_path, "rb") as f:
            uploaded_bytes = f.read()

        record = TranscriptionRecord(
            user_id=user_id,
            file_name=file.filename,
            uploaded_file=uploaded_bytes,
            transcript_file=transcript_text.encode("utf-8")
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "message": "File transcription completed successfully",
            "transcript": transcript_text,
            "transcript_filename": transcript_filename
        }

    except Exception as e:
        logger.exception("Error during file transcription")
        return JSONResponse(status_code=500, content={"error": str(e)})


# -------------------------------
# Download Endpoint
# -------------------------------
@router.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    return JSONResponse(status_code=404, content={"error": "File not found"})
