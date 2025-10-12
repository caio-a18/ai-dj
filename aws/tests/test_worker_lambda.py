from __future__ import annotations

import os
import json
import importlib.util
import pathlib
from typing import Any, Dict

import boto3
from moto import mock_aws


def import_worker_handler():
    path = pathlib.Path(__file__).parents[1] / "lambdas" / "worker" / "handler.py"
    spec = importlib.util.spec_from_file_location("worker_handler", str(path))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore
    return module.lambda_handler


@mock_aws
def test_worker_processes_message_and_writes_playlist():
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(
        TableName="playlists",
        KeySchema=[{"AttributeName": "playlist_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "playlist_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="test-bucket")

    # Env
    os.environ["TABLE_NAME"] = "playlists"
    os.environ["BUCKET_NAME"] = "test-bucket"

    handler = import_worker_handler()

    event = {
        "Records": [
            {
                "body": json.dumps(
                    {
                        "type": "playlist_request",
                        "prompt": "20 songs like 'Blinding Lights'",
                        "user_id": "u1",
                        "count": 5,
                    }
                )
            }
        ]
    }

    # Should not raise and should write an item
    handler(event, None)

    resp = table.scan()
    items = resp.get("Items", [])
    assert len(items) == 1
    item = items[0]
    assert item.get("user_id") == "u1"
    assert item.get("status") == "ready"
    assert isinstance(item.get("songs"), list)
    assert len(item.get("songs")) == 5
