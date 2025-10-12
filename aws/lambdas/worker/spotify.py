from __future__ import annotations

import json
import os
import time
from typing import Dict, Any, List, Optional

import boto3
import requests

_secrets_arn = os.environ.get("SPOTIFY_SECRET_ARN")
_sm = boto3.client("secretsmanager")


def _get_spotify_creds() -> Dict[str, str]:
    if not _secrets_arn:
        raise RuntimeError("SPOTIFY_SECRET_ARN not set")
    resp = _sm.get_secret_value(SecretId=_secrets_arn)
    secret_str = resp.get("SecretString") or "{}"
    data = json.loads(secret_str)
    return {
        "client_id": data.get("spotify_client_id", ""),
        "client_secret": data.get("spotify_client_secret", ""),
    }


def get_access_token() -> str:
    creds = _get_spotify_creds()
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(creds["client_id"], creds["client_secret"]),
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def search_track(q: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    token = token or get_access_token()
    r = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": q, "type": "track", "limit": 10},
        timeout=15,
    )
    r.raise_for_status()
    items = r.json().get("tracks", {}).get("items", [])
    results = []
    for it in items:
        results.append(
            {
                "title": it.get("name"),
                "artist": ", ".join(a.get("name") for a in it.get("artists", [])),
                "source": "spotify",
                "id": it.get("id"),
            }
        )
    return results
