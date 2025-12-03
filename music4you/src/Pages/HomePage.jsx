import { useState } from 'react';
import m4uLogo from "../Components/assets/M4U_Logo.png";
import "../Styles/HomePage.css";
import Menu from "../Components/Menu";
import UserDisplay from "../Components/UserDisplay";
import SpotifyConnect from "../Components/SpotifyConnect";

const HomePage = ({ setIsAuthenticated }) => {
  const [artist, setArtist] = useState('');
  const [song, setSong] = useState('');
  const [songCount, setSongCount] = useState('25');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleCreatePlaylist = async () => {
    setIsLoading(true);
    setError('');
    setSuccessMessage('');

    try {
      // Validate inputs
      if (!artist.trim() || !song.trim()) {
        throw new Error('Please enter both artist name and song title');
      }

      // Get Spotify access token
      const tokensRaw = sessionStorage.getItem('spotify_tokens');
      if (!tokensRaw) {
        throw new Error('Please connect to Spotify first');
      }

      const tokens = JSON.parse(tokensRaw);
      if (!tokens.access_token) {
        throw new Error('No valid Spotify access token found');
      }

      // Send request to backend
      const response = await fetch(`${API_BASE_URL}/playlists/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          artist: artist.trim(),
          song: song.trim(),
          song_count: parseInt(songCount),
          access_token: tokens.access_token
        })
      });

      const data = await response.json();

      if (data.status === 'ok') {
        setSuccessMessage(data.message);
        console.log('Backend response:', data);
      } else {
        throw new Error(data.message || 'Failed to generate playlist');
      }
    } catch (err) {
      console.error('Playlist generation error:', err);
      setError(err.message || 'Failed to generate playlist');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="homepage-container">
      <UserDisplay />
      <SpotifyConnect />
      <Menu setIsAuthenticated={setIsAuthenticated} />
      <div className="header">
        <img src={m4uLogo} alt="M4U Logo" className="logo" />
        <h1 className="title">Music For You</h1>
      </div>
      
      <div className="form-section">
        <input 
          type="text" 
          placeholder="Enter artist name" 
          className="input-field"
          value={artist}
          onChange={(e) => setArtist(e.target.value)}
          disabled={isLoading}
        />
        <input 
          type="text" 
          placeholder="Enter song title" 
          className="input-field"
          value={song}
          onChange={(e) => setSong(e.target.value)}
          disabled={isLoading}
        />
        <div className="number-field">
          <label>
            <input 
              type="radio" 
              className="radio-button" 
              name="option" 
              value="25" 
              checked={songCount === '25'}
              onChange={(e) => setSongCount(e.target.value)}
              disabled={isLoading}
            /> 25
          </label>
          <label>
            <input 
              type="radio" 
              className="radio-button" 
              name="option" 
              value="35" 
              checked={songCount === '35'}
              onChange={(e) => setSongCount(e.target.value)}
              disabled={isLoading}
            /> 35
          </label>
          <label>
            <input 
              type="radio" 
              className="radio-button" 
              name="option" 
              value="50" 
              checked={songCount === '50'}
              onChange={(e) => setSongCount(e.target.value)}
              disabled={isLoading}
            /> 50
          </label>
        </div>
        <button 
          className="create-button"
          onClick={handleCreatePlaylist}
          disabled={isLoading}
        >
          {isLoading ? 'Creating...' : 'Create Playlist'}
        </button>
        {error && <p style={{color: 'red', marginTop: '10px'}}>{error}</p>}
        {successMessage && <p style={{color: 'green', marginTop: '10px'}}>{successMessage}</p>}
      </div>
    </div>
  );
};

export default HomePage;