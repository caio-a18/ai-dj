import { CognitoService } from "./cognitoService";

// Get API endpoint from environment or use default
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class PlaylistService {
  /**
   * Request a new playlist from the backend
   * @param {Object} params - Playlist request parameters
   * @param {string} params.prompt - The prompt/search query (e.g., "songs like 'Blinding Lights'")
   * @param {string} params.user_id - The authenticated user's ID
   * @param {number} params.count - Number of songs to generate (default: 20)
   * @returns {Promise<Object>} - Response with status and playlist_id
   */
  static async requestPlaylist({ prompt, user_id, count = 20 }) {
    try {
      // Get the current user's ID token for authentication
      const user = await CognitoService.getCurrentUser();
      if (!user.success) {
        throw new Error("User not authenticated");
      }

      const response = await fetch(`${API_BASE_URL}/playlists/request`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Note: Add Authorization header if API Gateway requires it
          // The Cognito authorizer should handle this via API Gateway
        },
        body: JSON.stringify({
          prompt,
          user_id,
          count: parseInt(count),
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to request playlist:", error);
      throw error;
    }
  }

  /**
   * Get a playlist by ID
   * @param {string} playlist_id - The playlist ID to retrieve
   * @returns {Promise<Object>} - Playlist data with songs
   */
  static async getPlaylist(playlist_id) {
    try {
      const response = await fetch(`${API_BASE_URL}/playlists/${playlist_id}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to get playlist:", error);
      throw error;
    }
  }

  /**
   * Get playlist data with song details
   * @param {string} playlist_id - The playlist ID to retrieve
   * @returns {Promise<Object>} - Playlist data with metadata and songs
   */
  static async getPlaylistData(playlist_id) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/playlists/${playlist_id}/data`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to get playlist data:", error);
      throw error;
    }
  }

  /**
   * Check API health
   * @returns {Promise<Object>} - Health status
   */
  static async checkHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: "GET",
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("API health check failed:", error);
      throw error;
    }
  }
}

export default PlaylistService;
