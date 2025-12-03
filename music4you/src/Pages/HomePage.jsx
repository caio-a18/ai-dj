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
  const [naturalPrompt, setNaturalPrompt] = useState('');
  const [useNaturalInput, setUseNaturalInput] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleCreatePlaylist = async () => {
    setIsLoading(true);
    setError('');
    setSuccessMessage('');

    try {
      // If using natural language input, parse it first
      if (useNaturalInput) {
        if (!naturalPrompt.trim()) {
          throw new Error('Please enter a description of the playlist you want');
        }
        
        // Get Spotify access token first
        const tokensRaw = sessionStorage.getItem('spotify_tokens');
        if (!tokensRaw) {
          throw new Error('Please connect to Spotify first');
        }

        const tokens = JSON.parse(tokensRaw);
        if (!tokens.access_token) {
          throw new Error('No valid Spotify access token found');
        }
        
        // Call NLP parsing endpoint
        const parseResponse = await fetch(`${API_BASE_URL}/playlists/parse`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: naturalPrompt
          })
        });
        
        const parseResult = await parseResponse.json();
        
        if (parseResult.status === 'error') {
          throw new Error(`Parse error: ${parseResult.message}`);
        }
        
        // Extract parsed data
        const { artists, songs, k } = parseResult.parsed;
        
        // Validate we have at least an artist or song
        if (artists.length === 0 && songs.length === 0) {
          throw new Error('Could not extract artist or song from your query. Try: "give me 10 songs by Drake"');
        }
        
        // Use first artist and first song (or empty string if not found)
        const artist = artists.length > 0 ? artists[0] : '';
        const song = songs.length > 0 ? songs[0] : '';
        
        // Need at least one of them
        if (!artist && !song) {
          throw new Error('Please specify at least an artist or song name');
        }
        
        // Generate playlist with parsed data
        const response = await fetch(`${API_BASE_URL}/playlists/generate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            artist: artist,
            song: song,
            song_count: k,
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
        
        setIsLoading(false);
        return;
      }

      // Validate inputs for structured form
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
        {/* Toggle between natural language and structured input */}
        <div style={{ marginBottom: '20px', textAlign: 'center' }}>
          <button 
            onClick={() => setUseNaturalInput(!useNaturalInput)}
            style={{
              padding: '8px 16px',
              backgroundColor: '#1db954',
              color: 'white',
              border: 'none',
              borderRadius: '20px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            {useNaturalInput ? 'Switch to Form Input' : 'Try Natural Language'}
          </button>
        </div>

        {useNaturalInput ? (
          /* Natural Language Input */
          <div>
            <p style={{ marginBottom: '10px', color: '#666', fontSize: '14px' }}>
              Try: "give me 10 songs by Drake" or "recommend 25 tracks like 'Blinding Lights' by The Weeknd"
            </p>
            <textarea
              placeholder="Describe the playlist you want..."
              className="input-field"
              value={naturalPrompt}
              onChange={(e) => setNaturalPrompt(e.target.value)}
              disabled={isLoading}
              rows={4}
              style={{
                width: '100%',
                resize: 'vertical',
                fontFamily: 'inherit',
                padding: '12px'
              }}
            />
          </div>
        ) : (
          /* Structured Form Input */
          <>
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
          </>
        )}

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