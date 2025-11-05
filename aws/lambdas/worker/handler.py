from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List
from decimal import Decimal

import boto3
try:
    # When imported as part of a package
    from . import spotify as spotify_client  # type: ignore
    from . import nlp  # type: ignore
except Exception:
    # When imported as a top-level module (e.g., moto demo)
    import spotify as spotify_client  # type: ignore
    import nlp  # type: ignore

TABLE_NAME = os.environ.get("TABLE_NAME", "")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "")
AWS_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL")
AWS_REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))

if AWS_ENDPOINT_URL:
    dynamodb = boto3.resource("dynamodb", endpoint_url=AWS_ENDPOINT_URL, region_name=AWS_REGION)
    s3 = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URL, region_name=AWS_REGION)
else:
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    s3 = boto3.client("s3", region_name=AWS_REGION)

table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None


def _to_json_safe(o: Any):
    """JSON serializer for types not serializable by default (e.g., Decimal)."""
    if isinstance(o, Decimal):
        # Use float for readability; adjust if strict precision is required
        return float(o)
    raise TypeError(f"Object of type {type(o)} is not JSON serializable")

# Placeholder for future AI + Spotify orchestration
def _placeholder_generate_songs(prompt: str, count: int) -> List[Dict[str, Any]]:
    """Placeholder logic that simulates AI + Spotify recommendation results."""
    results = []
    for i in range(count):
        results.append(
            {
                "title": f"Mock Song {i+1}",
                "artist": "Mock Artist",
                "source": "spotify",
                # Use Decimal for DynamoDB numeric compatibility
                "score": Decimal("0.5"),
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
            base, derived_count = nlp.enhance_query(prompt or "")
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
                songs.extend(_placeholder_generate_songs(prompt or base, count - len(songs)))

            item = {
                "playlist_id": playlist_id,
                "user_id": user_id,
                "prompt": prompt,
                "songs": songs,
                "created_at": str(int(time.time())),
                "status": "ready",
            }
            # Persist full playlist payload to S3 as well (durable, large payload friendly)
            if BUCKET_NAME:
                s3_key = f"playlists/{playlist_id}.json"
                try:
                    s3.put_object(
                        Bucket=BUCKET_NAME,
                        Key=s3_key,
                        Body=json.dumps(
                            {
                                "playlist_id": playlist_id,
                                "metadata": {
                                    "user_id": user_id,
                                    "prompt": prompt,
                                    "created_at": int(time.time()),
                                },
                                "songs": songs,
                            },
                            default=_to_json_safe,
                        ).encode("utf-8"),
                        ContentType="application/json",
                    )
                    item["s3_key"] = s3_key
                    item["song_count"] = len(songs)
                except Exception as e:
                    # Log but don't fail the whole message; DynamoDB item still written
                    print(f"Failed to write playlist to S3: {e}")
            table.put_item(Item=item)
        except Exception as e:
            # Log and continue; failed messages will be retried then sent to DLQ
            print(f"Error processing record: {e}")
            raise
