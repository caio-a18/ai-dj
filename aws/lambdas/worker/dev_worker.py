from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

import boto3

# Environment
AWS_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL")  # e.g., http://localhost:4566
AWS_REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
QUEUE_URL = os.environ.get("QUEUE_URL")

if not QUEUE_URL:
    raise SystemExit("QUEUE_URL env var is required")

if AWS_ENDPOINT_URL:
    sqs = boto3.client("sqs", endpoint_url=AWS_ENDPOINT_URL, region_name=AWS_REGION)
else:
    sqs = boto3.client("sqs", region_name=AWS_REGION)


def _receive_messages(max_number: int = 5, wait_seconds: int = 2) -> List[Dict[str, Any]]:
    resp = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=max_number,
        WaitTimeSeconds=wait_seconds,
    )
    return resp.get("Messages", [])


def _delete_message(receipt_handle: str) -> None:
    sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)


def main():
    try:
        from .handler import lambda_handler  # type: ignore
    except Exception:
        import sys
        sys.path.append(os.path.dirname(__file__))
        from handler import lambda_handler  # type: ignore

    print("Dev worker started. Polling SQS... Press Ctrl+C to stop.")
    while True:
        try:
            messages = _receive_messages()
            if not messages:
                time.sleep(1)
                continue
            for m in messages:
                # Convert SQS message format to Lambda event shape
                event = {"Records": [{"body": m.get("Body", "{}")}]}
                lambda_handler(event, None)
                _delete_message(m["ReceiptHandle"])
        except KeyboardInterrupt:
            print("Stopping dev worker...")
            break
        except Exception as e:
            print(f"Error in dev worker: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
