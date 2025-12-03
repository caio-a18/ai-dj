import './SpotifyConnect.css';
import { useState } from 'react';
import { useEffect } from 'react';

const SpotifyConnect = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isConnected, setIsConnected] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleConnectSpotify = async () => {
    setIsLoading(true);
    setError('');

    try {
      // Use the same test-style endpoint that works locally
      const response = await fetch(`${API_BASE_URL}/spotify/test-auth-url`);
      const data = await response.json();

      if (data.status !== 'ok' || !data.url) {
        throw new Error(data.message || data.detail || 'Failed to get authorization URL');
      }

      // Mark auth in progress so callback logic can detect it
      sessionStorage.setItem('spotify_auth_in_progress', 'true');

      // Redirect browser to Spotify authorize URL
      window.location.href = data.url;
    } catch (err) {
      console.error('Spotify connection error:', err);
      setError(err.message || 'Failed to connect to Spotify');
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Check connection state on mount and listen for changes
    const checkConnection = () => {
      try {
        const tokensRaw = sessionStorage.getItem('spotify_tokens');
        if (tokensRaw) {
          const tokens = JSON.parse(tokensRaw);
          if (tokens && tokens.access_token) {
            setIsConnected(true);
            return;
          }
        }
        setIsConnected(false);
      } catch (e) {
        setIsConnected(false);
      }
    };
    
    checkConnection();
    
    // Listen for disconnect events
    const onDisconnect = () => {
      setIsConnected(false);
      // Double-check tokens are cleared
      sessionStorage.removeItem('spotify_tokens');
      sessionStorage.removeItem('spotify_auth_in_progress');
    };
    
    window.addEventListener('spotify-disconnected', onDisconnect);
    return () => window.removeEventListener('spotify-disconnected', onDisconnect);
  }, []);

  const handleDisconnect = async () => {
    try {
      // Clear server-side cache
      await fetch(`${API_BASE_URL}/spotify/disconnect`, {
        method: 'POST',
      }).catch(err => console.warn('Failed to clear server cache:', err));
      
      // Clear all Spotify-related session storage
      sessionStorage.removeItem('spotify_tokens');
      sessionStorage.removeItem('spotify_auth_in_progress');
      
      // Force state update
      setIsConnected(false);
      
      // Dispatch event to notify other components
      window.dispatchEvent(new Event('spotify-disconnected'));
      
      console.log('Spotify tokens cleared from session and server');
    } catch (e) {
      console.warn('Error clearing spotify tokens', e);
    }
  };

  const handleTestSpotify = async () => {
    setIsLoading(true);
    setError('');

    try {
      const tokensRaw = sessionStorage.getItem('spotify_tokens');
      if (!tokensRaw) {
        throw new Error('Not connected to Spotify');
      }

      const tokens = JSON.parse(tokensRaw);
      const response = await fetch(`${API_BASE_URL}/spotify/create-test-playlist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          access_token: tokens.access_token
        })
      });

      const data = await response.json();

      if (data.status === 'ok') {
        alert(`✓ Success! Created playlist: ${data.playlist.name}\n\nCheck your Spotify account!`);
      } else {
        throw new Error(data.message || 'Failed to create test playlist');
      }
    } catch (err) {
      console.error('Test Spotify error:', err);
      setError(err.message || 'Failed to create test playlist');
    } finally {
      setIsLoading(false);
    }
  };

  // keep this component reactive when other parts of the app disconnect

  return (
    <div className="spotify-connect-container">
      {!isConnected ? (
        <>
          <button
            className="spotify-connect-btn"
            onClick={handleConnectSpotify}
            disabled={isLoading}
          >
            {isLoading ? 'Connecting...' : 'Connect to Spotify'}
          </button>
          {error && <p className="spotify-error-message">{error}</p>}
        </>
      ) : (
        <div className="spotify-connected">
          <p>✓ Connected to Spotify</p>
          <button 
            className="spotify-connect-btn" 
            onClick={handleTestSpotify}
            disabled={isLoading}
            style={{marginLeft: 8}}
          >
            {isLoading ? 'Creating...' : 'Test Spotify'}
          </button>
          <button className="spotify-disconnect-btn" onClick={handleDisconnect} style={{marginLeft: 8}}>
            Disconnect
          </button>
        </div>
      )}
    </div>
  );
};

export default SpotifyConnect;