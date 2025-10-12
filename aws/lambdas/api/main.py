from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from mangum import Mangum
import boto3

# Environment variables
TABLE_NAME = os.environ.get("TABLE_NAME", "")
QUEUE_URL = os.environ.get("QUEUE_URL", "")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")

# AWS clients
dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")
table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None
# FastAPI app
app = FastAPI(title="AI-DJ API", version="0.1.0")

# CORS middleware
@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "time": int(time.time())}

# Playlist request endpoint
@app.post("/playlists/request")
def request_playlist(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Body example:
    {
      "prompt": "songs like 'Blinding Lights'",
      "user_id": "uuid-123",
      "count": 20
    }
    """
    prompt = payload.get("prompt")
    user_id = payload.get("user_id")
    count = int(payload.get("count") or 20)
    if not prompt or not user_id:
        raise HTTPException(status_code=400, detail="prompt and user_id are required")
    if not QUEUE_URL:
        raise HTTPException(status_code=500, detail="QUEUE_URL not configured")

    message = {
        "type": "playlist_request",
        "prompt": prompt,
        "user_id": user_id,
        "count": count,
    }
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))
    return {"status": "queued"}

# Spotify OAuth endpoints (placeholders for Phase 2)
@app.get("/spotify/auth-url")
def spotify_auth_url() -> Dict[str, Any]:
    # Placeholder: in Phase 2, generate a PKCE auth URL or server-side OAuth URL
    arn = os.environ.get("SPOTIFY_SECRET_ARN")
    return {"status": "ok", "configured": bool(arn)}

# Spotify OAuth callback endpoint
@app.get("/spotify/callback")
def spotify_callback(code: str | None = None, state: str | None = None) -> Dict[str, Any]:
    # Placeholder: handle OAuth callback and exchange code for tokens
    return {"status": "todo", "code": bool(code), "state": state}

# Get playlist by ID
@app.get("/playlists/{playlist_id}")
def get_playlist(playlist_id: str) -> Dict[str, Any]:
    if not table:
        raise HTTPException(status_code=500, detail="TABLE_NAME not configured")
    resp = table.get_item(Key={"playlist_id": playlist_id})
    item = resp.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="playlist not found")
    return item

# Lambda handler
handler = Mangum(app)
