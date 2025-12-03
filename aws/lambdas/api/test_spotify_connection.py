"""
Test Spotify OAuth connection using model.py's approach
Run this to verify the Spotify connection works before frontend integration
"""

import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load credentials from data/.env (correct relative path)
load_dotenv("../../../data/.env")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

print("=" * 60)
print("Testing Spotify OAuth Connection")
print("=" * 60)

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ ERROR: CLIENT_ID or CLIENT_SECRET not found in data/.env")
    exit(1)

print(f"✓ Loaded CLIENT_ID: {CLIENT_ID[:10]}...")
print(f"✓ Loaded CLIENT_SECRET: {CLIENT_SECRET[:10]}...")
print()

print("Initializing SpotifyOAuth with redirect_uri='http://127.0.0.1:5173/callback'")
print()

try:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope="playlist-modify-public playlist-modify-private user-read-private",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri="http://127.0.0.1:5173/callback",
        cache_path=None  # Don't cache during testing
    ))
    
    print("✓ SpotifyOAuth initialized successfully")
    print()
    print("Attempting to get current user...")
    
    user = sp.current_user()
    print(f"✓ Successfully authenticated as: {user['display_name']}")
    print(f"  User ID: {user['id']}")
    print(f"  Email: {user['email']}")
    print()
    print("=" * 60)
    print("✓ Spotify OAuth Connection TEST PASSED!")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    print()
    print("Make sure:")
    print("  1. CLIENT_ID and CLIENT_SECRET are set in data/.env")
    print("  2. Your Spotify app's redirect URIs include 'http://127.0.0.1:5173/callback'")
    print("  3. You have a Spotify account")
    exit(1)
