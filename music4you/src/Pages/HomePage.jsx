import m4uLogo from "../Components/assets/M4U_Logo.png";
import "../Styles/HomePage.css";
import Menu from "../Components/Menu";

const HomePage = ({ setIsAuthenticated }) => {
  return (
    <div className="homepage-container">
      <Menu setIsAuthenticated={setIsAuthenticated} />
      <div className="header">
        <img src={m4uLogo} alt="M4U Logo" className="logo" />
        <h1 className="title">Music For You</h1>
      </div>
      
      <div className="form-section">
        <input 
          type="text" 
          placeholder="Enter playlist name" 
          className="input-field"
        />
        <input 
          type="text" 
          placeholder="Enter your prompt" 
          className="input-field"
        />
        <div className="number-field">
          <label><input type="radio" className="radio-button" name="option" value="25" /> 25</label>
          <label><input type="radio" className="radio-button" name="option" value="35" /> 35</label>
          <label><input type="radio" className="radio-button" name="option" value="50" /> 50</label>
        </div>
        <button className="create-button">
          Create Playlist
        </button>
      </div>
    </div>
  );
};

export default HomePage;