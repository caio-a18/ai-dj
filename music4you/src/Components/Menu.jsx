import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Menu.css';
import { CognitoService } from "../services/cognitoService"

const Menu = ({ setIsAuthenticated }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [closeTimeout, setCloseTimeout] = useState(null);
  const navigate = useNavigate();

  const handleSignOut = async () => {
    const result = await CognitoService.signOut();
    
    if (result.success) {
      setIsAuthenticated(false);
      navigate('/login');
    } else {
      console.error("Sign out error: ", result.error);
    }
  };

  const handleMouseEnter = () => {
    if (closeTimeout) {
      clearTimeout(closeTimeout);
      setCloseTimeout(null);
    }
    setIsOpen(true);
  };

  const handleMouseLeave = () => {
    const timeout = setTimeout(() => {
      setIsOpen(false);
    }, 300);
    setCloseTimeout(timeout);
  };

  const handleMenuClick = (option) => {
    setIsOpen(false);
    
    switch(option) {
      case 'Home':
        navigate('/home');
        break;
      case 'My Playlists':
        navigate('/playlists');
        break;
      case 'Sign out':
        handleSignOut();
        break;
      default:
        break;
    }
  };

  return (
    <div 
      className="menu-container"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className={`menu-header ${isOpen ? 'expanded' : ''}`}>
        <div className="hamburger-icon">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <span className="menu-text">Menu</span>
      </div>

      {isOpen && (
        <div className="menu-dropdown">
          <div 
            className="menu-item" 
            onClick={() => {
              handleMenuClick('Home');
            }}
          >
            Home
          </div>
          <div 
            className="menu-item"
            onClick={() => {
              handleMenuClick('My Playlists');
            }}
          >
            My Playlists
          </div>
          <div 
            className="menu-item"
            onClick={() => {
              handleMenuClick('Sign out');
            }}
          >
            Sign Out
          </div>
        </div>
      )}
    </div>
  );
};

export default Menu;