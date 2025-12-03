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
AWS_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL")  # e.g., http://localhost:4566 for LocalStack
AWS_REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))

# AWS clients (local-friendly)
if AWS_ENDPOINT_URL:
    dynamodb = boto3.resource("dynamodb", endpoint_url=AWS_ENDPOINT_URL, region_name=AWS_REGION)
    sqs = boto3.client("sqs", endpoint_url=AWS_ENDPOINT_URL, region_name=AWS_REGION)
    secrets = boto3.client("secretsmanager", endpoint_url=AWS_ENDPOINT_URL, region_name=AWS_REGION)
else:
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    sqs = boto3.client("sqs", region_name=AWS_REGION)
    secrets = boto3.client("secretsmanager", region_name=AWS_REGION)

table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None
# FastAPI app
app = FastAPI(title="AI-DJ API", version="0.1.0")

# CORS middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Get playlist data directly from DynamoDB
@app.get("/playlists/{playlist_id}/data")
def get_playlist_data(playlist_id: str) -> Dict[str, Any]:
    if not table:
        raise HTTPException(status_code=500, detail="TABLE_NAME not configured")
    # Look up the item and return inline songs
    resp = table.get_item(Key={"playlist_id": playlist_id})
    item = resp.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="playlist not found")
    if "songs" not in item:
        raise HTTPException(status_code=404, detail="playlist data not found")
    return {
        "playlist_id": playlist_id,
        "metadata": {
            "user_id": item.get("user_id"),
            "prompt": item.get("prompt"),
            "created_at": int(item.get("created_at", 0)),
        },
        "songs": item.get("songs", []),
    }


# Spotify OAuth endpoints
@app.get("/spotify/auth-url")
def spotify_auth_url() -> Dict[str, Any]:
    """
    Generate Spotify authorization URL.
    Frontend redirects to this URL to start OAuth flow.
    """
    from spotify_oauth import get_auth_url
    return get_auth_url()


