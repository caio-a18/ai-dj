"""
Memory-only cache handler for Spotipy that doesn't persist to disk.
Tokens are stored in memory and cleared when the app restarts or disconnect is called.
"""
from spotipy.cache_handler import CacheHandler
from typing import Optional


class MemoryCacheHandler(CacheHandler):
    """
    A cache handler that stores tokens in memory only.
    Does not persist to disk, so tokens are lost when app restarts.
    """
    
    def __init__(self):
        self.token_info = None
    
    def get_cached_token(self) -> Optional[dict]:
        """
        Get the cached token info.
        Returns None if no token is cached.
        """
        return self.token_info
    
    def save_token_to_cache(self, token_info: dict) -> None:
        """
        Save token info to memory.
        """
        self.token_info = token_info
    
    def clear(self) -> None:
        """
        Clear the cached token.
        """
        self.token_info = None


# Global instance that can be cleared
_global_cache_handler = MemoryCacheHandler()


def get_memory_cache_handler() -> MemoryCacheHandler:
    """
    Get the global memory cache handler instance.
    """
    return _global_cache_handler


def clear_spotify_cache() -> None:
    """
    Clear all cached Spotify tokens from memory.
    Call this when user disconnects.
    """
    _global_cache_handler.clear()
