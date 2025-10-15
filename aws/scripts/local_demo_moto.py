from __future__ import annotations

"""
Single-process local demo using moto (no Docker required).

What it does:
- Spins up mocked AWS services (DynamoDB, SQS, Secrets Manager) in-process
- Creates table/queue/secret
- Calls the API enqueue function to put a message into SQS
- Runs the worker handler to process the message
- Reads the playlist item from DynamoDB and prints it

Run:
  python ai-dj\aws\scripts\local_demo_moto.py
"""

import json
import os
import sys
from typing import Any, Dict
from decimal import Decimal

import boto3
from moto import mock_aws


REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
TABLE_NAME = "playlists"
QUEUE_NAME = "playlist-requests"
SECRET_NAME = "ai-dj/spotify/credentials"


def create_resources() -> Dict[str, str]:
    dynamodb = boto3.client("dynamodb", region_name=REGION)
    sqs = boto3.client("sqs", region_name=REGION)
    sm = boto3.client("secretsmanager", region_name=REGION)

    # Table
    dynamodb.create_table(
        TableName=TABLE_NAME,
        AttributeDefinitions=[{"AttributeName": "playlist_id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "playlist_id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Queue
    q = sqs.create_queue(QueueName=QUEUE_NAME)
    queue_url = q["QueueUrl"]

    # Secret
    sm.create_secret(
        Name=SECRET_NAME,
        SecretString=json.dumps(
            {
                "spotify_client_id": "dummy",
                "spotify_client_secret": "dummy",
                "spotify_redirect_uri": "http://127.0.0.1:3000/callback",
            }
        ),
    )

    return {"queue_url": queue_url}


def import_api_and_worker():
    # Append directories so we can import modules directly
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lambdas"))
    api_dir = os.path.join(base_dir, "api")
    worker_dir = os.path.join(base_dir, "worker")
    for d in [api_dir, worker_dir]:
        if d not in sys.path:
            sys.path.append(d)
    import main as api_main  # type: ignore
    import handler as worker_handler  # type: ignore
    return api_main, worker_handler


def main() -> None:
    print("Starting moto in-process demo (no Docker required)...")
    with mock_aws():
        # Create AWS resources
        info = create_resources()
        queue_url = info["queue_url"]

        # Set env vars so our app code picks up resource names
        os.environ["AWS_REGION"] = REGION
        os.environ["TABLE_NAME"] = TABLE_NAME
        os.environ["QUEUE_URL"] = queue_url
        os.environ["SPOTIFY_SECRET_ARN"] = SECRET_NAME
        # This flag will be read by the worker to skip real Spotify HTTP calls in offline demo
        os.environ["SPOTIFY_OFFLINE"] = "1"
        # Important: DO NOT set AWS_ENDPOINT_URL so boto3 uses moto's patched endpoints

        # Import app modules after env vars are set
        api_main, worker_handler = import_api_and_worker()

        # Sanity check: API health
        health = api_main.health()
        print("API /health:", health)

        # Enqueue a playlist request via API function
        payload: Dict[str, Any] = {
            "prompt": "songs like Blinding Lights",
            "user_id": "demo",
            "count": 5,
        }
        resp = api_main.request_playlist(payload)
        print("Enqueue response:", resp)

        # Receive from SQS and invoke worker
        sqs = boto3.client("sqs", region_name=REGION)
        r = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=1)
        messages = r.get("Messages", [])
        if not messages:
            print("No messages found in queue; exiting.")
            return
        m = messages[0]
        event = {"Records": [{"body": m.get("Body", "{}")}]}  # lambda event shape
        worker_handler.lambda_handler(event, None)
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=m["ReceiptHandle"])

        # Verify playlist item was written
        ddb = boto3.resource("dynamodb", region_name=REGION)
        table = ddb.Table(TABLE_NAME)
        scan = table.scan()
        items = scan.get("Items", [])
        print(f"DynamoDB items count: {len(items)}")
        if items:
            print("Sample item:")
            def _to_json_safe(x):
                if isinstance(x, list):
                    return [_to_json_safe(i) for i in x]
                if isinstance(x, dict):
                    return {k: _to_json_safe(v) for k, v in x.items()}
                if isinstance(x, Decimal):
                    return float(x)
                return x
            print(json.dumps(_to_json_safe(items[0]), indent=2))


if __name__ == "__main__":
    main()
