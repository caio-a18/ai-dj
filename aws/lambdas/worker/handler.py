from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List

import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None
s3 = boto3.client("s3")


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
            count = int(body.get("count") or 20)
            playlist_id = str(uuid.uuid4())

            # Simulate AI+Spotify
            songs = _placeholder_bedrock_and_spotify(prompt, count)

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
