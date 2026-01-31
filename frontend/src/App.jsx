import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Wardrobe from './pages/Wardrobe';
import Recommendations from './pages/Recommendations';
import './App.css'

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if user is stored in localStorage
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  return (
    <Router>
      <div className="app">
        {user && (
          <nav className="navbar">
            <div className="nav-brand">时尚推荐系统</div>
            <div className="nav-links">
              <Link to="/wardrobe">我的衣橱</Link>
              <Link to="/recommendations">获取推荐</Link>
              <span className="user-info">你好，{user.username}！</span>
              <button onClick={handleLogout} className="btn-logout">退出</button>
            </div>
          </nav>
        )}

        <Routes>
          <Route
            path="/login"
            element={user ? <Navigate to="/wardrobe" /> : <Login onLogin={handleLogin} />}
          />
          <Route
            path="/register"
            element={user ? <Navigate to="/wardrobe" /> : <Register onLogin={handleLogin} />}
          />
          <Route
            path="/wardrobe"
            element={user ? <Wardrobe user={user} /> : <Navigate to="/login" />}
          />
          <Route
            path="/recommendations"
            element={user ? <Recommendations user={user} /> : <Navigate to="/login" />}
          />
          <Route
            path="/"
            element={<Navigate to={user ? "/wardrobe" : "/login"} />}
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App
