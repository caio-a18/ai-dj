import { useState, useEffect } from 'react';
import m4uLogo from "../Components/assets/M4U_Logo.png";
import playlistPlaceholder from "../Components/assets/playlist-placeholder.jpg";
import "../Styles/PlaylistPage.css";
import Menu from "../Components/Menu";
import UserDisplay from "../Components/UserDisplay";
import SpotifyConnect from "../Components/SpotifyConnect";

const PlaylistPage = ({ setIsAuthenticated }) => {
  const [playlists, setPlaylists] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const fetchPlaylists = async () => {
      try {
        // Check if user is connected to Spotify
        const tokensRaw = sessionStorage.getItem('spotify_tokens');
        if (!tokensRaw) {
          setIsConnected(false);
          setIsLoading(false);
          return;
        }

        const tokens = JSON.parse(tokensRaw);
        if (!tokens.access_token) {
          setIsConnected(false);
          setIsLoading(false);
          return;
        }

        setIsConnected(true);

        // Fetch user's playlists from Spotify API
        const response = await fetch('https://api.spotify.com/v1/me/playlists?limit=50', {
          headers: {
            'Authorization': `Bearer ${tokens.access_token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch playlists from Spotify');
        }

        const data = await response.json();
        
        // Transform Spotify data to our format
        const formattedPlaylists = data.items.map(playlist => ({
          id: playlist.id,
          name: playlist.name,
          image: playlist.images && playlist.images[0] ? playlist.images[0].url : null,
          url: playlist.external_urls.spotify,
          trackCount: playlist.tracks.total,
          owner: playlist.owner.display_name,
          addedAt: playlist.added_at || new Date().toISOString() // Fallback to now if not available
        }));

        // Sort by newest first (most recently added)
        formattedPlaylists.sort((a, b) => new Date(b.addedAt) - new Date(a.addedAt));

        setPlaylists(formattedPlaylists);
      } catch (err) {
        console.error('Error fetching playlists:', err);
        setError(err.message || 'Failed to load playlists');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPlaylists();

    // Listen for disconnect events to refresh
    const handleDisconnect = () => {
      setIsConnected(false);
      setPlaylists([]);
    };
    window.addEventListener('spotify-disconnected', handleDisconnect);

    return () => {
      window.removeEventListener('spotify-disconnected', handleDisconnect);
    };
  }, []);

  return (
    <div className="playlistpage-container">
      <UserDisplay />
      <SpotifyConnect />
      <Menu setIsAuthenticated={setIsAuthenticated} />
      <div className="header">
        <img src={m4uLogo} alt="M4U Logo" className="logo" />
        <h1 className="title">My Playlists</h1>
      </div>
      
      <div className="playlists-section">
        {!isConnected ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <p>Connect to Spotify to see your playlists</p>
          </div>
        ) : isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <p>Loading playlists...</p>
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'red' }}>
            <p>{error}</p>
          </div>
        ) : playlists.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <p>No playlists found</p>
          </div>
        ) : (
          <div className="playlists-grid">
            {playlists.map(playlist => (
              <a 
                key={playlist.id} 
                href={playlist.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="playlist-card"
                style={{ textDecoration: 'none', color: 'inherit' }}
              >
                <img 
                  src={playlist.image || playlistPlaceholder} 
                  alt={playlist.name}
                  className="playlist-cover"
                />
                <p className="playlist-name">{playlist.name}</p>
                <p style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                  {playlist.trackCount} tracks
                </p>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PlaylistPage;

