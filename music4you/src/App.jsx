import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import LoginSignup from './Pages/LoginSignup';
import HomePage from './Pages/HomePage';
import PlaylistPage from './Pages/PlaylistPage';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={
            <LoginSignup 
              setIsAuthenticated={setIsAuthenticated} 
            />
          } 
        />
        <Route 
          path="/home" 
          element={
            isAuthenticated ? 
            <HomePage setIsAuthenticated={setIsAuthenticated} /> : 
            <Navigate to="/login" />
          } 
        />
        <Route 
          path="/playlists" 
          element={
            isAuthenticated ? 
            <PlaylistPage setIsAuthenticated={setIsAuthenticated} /> : 
            <Navigate to="/login" />
          } 
        />
        <Route path="/" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  );
}

export default App;