import { Navigate, Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout() {
  const { user, logout, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <div className="app-layout">
      <nav className="navbar">
        <Link to="/" className="nav-brand">
          <img src="/emoteflow.svg" alt="" className="nav-logo" />
          EmoteFlow
        </Link>
        <div className="nav-links">
          {user.role === 'student' && (
            <Link
              to="/capture"
              className={location.pathname === '/capture' ? 'active' : ''}
            >
              Emotion Capture
            </Link>
          )}
          {(user.role === 'teacher' || user.role === 'admin') && (
            <Link
              to="/dashboard"
              className={location.pathname === '/dashboard' ? 'active' : ''}
            >
              Dashboard
            </Link>
          )}
          {user.role === 'admin' && (
            <Link
              to="/admin"
              className={location.pathname === '/admin' ? 'active' : ''}
            >
              Admin
            </Link>
          )}
        </div>
        <div className="nav-user">
          <span>{user.first_name} {user.last_name}</span>
          <span className="role-badge">{user.role}</span>
          <button onClick={logout} className="btn-logout">
            Logout
          </button>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
