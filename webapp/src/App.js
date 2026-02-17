import React, { useState, useEffect } from 'react';
import axios from 'axios';
import AlarmPanel from './components/AlarmPanel';
import TimerPanel from './components/TimerPanel';
import RGBPanel from './components/RGBPanel';
import SensorStatus from './components/SensorStatus';
import GrafanaPanel from './components/GrafanaPanel';
import WebCamera from './components/WebCamera';
import './App.css';

const API_BASE = 'http://localhost:5000';

function App() {
  const [alarmState, setAlarmState] = useState(false);
  const [systemActive, setSystemActive] = useState(false);
  const [peopleCount, setPeopleCount] = useState(0);
  const [sensorData, setSensorData] = useState({});

  // Fetch status periodically
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE}/status`);
        if (response.data) {
          setAlarmState(response.data.alarm || false);
          setSystemActive(response.data.system_active || false);
          setPeopleCount(response.data.people_count || 0);
          setSensorData(response.data.sensors || {});
        }
      } catch (error) {
        console.error('Error fetching status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleDeactivateAlarm = async () => {
    try {
      await axios.post(`${API_BASE}/alarm/deactivate`);
      setAlarmState(false);
    } catch (error) {
      console.error('Error deactivating alarm:', error);
    }
  };

  const handleActivateSystem = async () => {
    try {
      await axios.post(`${API_BASE}/system/activate`);
      setSystemActive(true);
    } catch (error) {
      console.error('Error activating system:', error);
    }
  };

  const handleDeactivateSystem = async () => {
    try {
      await axios.post(`${API_BASE}/system/deactivate`);
      setSystemActive(false);
    } catch (error) {
      console.error('Error deactivating system:', error);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🏠 Smart House Dashboard</h1>
        <div className="status-bar">
          <span className={`status-indicator ${alarmState ? 'alarm-active' : ''}`}>
            {alarmState ? '🚨 ALARM ACTIVE' : '✅ System OK'}
          </span>
          <span className="people-count">👥 People inside: {peopleCount}</span>
        </div>
      </header>

      <main className="dashboard">
        <section className="panel-row">
          <AlarmPanel 
            alarmState={alarmState}
            systemActive={systemActive}
            onDeactivateAlarm={handleDeactivateAlarm}
            onActivateSystem={handleActivateSystem}
            onDeactivateSystem={handleDeactivateSystem}
          />
          <TimerPanel />
          <RGBPanel />
        </section>

        <section className="panel-row">
          <SensorStatus sensorData={sensorData} />
        </section>

        <section className="panel-row">
          <WebCamera />
        </section>

        <section className="grafana-section">
          <h2>📊 Grafana Dashboard</h2>
          <GrafanaPanel />
        </section>
      </main>
    </div>
  );
}

export default App;
