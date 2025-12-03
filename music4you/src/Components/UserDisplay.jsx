import { useState, useEffect } from 'react';
import { CognitoService } from '../services/cognitoService';
import './UserDisplay.css';

const UserDisplay = () => {
  const [username, setUsername] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [spotifyUser, setSpotifyUser] = useState(null);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const result = await CognitoService.getUserAttributes();
        if (result.success && result.attributes) {
          const userUsername = result.attributes['custom:username'] || 
                              result.attributes.preferred_username || 
                              result.attributes.email;
          setUsername(userUsername);
        }
        // Try to load Spotify user from sessionStorage tokens
        try {
          const tokensRaw = sessionStorage.getItem('spotify_tokens');
          if (tokensRaw) {
            const tokens = JSON.parse(tokensRaw);
            if (tokens.access_token) {
              const resp = await fetch('https://api.spotify.com/v1/me', {
                headers: { Authorization: `Bearer ${tokens.access_token}` }
              });
              if (resp.ok) {
                const profile = await resp.json();
                setSpotifyUser({
                  display_name: profile.display_name,
                  id: profile.id,
                  image: profile.images && profile.images[0] ? profile.images[0].url : null
                });
              } else {
                // token might be expired or invalid — ignore for now
                console.warn('Failed to fetch Spotify profile', resp.status);
              }
            }
          }
        } catch (err) {
          console.error('Error fetching Spotify profile:', err);
        }
      } catch (error) {
        console.error('Error fetching user data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserData();
    // listen for disconnect events
    const onDisconnect = () => setSpotifyUser(null);
    window.addEventListener('spotify-disconnected', onDisconnect);
    return () => {
      window.removeEventListener('spotify-disconnected', onDisconnect);
    };
  }, []);

  if (isLoading) {
    return <div className="user-display-loading">Loading...</div>;
  }

  return (
    <div className="user-display" style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
      <div style={{display: 'flex', flexDirection: 'column'}}>
        <div className="welcome-text">Welcome,</div>
        <div className="username">{username}</div>
      </div>
      {spotifyUser && (
        <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
          {spotifyUser.image ? (
            <img src={spotifyUser.image} alt="Spotify avatar" style={{width: 40, height: 40, borderRadius: '50%'}} />
          ) : (
            <div style={{width: 40, height: 40, borderRadius: '50%', backgroundColor: '#1db954', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff'}}>S</div>
          )}
          <div style={{fontSize: '14px'}}>{spotifyUser.display_name || spotifyUser.id}</div>
        </div>
      )}
    </div>
  );
};

export default UserDisplay;