import m4uLogo from "../Components/assets/M4U_Logo.png";
import playlistPlaceholder from "../Components/assets/playlist-placeholder.jpg";
import "../Styles/PlaylistPage.css";
import Menu from "../Components/Menu";

const PlaylistPage = ({ setIsAuthenticated }) => {
  // Temporary data - replace with actual data later
  const tempPlaylists = [
    { id: 1, name: "Workout Mix" },
    { id: 2, name: "Chill Vibes" },
    { id: 3, name: "Road Trip" },
    { id: 4, name: "Study Focus" },
    { id: 5, name: "Party Hits" },
    { id: 6, name: "Morning Coffee" },
    { id: 7, name: "Late Night" },
    { id: 8, name: "Throwbacks" },
    { id: 1, name: "Workout Mix" },
    { id: 2, name: "Chill Vibes" },
    { id: 3, name: "Road Trip" },
    { id: 4, name: "Study Focus" },
    { id: 5, name: "Party Hits" },
    { id: 6, name: "Morning Coffee" },
    { id: 7, name: "Late Night" },
    { id: 8, name: "Throwbacks" },
  ];

  return (
    <div className="playlistpage-container">
      <Menu setIsAuthenticated={setIsAuthenticated} />
      <div className="header">
        <img src={m4uLogo} alt="M4U Logo" className="logo" />
        <h1 className="title">My Playlists</h1>
      </div>
      
      <div className="playlists-section">
        <div className="playlists-grid">
          {tempPlaylists.map(playlist => (
            <div key={playlist.id} className="playlist-card">
              <img 
                src={playlistPlaceholder} 
                alt={playlist.name}
                className="playlist-cover"
              />
              <p className="playlist-name">{playlist.name}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PlaylistPage;

