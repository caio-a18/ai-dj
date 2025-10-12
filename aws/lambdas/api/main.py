from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from mangum import Mangum
import boto3
import base64
import requests

# Environment variables
TABLE_NAME = os.environ.get("TABLE_NAME", "")
QUEUE_URL = os.environ.get("QUEUE_URL", "")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")

# AWS clients
dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")
table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None
secrets = boto3.client("secretsmanager")
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
    arn = os.environ.get("SPOTIFY_SECRET_ARN")
    if not arn:
        return {"status": "error", "message": "SPOTIFY_SECRET_ARN not configured"}
    # Fetch creds and redirect_uri from Secrets Manager
    secret = secrets.get_secret_value(SecretId=arn).get("SecretString") or "{}"
    data = json.loads(secret)
    client_id = data.get("spotify_client_id")
    redirect_uri = data.get("spotify_redirect_uri") or "http://127.0.0.1:3000/callback"
    scopes = "user-read-email playlist-modify-private playlist-modify-public"
    # Basic, non-PKCE URL (PKCE recommended for SPA; here we use server-side exchange)
    url = (
        "https://accounts.spotify.com/authorize?"
        f"client_id={client_id}&response_type=code&redirect_uri={requests.utils.quote(redirect_uri, safe='')}"
        f"&scope={requests.utils.quote(scopes, safe=' ')}"
    )
    return {"url": url}

# Spotify OAuth callback endpoint
@app.get("/spotify/callback")
def spotify_callback(code: str | None = None, state: str | None = None, user_id: str | None = None) -> Dict[str, Any]:
    if not code:
        raise HTTPException(status_code=400, detail="missing code")
    arn = os.environ.get("SPOTIFY_SECRET_ARN")
    if not arn:
        raise HTTPException(status_code=500, detail="SPOTIFY_SECRET_ARN not configured")
    secret = secrets.get_secret_value(SecretId=arn).get("SecretString") or "{}"
    data = json.loads(secret)
    client_id = data.get("spotify_client_id")
    client_secret = data.get("spotify_client_secret")
    redirect_uri = data.get("spotify_redirect_uri") or "http://127.0.0.1:3000/callback"

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
        timeout=20,
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    tokens = resp.json()

    # Persist tokens keyed by user_id if provided; otherwise return them directly
    if table and user_id:
        table.put_item(
            Item={
                "playlist_id": f"auth:{user_id}",
                "user_id": user_id,
                "spotify_tokens": tokens,
                "status": "auth",
            }
        )
        return {"status": "saved", "user_id": user_id}
    return {"status": "ok", "tokens": {k: tokens.get(k) for k in ["access_token", "refresh_token", "expires_in"]}}

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
