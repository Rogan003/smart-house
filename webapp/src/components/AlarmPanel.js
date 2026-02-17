import React from 'react';

function AlarmPanel({ alarmState, systemActive, onDeactivateAlarm, onActivateSystem, onDeactivateSystem }) {
  return (
    <div className="panel">
      <h3>🚨 Alarm Control</h3>
      
      <div className={`alarm-status ${alarmState ? 'active' : 'inactive'}`}>
        {alarmState ? '⚠️ ALARM IS ACTIVE!' : '✅ Alarm is off'}
      </div>

      <div className={`system-status ${systemActive ? 'active' : 'inactive'}`}>
        {systemActive ? '🔒 Security system ACTIVE' : '🔓 Security system inactive'}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {alarmState && (
          <button className="btn btn-danger" onClick={onDeactivateAlarm}>
            🔕 Deactivate Alarm
          </button>
        )}

        {!systemActive ? (
          <button className="btn btn-warning" onClick={onActivateSystem}>
            🔐 Activate Security System
          </button>
        ) : (
          <button className="btn btn-success" onClick={onDeactivateSystem}>
            🔓 Deactivate Security System
          </button>
        )}
      </div>

      <div style={{ marginTop: '15px', fontSize: '0.85rem', color: 'rgba(255,255,255,0.7)' }}>
        <p>ℹ️ Alarm is activated when:</p>
        <ul style={{ marginLeft: '20px', marginTop: '5px' }}>
          <li>Door remains open for more than 5 seconds</li>
          <li>System is active and motion is detected</li>
          <li>No one is inside and motion is detected</li>
          <li>GSG sensor detects significant movement</li>
        </ul>
      </div>
    </div>
  );
}

export default AlarmPanel;
