import { useState } from 'react';
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import Logo from '../assets/logo.png';

export default function Layout() {
  const { user, logout } = useApp();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  const isActive = (path) => location.pathname === path;

  const navLinks = [
    { to: '/', label: 'Dashboard' },
    { to: '/predictions', label: 'Predictions' },
    { to: '/game', label: 'Paper Trading' },
    { to: '/formulas', label: 'Formulas' },
    { to: '/profiles', label: 'Profiles' },
  ];

  return (
    <div>
      <nav className="navbar">
        <div className="logo">
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', textDecoration: 'none' }}>
            <div className="logo-mark">
              <img src={Logo} alt="FinScopeMX" />
            </div>
            <span className="logo-text">FinScopeMX</span>
          </Link>
        </div>

        <div className="nav-links-desktop">
          {navLinks.map(link => (
            <Link 
              key={link.to} 
              to={link.to} 
              className={`nav-link ${isActive(link.to) ? 'active' : ''}`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="nav-right">
          {user ? (
            <button className="nav-btn" onClick={handleLogout}>{user.username}</button>
          ) : (
            <div className="auth-buttons">
              <Link to="/login" className="nav-btn">Login</Link>
              <Link to="/register" className="nav-btn nav-btn-primary">Register</Link>
            </div>
          )}
          
          <button 
            className="mobile-menu-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {mobileMenuOpen ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </>
              ) : (
                <>
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </>
              )}
            </svg>
          </button>
        </div>
      </nav>

      {mobileMenuOpen && (
        <div className="mobile-menu">
          {navLinks.map(link => (
            <Link 
              key={link.to} 
              to={link.to} 
              className={`mobile-nav-link ${isActive(link.to) ? 'active' : ''}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <div className="mobile-nav-divider"></div>
          {user ? (
            <button className="mobile-nav-link" onClick={() => { handleLogout(); setMobileMenuOpen(false); }}>
              Logout ({user.username})
            </button>
          ) : (
            <>
              <Link 
                to="/login" 
                className="mobile-nav-link"
                onClick={() => setMobileMenuOpen(false)}
              >
                Login
              </Link>
              <Link 
                to="/register" 
                className="mobile-nav-link"
                onClick={() => setMobileMenuOpen(false)}
              >
                Register
              </Link>
            </>
          )}
        </div>
      )}

      <div className="disclaimer-bar">
        Educational tool only. Past performance does not guarantee future results. This site does not provide financial advice.
      </div>

      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
