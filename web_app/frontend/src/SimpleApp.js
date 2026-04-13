import React, { useState, useEffect, useCallback } from 'react';
import './SimpleApp.css';

// Use environment variable for API URL, fallback to relative URL for Docker/nginx proxy
const API_URL = process.env.REACT_APP_API_URL || '';

// Security constants
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
const ALLOWED_EXTENSIONS = ['.txt', '.log', '.csv'];

/**
 * Sanitize filename to prevent path traversal
 * @param {string} filename - Original filename
 * @returns {string} - Sanitized filename
 */
const sanitizeFilename = (filename) => {
  if (!filename) return '';
  // Remove any path components
  const name = filename.split(/[\\/]/).pop();
  // Remove dangerous characters
  return name.replace(/[<>"'`&]/g, '');
};

/**
 * Validate file before upload
 * @param {File} file - File object
 * @returns {Object} - { valid: boolean, error: string }
 */
const validateFile = (file) => {
  if (!file) {
    return { valid: false, error: 'No file selected' };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    return { valid: false, error: `File size exceeds ${MAX_FILE_SIZE / (1024 * 1024)}MB limit` };
  }

  // Check file extension
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return { valid: false, error: `File type ${ext} not allowed. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}` };
  }

  return { valid: true, error: null };
};

/**
 * Secure token storage using sessionStorage (cleared on tab close)
 * Note: For production, consider using httpOnly cookies instead
 */
const tokenStorage = {
  get: () => {
    try {
      return sessionStorage.getItem('token');
    } catch {
      return null;
    }
  },
  set: (token) => {
    try {
      sessionStorage.setItem('token', token);
    } catch {
      console.error('Failed to store token');
    }
  },
  remove: () => {
    try {
      sessionStorage.removeItem('token');
      sessionStorage.removeItem('username');
    } catch {
      console.error('Failed to remove token');
    }
  },
  getUser: () => {
    try {
      return sessionStorage.getItem('username');
    } catch {
      return null;
    }
  },
  setUser: (username) => {
    try {
      sessionStorage.setItem('username', username);
    } catch {
      console.error('Failed to store username');
    }
  }
};

function SimpleApp() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [selectedParser, setSelectedParser] = useState('vpn');
  const [selectedFile, setSelectedFile] = useState(null);
  const [usernameFilter, setUsernameFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [validationError, setValidationError] = useState('');

  // Check for existing session on mount
  useEffect(() => {
    const token = tokenStorage.get();
    const storedUser = tokenStorage.getUser();
    if (token && storedUser) {
      // Verify token is still valid
      verifyToken(token).then(valid => {
        if (valid) {
          setIsLoggedIn(true);
        } else {
          tokenStorage.remove();
        }
      });
    }
  }, []);

  /**
   * Verify JWT token validity
   */
  const verifyToken = async (token) => {
    try {
      const response = await fetch(`${API_URL}/api/auth/verify`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return response.ok;
    } catch {
      return false;
    }
  };

  /**
   * Handle user login
   */
  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setValidationError('');

    // Input validation
    if (!username.trim()) {
      setValidationError('Username is required');
      return;
    }
    if (!password) {
      setValidationError('Password is required');
      return;
    }

    // Sanitize username
    const cleanUsername = username.trim().slice(0, 64);

    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ 
          username: cleanUsername, 
          password 
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        tokenStorage.set(data.access_token);
        tokenStorage.setUser(data.username);
        setIsLoggedIn(true);
        setPassword(''); // Clear password from memory
      } else {
        // Sanitize error message
        const errorMsg = data.error || 'Login failed';
        setError(errorMsg.slice(0, 200)); // Limit error message length
      }
    } catch (err) {
      setError('Connection error - make sure backend is running');
    }
  };

  /**
   * Handle file selection
   */
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFile(null);
    setResults(null);
    setError('');
    setValidationError('');

    if (!file) return;

    const validation = validateFile(file);
    if (!validation.valid) {
      setValidationError(validation.error);
      return;
    }

    setSelectedFile(file);
  };

  /**
   * Handle parse operation
   */
  const handleParse = async () => {
    setValidationError('');
    
    if (!selectedFile) {
      setValidationError('Please select a file');
      return;
    }

    if (selectedParser === 'vpn-shutdown') {
      if (!usernameFilter.trim()) {
        setValidationError('Please enter a username for VPN shutdown parser');
        return;
      }
      // Sanitize username filter
      const cleanFilter = usernameFilter.trim().slice(0, 64);
      if (!/^[a-zA-Z0-9_.-]+$/.test(cleanFilter)) {
        setValidationError('Username contains invalid characters');
        return;
      }
    }

    setLoading(true);
    setError('');
    setResults(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    if (selectedParser === 'vpn-shutdown') {
      formData.append('username', usernameFilter.trim().slice(0, 64));
    }

    const token = tokenStorage.get();
    
    try {
      const response = await fetch(`${API_URL}/api/parse/${selectedParser}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setResults(data);
      } else {
        const errorMsg = data.error || 'Parsing failed';
        setError(errorMsg.slice(0, 500)); // Limit error message length
      }
    } catch (err) {
      setError('Connection error - make sure backend is running');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle file download
   */
  const handleDownload = async () => {
    if (!results || !results.filename) return;

    const token = tokenStorage.get();

    try {
      const response = await fetch(`${API_URL}/api/download/${encodeURIComponent(results.filename)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = sanitizeFilename(results.filename);
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } else {
        setError('Download failed');
      }
    } catch (err) {
      setError('Download failed');
    }
  };

  /**
   * Handle logout
   */
  const handleLogout = useCallback(() => {
    tokenStorage.remove();
    setIsLoggedIn(false);
    setUsername('');
    setPassword('');
    setSelectedFile(null);
    setResults(null);
    setError('');
    setUsernameFilter('');
  }, []);

  if (!isLoggedIn) {
    return (
      <div className="container">
        <div className="login-box">
          <h1>🔐 Forti-DFIR Web</h1>
          <h2>Fortinet Log Parser</h2>
          <p className="description">
            Convert your Fortinet VPN and firewall logs into structured data with powerful parsing capabilities.
            <br /><strong>Supports both CSV and Fortinet log formats!</strong>
          </p>
          <form onSubmit={handleLogin}>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value.slice(0, 64))}
              required
              autoComplete="username"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
            <button type="submit">Sign In</button>
          </form>
          {validationError && <div className="validation-error">{validationError}</div>}
          {error && <div className="error">{error}</div>}
          <p className="hint">
            <strong>Security Notice:</strong> Use strong credentials in production.
            <br />Default: admin / admin123 (change immediately!)
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="header">
        <div>
          <h1>🛡️ Forti-DFIR Log Parser</h1>
          <p className="subtitle">Professional log analysis for DFIR investigations • CSV & Fortinet Format Support</p>
        </div>
        <div className="header-right">
          <span className="user-info">👤 {tokenStorage.getUser()}</span>
          <button onClick={handleLogout} className="logout-btn">Logout</button>
        </div>
      </div>

      {validationError && (
        <div className="validation-banner" onClick={() => setValidationError('')}>
          ⚠️ {validationError}
        </div>
      )}

      <div className="parser-box">
        <h2>🔍 Select Parser Type</h2>
        <div className="parser-options">
          <label className={selectedParser === 'vpn' ? 'selected' : ''}>
            <input
              type="radio"
              value="vpn"
              checked={selectedParser === 'vpn'}
              onChange={(e) => setSelectedParser(e.target.value)}
            />
            <div className="option-content">
              <span className="icon">🔑</span>
              <div>
                <strong>VPN Logs</strong>
                <p>Extract successful login details</p>
              </div>
            </div>
          </label>
          <label className={selectedParser === 'firewall' ? 'selected' : ''}>
            <input
              type="radio"
              value="firewall"
              checked={selectedParser === 'firewall'}
              onChange={(e) => setSelectedParser(e.target.value)}
            />
            <div className="option-content">
              <span className="icon">🛡️</span>
              <div>
                <strong>Firewall Logs</strong>
                <p>Aggregate traffic by destination</p>
              </div>
            </div>
          </label>
          <label className={selectedParser === 'vpn-shutdown' ? 'selected' : ''}>
            <input
              type="radio"
              value="vpn-shutdown"
              checked={selectedParser === 'vpn-shutdown'}
              onChange={(e) => setSelectedParser(e.target.value)}
            />
            <div className="option-content">
              <span className="icon">⚡</span>
              <div>
                <strong>VPN Shutdown</strong>
                <p>Analyze session termination data</p>
              </div>
            </div>
          </label>
        </div>

        {selectedParser === 'vpn-shutdown' && (
          <div className="username-input">
            <label>👤 Username Filter</label>
            <input
              type="text"
              placeholder="Enter username to filter (e.g., john.doe)"
              value={usernameFilter}
              onChange={(e) => setUsernameFilter(e.target.value.replace(/[^a-zA-Z0-9_.-]/g, '').slice(0, 64))}
              maxLength={64}
            />
            <small>Case-insensitive search for specific user sessions</small>
          </div>
        )}

        <div className="file-input">
          <label>📁 Log File Upload</label>
          <div className="file-upload-area">
            <input
              type="file"
              accept=".txt,.log,.csv"
              onChange={handleFileChange}
              id="file-input"
            />
            <div className="file-upload-text">
              {selectedFile ? (
                <span>✅ {sanitizeFilename(selectedFile.name)} ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)</span>
              ) : (
                <span>Choose a log file (.txt, .log, .csv)</span>
              )}
            </div>
          </div>
          <small style={{color: '#b0bec5', fontSize: '0.85rem', marginTop: '8px', display: 'block'}}>
            📋 <strong>Supports:</strong> Fortinet log format (key=value) and CSV format with headers
            <br />⚠️ Maximum file size: {MAX_FILE_SIZE / (1024 * 1024)} MB
          </small>
        </div>

        <button 
          onClick={handleParse} 
          disabled={loading || !selectedFile}
          className="parse-button"
        >
          {loading ? '⏳ Processing...' : '🚀 Parse File'}
        </button>

        {error && <div className="error">❌ {error}</div>}

        {results && (
          <div className="results">
            <h3>📊 Parse Results</h3>
            <div className="stats">
              <div className="stat-item">
                <span className="stat-number">{results.records?.toLocaleString() || 0}</span>
                <span className="stat-label">Records Found</span>
              </div>
              {results.total_mb && (
                <div className="stat-item">
                  <span className="stat-number">{results.total_mb?.toFixed(2) || '0.00'} MB</span>
                  <span className="stat-label">Total Data</span>
                </div>
              )}
              {results.format_detected && (
                <div className="stat-item">
                  <span className="stat-number">{results.format_detected?.toUpperCase() || 'UNKNOWN'}</span>
                  <span className="stat-label">Format Detected</span>
                </div>
              )}
            </div>
            
            <div className="action-buttons">
              <button onClick={handleDownload} className="download-button">
                💾 Download CSV
              </button>
              <button onClick={() => { setResults(null); setSelectedFile(null); }} className="clear-button">
                🗑️ Clear Results
              </button>
            </div>

            {results.preview && results.preview.length > 0 && (
              <div className="preview">
                <h4>👀 Preview (first {Math.min(10, results.preview.length)} records)</h4>
                <div className="table-wrapper">
                  <table>
                    <thead>
                      <tr>
                        {Object.keys(results.preview[0]).map(key => (
                          <th key={key}>{key.replace(/_/g, ' ').toUpperCase()}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {results.preview.slice(0, 10).map((row, idx) => (
                        <tr key={idx}>
                          {Object.values(row).map((val, i) => (
                            <td key={i} title={String(val)}>{String(val).slice(0, 50)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {results.records > 10 && (
                  <p className="preview-note">
                    Showing 10 of {results.records.toLocaleString()} records. Download CSV for complete data.
                  </p>
                )}
              </div>
            )}

            {results.message && (
              <p className="result-message">{results.message}</p>
            )}
          </div>
        )}
      </div>

      <footer className="footer">
        <p>🔬 Developed by IONSec Research Team | Forti-DFIR v1.0.0 | Multi-Format Support</p>
        <p className="security-notice">
          🔒 For security: Always use HTTPS in production. Change default credentials.
        </p>
      </footer>
    </div>
  );
}

export default SimpleApp;
