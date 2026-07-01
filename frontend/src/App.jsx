import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './index.css';

function App() {
  const [mode, setMode] = useState('batting'); // 'batting' or 'bowling'
  const [targetEntity, setTargetEntity] = useState('Australia');
  const [stadiumName, setStadiumName] = useState('Eden Gardens');
  const [matchFormat, setMatchFormat] = useState('T20');
  const [loading, setLoading] = useState(false);
  const [playbook, setPlaybook] = useState(null);
  const [error, setError] = useState(null);

  const handleModeToggle = (selectedMode) => {
    setMode(selectedMode);
    if (selectedMode === 'batting') {
      setTargetEntity('Australia');
    } else {
      setTargetEntity('Travis Head');
    }
    setPlaybook(null);
    setError(null);
  };

  const generatePlaybook = async () => {
    setLoading(true);
    setError(null);
    setPlaybook(null);
    
    try {
      // Use Vercel Environment Variable if available, fallback to localhost for local dev
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mode: mode,
          target_entity: targetEntity,
          venue: stadiumName,
          format: matchFormat,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate playbook');
      }
      
      const data = await response.json();
      setPlaybook(data.playbook);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <nav className="top-nav">
        <div className="wordmark">AI SCOUTING</div>
        <button className="btn-ghost">SIGN IN</button>
      </nav>

      <div className="hero-section">
        <div className="hero-content">
          <h1 className="display-headline">
            CRICKET<br />ANALYSIS<br />ENGINE
          </h1>
          <p className="subheading">HIGH-OCTANE TACTICAL SCOUTING AT TOURNAMENT SCALE.</p>
        </div>
      </div>

      <div className="dark-card">
        <div style={{ display: 'flex', gap: '16px', marginBottom: '8px' }}>
          <button 
            className={`btn-ghost ${mode === 'batting' ? 'active' : ''}`}
            onClick={() => handleModeToggle('batting')}
          >
            BATTING PLAN
          </button>
          <button 
            className={`btn-ghost ${mode === 'bowling' ? 'active' : ''}`}
            onClick={() => handleModeToggle('bowling')}
          >
            BOWLING PLAN
          </button>
        </div>

        <div className="input-block">
          <label>Match Format</label>
          <select value={matchFormat} onChange={(e) => setMatchFormat(e.target.value)}>
            <option value="T20">T20 / IPL</option>
            <option value="ODI">ODI</option>
            <option value="Test">Test</option>
          </select>
        </div>
        
        <div className="input-block">
          <label>{mode === 'batting' ? 'Opposition Team' : 'Opposition Batter'}</label>
          <input 
            type="text" 
            value={targetEntity} 
            onChange={(e) => setTargetEntity(e.target.value)} 
            placeholder={mode === 'batting' ? "e.g. Australia" : "e.g. Travis Head"}
          />
        </div>
        
        <div className="input-block">
          <label>Stadium / Venue</label>
          <input 
            type="text" 
            value={stadiumName} 
            onChange={(e) => setStadiumName(e.target.value)} 
            placeholder="e.g. Eden Gardens"
          />
        </div>
        
        <button 
          className="btn-primary" 
          onClick={generatePlaybook}
          disabled={loading || !targetEntity || !stadiumName}
          style={{ marginTop: '16px', width: '100%' }}
        >
          {loading ? 'GENERATING...' : 'GENERATE ACTION PLAN'}
        </button>

        {error && (
          <div className="error-text">
            {error}
          </div>
        )}
      </div>

      {playbook && (
        <div className="white-floating-card">
          <ReactMarkdown>{playbook}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}

export default App;
