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
import SpotifyCallback from "./Pages/SpotifyCallback";
import { CognitoService } from "./services/cognitoService";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const result = await CognitoService.getCurrentUser();
        console.log("Auth check result:", result);
        setIsAuthenticated(result.success);
      } catch (error) {
        console.log("Auth check error:", error);
        setIsAuthenticated(false);
      } finally {
        setIsCheckingAuth(false);
      }
    };

    checkAuth();
  }, []);

  if (isCheckingAuth) {
    return (
      <div>Loading...</div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={
            !isAuthenticated ? (
              <LoginSignup setIsAuthenticated={setIsAuthenticated} />
            ) : (
              <Navigate to="/home" />
            )
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
        <Route
          path="/callback"
          element={<SpotifyCallback />}
        />
        <Route
          path="/"
          element={<Navigate to={isAuthenticated ? "/home" : "/login"} />}
        />
      </Routes>
    </Router>
  );
}

export default App;
