import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000';
axios.defaults.headers.post['Content-Type'] = 'application/json';

function TimerPanel() {
  const [minutes, setMinutes] = useState(0);
  const [seconds, setSeconds] = useState(0);
  const [addSeconds, setAddSeconds] = useState(10);
  const [timerDisplay, setTimerDisplay] = useState('00:00');
  const [isBlinking, setIsBlinking] = useState(false);

  // Fetch timer status from server periodically
  useEffect(() => {
    const fetchTimerStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE}/status`);
        if (response.data) {
          const timerSeconds = response.data.timer_seconds || 0;
          const blinking = response.data.timer_blinking || false;
          
          const mins = Math.floor(timerSeconds / 60);
          const secs = timerSeconds % 60;
          setTimerDisplay(`${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`);
          setIsBlinking(blinking);
        }
      } catch (error) {
        console.error('Error fetching timer status:', error);
      }
    };

    fetchTimerStatus();
    const interval = setInterval(fetchTimerStatus, 1000); // Update every second
    return () => clearInterval(interval);
  }, []);

  const handleSetTimer = async () => {
    try {
      const totalSeconds = (parseInt(minutes) || 0) * 60 + (parseInt(seconds) || 0);
      await axios.post(`${API_BASE}/timer/set`, { seconds: totalSeconds });
    } catch (error) {
      console.error('Error setting timer:', error);
    }
  };

  const handleConfigureAddSeconds = async () => {
    try {
      await axios.post(`${API_BASE}/timer/configure`, { add_seconds: parseInt(addSeconds) || 10 });
    } catch (error) {
      console.error('Error configuring add seconds:', error);
    }
  };

  const handleAddTime = async () => {
    try {
      await axios.post(`${API_BASE}/timer/add`);
    } catch (error) {
      console.error('Error adding time:', error);
    }
  };

  const handleResetTimer = async () => {
    try {
      await axios.post(`${API_BASE}/timer/reset`);
    } catch (error) {
      console.error('Error resetting timer:', error);
    }
  };

  const handleStopBlinking = async () => {
    try {
      await axios.post(`${API_BASE}/timer/stop`);
    } catch (error) {
      console.error('Error stopping timer:', error);
    }
  };

  return (
    <div className="panel">
      <h3>⏱️ Kitchen Timer (4SD)</h3>

      <div className={`timer-display ${isBlinking ? 'blinking' : ''}`}>
        {isBlinking ? '00:00' : timerDisplay}
      </div>

      <div className="input-group">
        <label>Minutes:</label>
        <input
          type="number"
          min="0"
          max="99"
          value={minutes}
          onChange={(e) => setMinutes(e.target.value)}
          placeholder="0"
        />
      </div>

      <div className="input-group">
        <label>Seconds:</label>
        <input
          type="number"
          min="0"
          max="59"
          value={seconds}
          onChange={(e) => setSeconds(e.target.value)}
          placeholder="0"
        />
      </div>

      <button className="btn btn-primary" onClick={handleSetTimer}>
        ▶️ Set Timer
      </button>

      <hr style={{ margin: '15px 0', opacity: 0.3 }} />

      <div className="input-group">
        <label>BTN adds (N sec):</label>
        <input
          type="number"
          min="1"
          max="60"
          value={addSeconds}
          onChange={(e) => setAddSeconds(e.target.value)}
          placeholder="10"
        />
      </div>

      <button className="btn btn-warning" onClick={handleConfigureAddSeconds}>
        ⚙️ Save Config
      </button>

      <button className="btn btn-success" onClick={handleAddTime} style={{ marginLeft: '10px' }}>
        ➕ Add {addSeconds}s
      </button>

      <div className="timer-buttons" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '15px' }}>
        <button className="btn btn-danger" onClick={handleStopBlinking}>
          ⏹️ Stop Blinking
        </button>
        <button className="btn btn-secondary" onClick={handleResetTimer} style={{ background: '#95a5a6' }}>
          🔄 Reset
        </button>
      </div>

      <div style={{ marginTop: '15px', fontSize: '0.85rem', color: 'rgba(255,255,255,0.7)' }}>
        <p>ℹ️ Timer value shown is from server (real-time).</p>
        <p>BTN button on PI2 adds {addSeconds} seconds.</p>
        <p>When time runs out, display blinks 00:00.</p>
      </div>
    </div>
  );
}

export default TimerPanel;
