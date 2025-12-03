"""
Spotify OAuth handler for AI-DJ
Adapted from model.py SpotifyOAuth implementation
"""

from __future__ import annotations

import json
import os
import base64
import urllib.parse
from typing import Dict, Any
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from fastapi import HTTPException
from dotenv import load_dotenv

# Load environment variables from .env file (look in data directory)
env_path = os.path.join(os.path.dirname(__file__), '../../../data/.env')
if os.path.exists(env_path):
    load_dotenv(env_path)


def _get_spotify_config() -> Dict[str, str]:
    """Get Spotify credentials from environment or .env file"""
    client_id = os.getenv("CLIENT_ID") or os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET") or os.environ.get("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5173/callback")
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail="Spotify credentials not configured. Set CLIENT_ID and CLIENT_SECRET."
        )
    
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }



def get_auth_url() -> Dict[str, Any]:
    """
    Generate Spotify authorization URL for user to authorize the app.
    Returns the URL that frontend should redirect to.
    """
    try:
        config = _get_spotify_config()
        
        # Create SpotifyOAuth instance to use its methods
        sp_oauth = SpotifyOAuth(
            scope="playlist-modify-public playlist-modify-private user-read-private",
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            redirect_uri=config["redirect_uri"],
            cache_path=None,  # Don't use file cache in Lambda
            open_browser=False  # Don't try to open browser on server-side
        )
        
        # Get the authorization URL without opening browser
        auth_url = sp_oauth.get_authorize_url()
        
        return {
            "status": "ok",
            "url": auth_url
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )



def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access tokens.
    This is called by the frontend callback endpoint.
    """
    try:
        config = _get_spotify_config()
        
        # Create SpotifyOAuth instance
        sp_oauth = SpotifyOAuth(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            redirect_uri=config["redirect_uri"],
            scope="playlist-modify-public playlist-modify-private user-read-private",
            cache_path=None  # Don't use file cache in Lambda
        )
        
        # Exchange code for tokens
        token_info = sp_oauth.get_access_token(code)
        
        if not token_info:
            raise HTTPException(
                status_code=400,
                detail="Failed to exchange code for tokens"
            )
        
        return {
            "status": "ok",
            "tokens": {
                "access_token": token_info.get("access_token"),
                "refresh_token": token_info.get("refresh_token"),
                "expires_in": token_info.get("expires_in"),
                "token_type": token_info.get("token_type", "Bearer")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to exchange code for tokens: {str(e)}"
        )


def get_spotify_client_with_token(access_token: str) -> spotipy.Spotify:
    """
    Create a Spotify client with user's access token.
    Use this for user-specific operations like creating playlists.
    """
    return spotipy.Spotify(auth=access_token)


def get_spotify_client_credentials() -> spotipy.Spotify:
    """
    Create a Spotify client using Client Credentials flow.
    Use this for general search operations that don't need user context.
    """
    try:
        config = _get_spotify_config()
        
        auth_manager = spotipy.oauth2.SpotifyClientCredentials(
            client_id=config["client_id"],
            client_secret=config["client_secret"]
        )
        
        return spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Spotify client: {str(e)}"
        )
