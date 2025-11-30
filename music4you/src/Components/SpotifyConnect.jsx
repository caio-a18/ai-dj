import './SpotifyConnect.css';

const SpotifyConnect = () => {
  const handleConnectSpotify = () => {
    console.log('Connect to Spotify clicked');
    // Add Spotify OAuth logic here later
  };

  return (
    <button className="spotify-connect-btn" onClick={handleConnectSpotify}>
      Connect to Spotify
    </button>
  );
};

export default SpotifyConnect;