@app.post("/spotify/disconnect")
def spotify_disconnect() -> Dict[str, Any]:
    """
    Clear Spotify cache on server side when user disconnects.
    This ensures a fresh auth flow on next connection.
    """
    try:
        from memory_cache_handler import clear_spotify_cache
        clear_spotify_cache()
        return {"status": "ok", "message": "Spotify cache cleared"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/spotify/callback")
def spotify_callback(code: str | None = None) -> Dict[str, Any]:
    """
    Handle Spotify OAuth callback.
    Frontend calls this endpoint with the authorization code from Spotify.
    Returns access and refresh tokens.
    """
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    from spotify_oauth import exchange_code_for_tokens
    return exchange_code_for_tokens(code)


@app.get("/spotify/test")
def spotify_test() -> Dict[str, Any]:
    """
    Test Spotify connection - directly test if credentials work
    """
    try:
        import os
        from dotenv import load_dotenv
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        # Load credentials
        env_path = os.path.join(os.path.dirname(__file__), '../../../data/.env')
        load_dotenv(env_path)
        
        CLIENT_ID = os.getenv("CLIENT_ID")
        CLIENT_SECRET = os.getenv("CLIENT_SECRET")
        
        if not CLIENT_ID or not CLIENT_SECRET:
            return {"status": "error", "message": "Credentials not found"}
        
        # Test SpotifyOAuth - don't use cache
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            scope="playlist-modify-public playlist-modify-private user-read-private",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri="http://127.0.0.1:5173/callback",
            cache_path=None,  # Critical: Don't cache credentials
            show_dialog=True
        ))
        
        user = sp.current_user()
        
        return {
            "status": "ok",
            "message": "Spotify connection successful!",
            "user": {
                "id": user.get('id'),
                "display_name": user.get('display_name'),
                "email": user.get('email')
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/spotify/test-auth-url")
def spotify_test_auth_url() -> Dict[str, Any]:
    """
    Test the get_auth_url function directly
    """
    try:
        import os
        from dotenv import load_dotenv
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        # Load credentials
        env_path = os.path.join(os.path.dirname(__file__), '../../../data/.env')
        load_dotenv(env_path)
        
        CLIENT_ID = os.getenv("CLIENT_ID")
        CLIENT_SECRET = os.getenv("CLIENT_SECRET")
        
        if not CLIENT_ID or not CLIENT_SECRET:
            return {"status": "error", "message": "Credentials not found"}
        
        # Test SpotifyOAuth with open_browser=False and show_dialog=True
        sp_oauth = SpotifyOAuth(
            scope="user-read-private user-read-email playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri="http://127.0.0.1:5173/callback",
            cache_path=None,
            open_browser=False,
            show_dialog=True  # Force account selection dialog
        )
        
        auth_url = sp_oauth.get_authorize_url()
        
        # Manually ensure show_dialog=true is in the URL
        if 'show_dialog' not in auth_url:
            separator = '&' if '?' in auth_url else '?'
            auth_url = f"{auth_url}{separator}show_dialog=true"
        
        print(f"Generated auth URL with show_dialog: {auth_url}")
        
        return {
            "status": "ok",
            "message": "Auth URL generated successfully",
            "url": auth_url,
            "url_length": len(auth_url)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "type": type(e).__name__
        }


@app.post("/spotify/create-test-playlist")
def create_test_playlist(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an empty test playlist on the user's Spotify account.
    Expects: { "access_token": "..." }
    """
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        access_token = payload.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="access_token is required")
        
        # Create Spotify client with user's access token
        sp = spotipy.Spotify(auth=access_token)
        
        # Get current user info
        user = sp.current_user()
        user_id = user['id']
        
        # Create empty playlist
        playlist = sp.user_playlist_create(
            user=user_id,
            name="AI-DJ Test Playlist",
            public=False,
            description="Test playlist created by AI-DJ"
        )
        
        return {
            "status": "ok",
            "message": "Test playlist created successfully!",
            "playlist": {
                "id": playlist['id'],
                "name": playlist['name'],
                "url": playlist['external_urls']['spotify']
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "type": type(e).__name__
        }


@app.post("/playlists/parse")
def parse_nlp_query(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse natural language query to extract artists, songs, and count.
    Expects: { "query": "give me 10 songs by Drake" }
    Returns: { "artists": [...], "songs": [...], "k": 10 }
    """
    try:
        query = payload.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="query is required")
        
        # Import NLP module
        from nlp import parse_music_query
        
        # Parse the query
        result = parse_music_query(query)
        
        return {
            "status": "ok",
            "parsed": result,
            "original_query": query
        }
        
    except Exception as e:
        print(f"Error in parse_nlp_query: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "type": type(e).__name__
        }


@app.post("/playlists/generate")
def generate_playlist_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate playlist using ML model.
    Expects: { "artist": "...", "song": "...", "song_count": 25, "access_token": "..." }
    """
    try:
        artist = payload.get("artist")
        song = payload.get("song")
        song_count = payload.get("song_count", 25)
        access_token = payload.get("access_token")
        
        if not artist or not song:
            raise HTTPException(status_code=400, detail="artist and song are required")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="access_token is required")
        
        # Import the playlist generator
        from playlist_generator import generate_playlist
        
        # Set up DynamoDB table - MUST use us-east-2 where table exists
        import boto3
        AWS_REGION = "us-east-2"  # Hardcode the correct region
        aws_profile = os.environ.get("AWS_PROFILE", "DevMusic4You-411189321562")
        
        # Create session with profile
        print(f"Using AWS profile: {aws_profile}, region: {AWS_REGION}")
        session = boto3.Session(profile_name=aws_profile, region_name=AWS_REGION)
        
        # Test connection
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"Connected as: {identity['Arn']}")
        
        dynamodb = session.resource('dynamodb', region_name=AWS_REGION)
        datasets_table = dynamodb.Table('aidj_datasets')
        playlists_table = dynamodb.Table('aidj_playlists')
        
        # Verify tables exist
        print(f"DynamoDB datasets table: {datasets_table.table_name}")
        print(f"DynamoDB playlists table: {playlists_table.table_name}")
        
        # Generate the playlist
        result = generate_playlist(
            artist=artist,
            song=song,
            song_count=song_count,
            access_token=access_token,
            datasets_table=datasets_table,
            playlists_table=playlists_table
        )
        
        return result
        
    except Exception as e:
        print(f"Error in generate_playlist_endpoint: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "type": type(e).__name__
        }


# Lambda handler
handler = Mangum(app)
