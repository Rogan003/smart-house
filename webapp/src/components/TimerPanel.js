import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000';

function TimerPanel() {
  const [minutes, setMinutes] = useState(0);
  const [seconds, setSeconds] = useState(0);
  const [addSeconds, setAddSeconds] = useState(10);
  const [timerDisplay, setTimerDisplay] = useState('00:00');
  const [isBlinking, setIsBlinking] = useState(false);

  const handleSetTimer = async () => {
    try {
      const totalSeconds = (parseInt(minutes) || 0) * 60 + (parseInt(seconds) || 0);
      await axios.post(`${API_BASE}/timer/set`, { seconds: totalSeconds });
      const mins = Math.floor(totalSeconds / 60);
      const secs = totalSeconds % 60;
      setTimerDisplay(`${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`);
      setIsBlinking(false);
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

  const handleResetTimer = async () => {
    try {
      await axios.post(`${API_BASE}/timer/set`, { seconds: 0 });
      setTimerDisplay('00:00');
      setIsBlinking(false);
    } catch (error) {
      console.error('Error resetting timer:', error);
    }
  };

  const handleStopTimer = async () => {
    try {
      await axios.post(`${API_BASE}/timer/stop`);
      setIsBlinking(false);
    } catch (error) {
      console.error('Error stopping timer:', error);
    }
  };

  return (
    <div className="panel">
      <h3>⏱️ Kitchen Timer</h3>
      
      <div className={`timer-display ${isBlinking ? 'blinking' : ''}`}>
        {timerDisplay}
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
        ⚙️ Save
      </button>

      <div className="timer-buttons" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '10px' }}>
        <button className="btn btn-danger" onClick={handleStopTimer}>
          ⏹️ Stop Blinking
        </button>
        <button className="btn btn-secondary" onClick={handleResetTimer} style={{ background: '#95a5a6' }}>
          🔄 Reset to 00:00
        </button>
      </div>

      <div style={{ marginTop: '15px', fontSize: '0.85rem', color: 'rgba(255,255,255,0.7)' }}>
        <p>ℹ️ BTN button adds {addSeconds} seconds to the timer.</p>
        <p>When time runs out, the 4SD display blinks with 00:00.</p>
      </div>
    </div>
  );
}

export default TimerPanel;
