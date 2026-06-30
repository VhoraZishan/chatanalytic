import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from parser import parse_whatsapp_chat
from analytics import run_analytics
from llm import generate_report_commentary

app = FastAPI(title="Chat Analytic API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_chat(file: UploadFile = File(...), chat_mode: str = Form("group")):
    """
    Handles uploading a WhatsApp .txt export.
    Parses, runs analytics, queries Gemini, and returns the report in a single ephemeral request.
    """
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    if chat_mode not in ("dm", "group"):
        chat_mode = "group"

    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Parse chat in-memory
        chat_data = parse_whatsapp_chat(temp_path, file.filename.replace('.txt', ''), chat_mode)
        
        # 2. Run in-memory analytics
        payload = run_analytics(chat_data)
        if "error" in payload:
            raise HTTPException(status_code=400, detail=payload["error"])
            
        # 3. Call Gemini to generate the roasts
        try:
            commentary = generate_report_commentary(payload, chat_mode=chat_mode)
        except Exception as e:
            print(f"Failed to generate commentary: {e}")
            commentary = {}
            
        # 4. Merge roasts directly into the response payload
        payload['ai_roast'] = commentary
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Privacy: Delete raw uploaded chat file from disk immediately
        if os.path.exists(temp_path):
            os.remove(temp_path)
