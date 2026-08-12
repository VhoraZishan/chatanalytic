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

import uuid
from typing import List

@app.post("/upload")
async def upload_chat(
    files: List[UploadFile] = File(...), 
    chat_mode: str = Form("group"),
    user_names: str = Form("")
):
    """
    Handles uploading one or more WhatsApp .txt exports.
    chat_mode: 'dm', 'group', or 'ego'.
    user_names: Comma-separated names for Ego mode profiling.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if chat_mode not in ("dm", "group", "ego"):
        chat_mode = "group"

    temp_paths = []
    parsed_chats = []
    try:
        for file in files:
            if not file.filename.endswith('.txt'):
                raise HTTPException(status_code=400, detail="Only .txt files are supported")
            
            temp_path = f"temp_{uuid.uuid4().hex}_{file.filename}"
            temp_paths.append(temp_path)
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            chat_data = parse_whatsapp_chat(temp_path, file.filename.replace('.txt', ''), chat_mode)
            parsed_chats.append(chat_data)

        # 2. Run appropriate analytics engine
        if chat_mode == "ego":
            aliases = [n.strip() for n in user_names.split(",") if n.strip()]
            if not aliases:
                raise HTTPException(status_code=400, detail="Ego Profile mode requires entering your chat name(s)")
            from analytics import run_ego_analytics
            payload = run_ego_analytics(parsed_chats, aliases)
        else:
            payload = run_analytics(parsed_chats[0])

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
        # Privacy: Delete all raw uploaded chat files from disk immediately
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                os.remove(temp_path)

