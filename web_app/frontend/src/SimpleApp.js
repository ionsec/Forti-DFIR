import React, { useState } from 'react';
import './SimpleApp.css';

// Use environment variable for API URL, fallback to relative URL for Docker/nginx proxy
const API_URL = process.env.REACT_APP_API_URL || '';

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

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setIsLoggedIn(true);
        localStorage.setItem('token', data.access_token);
      } else {
        setError(data.error || 'Login failed');
      }
    } catch (err) {
      setError('Connection error - make sure backend is running');
    }
  };

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setResults(null);
    setError('');
  };

  const handleParse = async () => {
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    if (selectedParser === 'vpn-shutdown' && !usernameFilter) {
      setError('Please enter a username for VPN shutdown parser');
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    if (selectedParser === 'vpn-shutdown') {
      formData.append('username', usernameFilter);
    }

    try {
      const response = await fetch(`${API_URL}/api/parse/${selectedParser}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setResults(data);
      } else {
        setError(data.error || 'Parsing failed');
      }
    } catch (err) {
      setError('Connection error - make sure backend is running');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!results || !results.filename) return;

    try {
      const response = await fetch(`${API_URL}/api/download/${results.filename}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = results.filename;
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

  const resetApp = () => {
    setIsLoggedIn(false);
    setUsername('');
    setPassword('');
    setSelectedFile(null);
    setResults(null);
    setError('');
    setUsernameFilter('');
    localStorage.removeItem('token');
  };

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
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button type="submit">Sign In</button>
          </form>
          {error && <div className="error">{error}</div>}
          <p className="hint">Default credentials: admin / admin123</p>
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
        <button onClick={resetApp} className="logout-btn">Logout</button>
      </div>

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
              onChange={(e) => setUsernameFilter(e.target.value)}
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
                <span>✅ {selectedFile.name}</span>
              ) : (
                <span>Choose a log file (.txt, .log, .csv)</span>
              )}
            </div>
          </div>
          <small style={{color: '#b0bec5', fontSize: '0.85rem', marginTop: '8px', display: 'block'}}>
            📋 <strong>Supports:</strong> Fortinet log format (key=value) and CSV format with headers
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
                <span className="stat-number">{results.records}</span>
                <span className="stat-label">Records Found</span>
              </div>
              {results.total_mb && (
                <div className="stat-item">
                  <span className="stat-number">{results.total_mb.toFixed(2)} MB</span>
                  <span className="stat-label">Total Data</span>
                </div>
              )}
              {results.format_detected && (
                <div className="stat-item">
                  <span className="stat-number">{results.format_detected.toUpperCase()}</span>
                  <span className="stat-label">Format Detected</span>
                </div>
              )}
            </div>
            
            <div className="action-buttons">
              <button onClick={handleDownload} className="download-button">
                💾 Download CSV
              </button>
              <button onClick={() => setResults(null)} className="clear-button">
                🗑️ Clear Results
              </button>
            </div>

            {results.preview && results.preview.length > 0 && (
              <div className="preview">
                <h4>👀 Preview (first 10 records)</h4>
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
                      {results.preview.map((row, idx) => (
                        <tr key={idx}>
                          {Object.values(row).map((val, i) => (
                            <td key={i} title={val}>{val}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {results.records > 10 && (
                  <p className="preview-note">
                    Showing 10 of {results.records} records. Download CSV for complete data.
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <footer className="footer">
        <p>🔬 Developed by IONSec Research Team | Forti-DFIR v1.0 | Multi-Format Support</p>
      </footer>
    </div>
  );
}

export default SimpleApp;