import m4uLogo from '/M4U_logo.png'
import './App.css'

function App() {
  return (
    <div className='app'>
      <div className='top-bar'>
        <button className="menu-button">
          Menu
        </button>
        <div className='header'>
          <h1>Music 4 You</h1>
          <img src={m4uLogo} className='logo' alt='M4U logo' />
        </div>
      </div>
      <div className="input-section">
        <input 
          type="text" 
          placeholder="Enter playlist name"
          className="text-input"
        />
        <input 
          type="text" 
          placeholder="Songs like..."
          className="text-input"
        />
        <button className="create-playlist-btn">
          Create Playlist
        </button>
      </div>
    </div>
  )
}

export default App
