import { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const SpotifyCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('processing');
  const [message, setMessage] = useState('Processing Spotify authorization...');
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Prevent duplicate calls (React Strict Mode runs effects twice)
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const handleCallback = async () => {
      const code = searchParams.get('code');
      const error = searchParams.get('error');

      if (error) {
        setStatus('error');
        setMessage(`Spotify authorization denied: ${error}`);
        setTimeout(() => navigate('/'), 3000);
        return;
      }

      if (!code) {
        setStatus('error');
        setMessage('No authorization code received from Spotify');
        setTimeout(() => navigate('/'), 3000);
        return;
      }

      try {
        const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/spotify/callback?code=${code}`);
        const data = await response.json();

        if (data.status === 'ok') {
          setStatus('success');
          setMessage('Successfully connected to Spotify!');
          // Store tokens in sessionStorage or localStorage
          if (data.tokens) {
            console.log('DEBUG: Storing tokens in sessionStorage:', data.tokens);
            sessionStorage.setItem('spotify_tokens', JSON.stringify(data.tokens));
            console.log('DEBUG: Tokens stored. Verifying:', sessionStorage.getItem('spotify_tokens'));
          } else {
            console.error('DEBUG: No tokens in response!', data);
          }
          setTimeout(() => navigate('/'), 2000);
        } else {
          setStatus('error');
          setMessage(data.detail || 'Failed to exchange code for tokens');
          setTimeout(() => navigate('/'), 3000);
        }
      } catch (err) {
        setStatus('error');
        setMessage(`Error: ${err.message}`);
        setTimeout(() => navigate('/'), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  return (
    <div style={{ padding: '40px', textAlign: 'center' }}>
      <h2>Spotify Authorization</h2>
      <p style={{
        color: status === 'success' ? 'green' : status === 'error' ? 'red' : 'blue',
        fontSize: '16px'
      }}>
        {message}
      </p>
      {status === 'processing' && <p>Redirecting...</p>}
    </div>
  );
};

export default SpotifyCallback;
