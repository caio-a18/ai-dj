from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List

import boto3
from . import spotify as spotify_client  # type: ignore
from . import nlp

TABLE_NAME = os.environ.get("TABLE_NAME", "")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None
s3 = boto3.client("s3")

# Placeholder for future Bedrock-powered parsing if needed
def _placeholder_bedrock_and_spotify(prompt: str, count: int) -> List[Dict[str, Any]]:
    """Placeholder logic that simulates AI + Spotify recommendation results."""
    results = []
    for i in range(count):
        results.append(
            {
                "title": f"Mock Song {i+1}",
                "artist": "Mock Artist",
                "source": "spotify",
                "score": 0.5,
            }
        )
    return results

# Lambda function handler
def lambda_handler(event, context):
    if not table:
        raise RuntimeError("TABLE_NAME not configured")

    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"]) if isinstance(record.get("body"), str) else record.get("body", {})
            if body.get("type") != "playlist_request":
                continue
            prompt = body.get("prompt")
            user_id = body.get("user_id")
            # Try to derive count/base from prompt if not provided
            base, derived_count = nlp.bedrock_enhance_query(prompt or "")
            count = int(body.get("count") or derived_count or 20)
            playlist_id = str(uuid.uuid4())

            # If Secrets Manager ARN is set, try real Spotify search for base; then fill with mocks
            songs: List[Dict[str, Any]] = []
            try:
                if os.environ.get("SPOTIFY_SECRET_ARN") and base:
                    seeds = spotify_client.search_track(base)
                    songs.extend(seeds[: min(len(seeds), count)])
            except Exception as e:
                print(f"Spotify lookup failed, fallback to mock: {e}")
            if len(songs) < count:
                songs.extend(_placeholder_bedrock_and_spotify(prompt or base, count - len(songs)))

            item = {
                "playlist_id": playlist_id,
                "user_id": user_id,
                "prompt": prompt,
                "songs": songs,
                "created_at": str(int(time.time())),
                "status": "ready",
            }
            table.put_item(Item=item)
        except Exception as e:
            # Log and continue; failed messages will be retried then sent to DLQ
            print(f"Error processing record: {e}")
            raise
