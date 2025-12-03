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
from memory_cache_handler import get_memory_cache_handler, clear_spotify_cache

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
            scope="user-read-private user-read-email playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private",
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            redirect_uri=config["redirect_uri"],
            cache_handler=get_memory_cache_handler(),  # Use memory-only cache
            open_browser=False,  # Don't try to open browser on server-side
            show_dialog=True  # Force Spotify to show account selection dialog
        )
        
        # Get the authorization URL and manually add show_dialog parameter
        auth_url = sp_oauth.get_authorize_url()
        
        # Ensure show_dialog=true is in the URL
        if 'show_dialog' not in auth_url:
            separator = '&' if '?' in auth_url else '?'
            auth_url = f"{auth_url}{separator}show_dialog=true"
        
        print(f"Generated auth URL: {auth_url}")  # Debug log
        
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
        
        # Create a fresh SpotifyOAuth instance with a new cache handler
        # This prevents tokens from being shared between users
        from memory_cache_handler import MemoryCacheHandler
        temp_cache = MemoryCacheHandler()
        
        sp_oauth = SpotifyOAuth(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            redirect_uri=config["redirect_uri"],
            scope="user-read-private user-read-email playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private",
            cache_handler=temp_cache,  # Use temporary cache for this request
            show_dialog=True  # Force account selection dialog
        )
        
        # Exchange code for tokens
        token_info = sp_oauth.get_access_token(code, as_dict=True, check_cache=False)
        
        if not token_info:
            raise HTTPException(
                status_code=400,
                detail="Failed to exchange code for tokens"
            )
        
        result = {
            "status": "ok",
            "tokens": {
                "access_token": token_info.get("access_token"),
                "refresh_token": token_info.get("refresh_token"),
                "expires_in": token_info.get("expires_in"),
                "token_type": token_info.get("token_type", "Bearer")
            }
        }
        print(f"DEBUG: Returning tokens to frontend: {result['tokens'].get('access_token')[:20]}..." if result['tokens'].get('access_token') else "No access token!")
        return result
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
