import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
from typing import Dict

from database import init_db
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

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/upload")
async def upload_chat(file: UploadFile = File(...), chat_mode: str = Form("group")):
    """
    Handles uploading a WhatsApp .txt export.
    chat_mode: 'dm' for personal 1-on-1, 'group' for group chats.
    """
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    if chat_mode not in ("dm", "group"):
        chat_mode = "group"

    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chat_id = parse_whatsapp_chat(temp_path, file.filename.replace('.txt', ''), chat_mode)
        return {"chat_id": chat_id, "chat_mode": chat_mode, "message": "Successfully parsed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/report/{chat_id}")
async def get_report(chat_id: int):
    """
    Computes analytics and fetches LLM commentary.
    LLM result is cached in DB — Gemini is only called ONCE per chat.
    """
    from database import get_db_connection
    import json as _json

    # 1. Run analytics (always fresh — pure Python, fast)
    payload = run_analytics(chat_id)
    if "error" in payload:
        raise HTTPException(status_code=404, detail=payload["error"])

    # 2. Check cache first; also fetch mode
    with get_db_connection() as conn:
        cached = conn.execute(
            "SELECT ai_roast_json FROM report_cache WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        chat_row = conn.execute(
            "SELECT chat_mode FROM chats WHERE id = ?", (chat_id,)
        ).fetchone()
    
    chat_mode = chat_row["chat_mode"] if chat_row else "group"
    payload["chat_mode"] = chat_mode

    if cached:
        print(f"Cache hit for chat_id={chat_id}")
        payload["ai_roast"] = _json.loads(cached["ai_roast_json"])
        return payload

    # 3. Cache miss — call Gemini
    print(f"Cache miss for chat_id={chat_id} (mode={chat_mode}) — calling Gemini...")
    try:
        commentary = generate_report_commentary(payload, chat_mode=chat_mode)
    except Exception as e:
        print(f"Failed to generate commentary: {e}")
        commentary = {}

    # 4. Save to cache
    if commentary:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO report_cache (chat_id, ai_roast_json) VALUES (?, ?)",
                (chat_id, _json.dumps(commentary, ensure_ascii=False))
            )
            conn.commit()

    payload["ai_roast"] = commentary
    return payload

@app.delete("/report/{chat_id}/cache")
async def clear_report_cache(chat_id: int):
    """Force-regenerates the roast by clearing the cache for a chat."""
    from database import get_db_connection
    with get_db_connection() as conn:
        conn.execute("DELETE FROM report_cache WHERE chat_id = ?", (chat_id,))
        conn.commit()
    return {"message": f"Cache cleared for chat_id={chat_id}. Next /report call will regenerate."}
