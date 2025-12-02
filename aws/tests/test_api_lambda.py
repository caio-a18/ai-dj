from __future__ import annotations

import os
import json
from typing import Any

import boto3
import pytest
from moto import mock_aws

# Import the FastAPI app from the lambda
import importlib.util
import pathlib


def import_api_app():
    api_path = pathlib.Path(__file__).parents[1] / "lambdas" / "api" / "main.py"
    spec = importlib.util.spec_from_file_location("api_main", str(api_path))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore
    return module.app  # FastAPI instance


@mock_aws
def test_health_endpoint():
    from fastapi.testclient import TestClient

    app = import_api_app()
    client = TestClient(app)

    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"


@mock_aws
def test_enqueue_playlist_request():
    from fastapi.testclient import TestClient

    # Setup moto for SQS and DynamoDB (table optional for this test)
    sqs = boto3.client("sqs", region_name="us-east-1")
    q = sqs.create_queue(QueueName="test-queue")
    queue_url = q["QueueUrl"]

    # Env vars consumed by API lambda
    os.environ["QUEUE_URL"] = queue_url
    os.environ["TABLE_NAME"] = ""
    os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"

    app = import_api_app()
    client = TestClient(app)

    payload = {"prompt": "songs like 'Blinding Lights'", "user_id": "u1", "count": 5}
    r = client.post("/playlists/request", json=payload)
    assert r.status_code == 200
    assert r.json().get("status") == "queued"

    msgs = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
    assert "Messages" in msgs
    body = json.loads(msgs["Messages"][0]["Body"])
    assert body["type"] == "playlist_request"
    assert body["prompt"] == payload["prompt"]
    assert body["user_id"] == payload["user_id"]
