import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user, updateUser } = useAuth();
  const [language, setLanguage] = useState(user?.preferred_language || 'es');
  const [theme, setTheme] = useState(user?.theme || 'dark');
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  async function handleSave() {
    try {
      setError('');
      await updateUser({
        preferred_language: language,
        theme: theme,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <h1>Settings</h1>
      
      <div className="card" style={{ maxWidth: '500px' }}>
        {error && <div className="error-message">{error}</div>}
        
        <div className="form-group">
          <label>Username</label>
          <input type="text" value={user?.username || ''} disabled />
        </div>
        
        <div className="form-group">
          <label>Language</label>
          <select value={language} onChange={e => setLanguage(e.target.value)}>
            <option value="es">Espanol</option>
            <option value="en">English</option>
          </select>
        </div>
        
        <div className="form-group">
          <label>Theme</label>
          <select value={theme} onChange={e => setTheme(e.target.value)}>
            <option value="dark">Dark</option>
            <option value="light">Light</option>
          </select>
        </div>

        <button onClick={handleSave} className="btn-primary">
          {saved ? 'Saved!' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
}
