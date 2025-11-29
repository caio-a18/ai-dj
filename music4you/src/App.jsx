// App.jsx - DEBUG VERSION
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { useState, useEffect } from "react";
import LoginSignup from "./Pages/LoginSignup";
import HomePage from "./Pages/HomePage";
import PlaylistPage from "./Pages/PlaylistPage";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  console.log("App component rendering");

  useEffect(() => {
    console.log("App useEffect running");
    
    // Skip auth check entirely for now
    const checkAuth = () => {
      console.log("Setting isAuthenticated to false for testing");
      setIsAuthenticated(false);
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, []);

  console.log("Rendering App - isAuthenticated:", isAuthenticated, "isCheckingAuth:", isCheckingAuth);

  if (isCheckingAuth) {
    console.log("Showing loading screen");
    return (
      <div style={{ 
        background: '#1a1a1a', 
        color: 'white', 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        fontSize: '24px'
      }}>
        Loading... (Checking authentication)
      </div>
    );
  }

  console.log("Rendering router");
  return (
    <div style={{ background: '#1a1a1a', minHeight: '100vh' }}>
      <Router>
        <Routes>
          <Route
            path="/login"
            element={
              <div>
                <LoginSignup setIsAuthenticated={setIsAuthenticated} />
              </div>
            }
          />
          <Route
            path="/home"
            element={
              isAuthenticated ? (
                <HomePage setIsAuthenticated={setIsAuthenticated} />
              ) : (
                <Navigate to="/login" />
              )
            }
          />
          <Route
            path="/playlists"
            element={
              isAuthenticated ? (
                <PlaylistPage setIsAuthenticated={setIsAuthenticated} />
              ) : (
                <Navigate to="/login" />
              )
            }
          />
          <Route path="/" element={<Navigate to="/login" />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;
