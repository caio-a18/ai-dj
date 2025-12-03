import './SpotifyConnect.css';
import { useState } from 'react';

const SpotifyTest = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [testType, setTestType] = useState('connection'); // 'connection' or 'auth-url'

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleTestSpotify = async (type) => {
    setIsLoading(true);
    setError('');
    setResult(null);
    setTestType(type);

    try {
      const endpoint = type === 'connection' ? '/spotify/test' : '/spotify/test-auth-url';
      const response = await fetch(`${API_BASE_URL}${endpoint}`);
      const data = await response.json();

      if (data.status === 'ok') {
        setResult(data);
      } else {
        setError(data.message || 'Test failed');
      }
    } catch (err) {
      console.error('Test error:', err);
      setError(err.message || 'Failed to test Spotify connection');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="spotify-connect-container">
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <button
          className="spotify-connect-btn"
          onClick={() => handleTestSpotify('connection')}
          disabled={isLoading}
        >
          {isLoading && testType === 'connection' ? 'Testing...' : 'Test Spotify Connection'}
        </button>
        
        <button
          className="spotify-connect-btn"
          onClick={() => handleTestSpotify('auth-url')}
          disabled={isLoading}
        >
          {isLoading && testType === 'auth-url' ? 'Testing...' : 'Test Auth URL'}
        </button>
      </div>

      {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}

      {result && (
        <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
          <p><strong>✓ Success!</strong></p>
          {result.user && (
            <>
              <p>User: {result.user.display_name}</p>
              <p>Email: {result.user.email}</p>
              <p>ID: {result.user.id}</p>
            </>
          )}
          {result.url && (
            <>
              <p>Auth URL generated ({result.url_length} chars)</p>
              <p style={{ wordBreak: 'break-all', fontSize: '12px' }}>
                {result.url.substring(0, 100)}...
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SpotifyTest;
