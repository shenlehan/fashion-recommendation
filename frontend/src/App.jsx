import { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Wardrobe from './pages/Wardrobe';
import Recommendations from './pages/Recommendations';
import Conversation from './pages/Conversation';
import Profile from './pages/Profile';
import './App.css'

function App() {
  const [user, setUser] = useState(null);
  const [globalUpload, setGlobalUpload] = useState({
    uploading: false,
    progress: { current: 0, total: 0 },
    onCancel: null
  });
  
  // 将 AbortController 提升到 App 层级，避免路由切换丢失
  const abortControllerRef = useRef(null);
  const isAbortedRef = useRef(false);

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

  const handleUpdateUser = (updatedUserData) => {
    const mergedUser = { ...user, ...updatedUserData };
    setUser(mergedUser);
    localStorage.setItem('user', JSON.stringify(mergedUser));
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
              <Link to="/conversation">对话调整</Link>
              <Link to="/profile">个人资料</Link>
              <span className="user-info">你好，{user.username}！</span>
              <button onClick={handleLogout} className="btn-logout">退出</button>
            </div>
          </nav>
        )}

        {/* 全局上传进度条 */}
        {globalUpload.uploading && (
          <div className="global-upload-bar">
            <div className="upload-info">
              <span className="upload-text">
                正在上传 {globalUpload.progress.current}/{globalUpload.progress.total} 件衣物...
              </span>
              {globalUpload.onCancel && (
                <button className="btn-cancel-upload" onClick={globalUpload.onCancel}>
                  取消上传
                </button>
              )}
            </div>
            <div className="global-progress-bar">
              <div 
                className="global-progress-fill" 
                style={{ 
                  width: `${globalUpload.progress.total > 0 ? (globalUpload.progress.current / globalUpload.progress.total) * 100 : 0}%` 
                }}
              ></div>
            </div>
          </div>
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
            element={user ? <Wardrobe user={user} setGlobalUpload={setGlobalUpload} isUploading={globalUpload.uploading} abortControllerRef={abortControllerRef} isAbortedRef={isAbortedRef} /> : <Navigate to="/login" />}
          />
          <Route
            path="/recommendations"
            element={user ? <Recommendations user={user} isUploading={globalUpload.uploading} /> : <Navigate to="/login" />}
          />
          <Route
            path="/conversation"
            element={user ? <Conversation user={user} isUploading={globalUpload.uploading} /> : <Navigate to="/login" />}
          />
          <Route
            path="/profile"
            element={user ? <Profile user={user} onUpdateUser={handleUpdateUser} /> : <Navigate to="/login" />}
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
