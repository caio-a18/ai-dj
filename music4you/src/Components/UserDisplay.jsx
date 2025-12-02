import { useState, useEffect } from 'react';
import { CognitoService } from '../services/cognitoService';
import './UserDisplay.css';

const UserDisplay = () => {
  const [username, setUsername] = useState('');
  const [isLoading, setIsLoading] = useState(true);

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
      } catch (error) {
        console.error('Error fetching user data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserData();
  }, []);

  if (isLoading) {
    return <div className="user-display-loading">Loading...</div>;
  }

  return (
    <div className="user-display">
      <div className="welcome-text">Welcome,</div>
      <div className="username">{username}</div>
    </div>
  );
};

export default UserDisplay;