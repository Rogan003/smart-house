import React, { useState } from 'react';

function GrafanaPanel() {
  const [activeTab, setActiveTab] = useState('PI1');

  const pi1Panels = [
    { name: 'Door Button 1', panelId: 'panel-1' },
    { name: 'Door Buzzer 1', panelId: 'panel-2' },
    { name: 'Door LED 1', panelId: 'panel-3' },
    { name: 'Door Membrane Switch', panelId: 'panel-4' },
    { name: 'Door Motion Sensor 1', panelId: 'panel-5' },
    { name: 'Door Distance Sensor 1', panelId: 'panel-6' },
  ];

  const pi2Panels = [
    { name: 'Door Button 2', panelId: 'panel-7' },
    { name: 'Kitchen Button', panelId: 'panel-8' },
    { name: 'Door Motion Sensor 2', panelId: 'panel-9' },
    { name: 'Door Distance Sensor 2', panelId: 'panel-10' },
    { name: 'Kitchen DHT', panelId: 'panel-11' },
    { name: 'Kitchen 4-Digit 7-Segment Display', panelId: 'panel-12' },
    { name: 'Gyroscope', panelId: 'panel-13' },
  ];

  const pi3Panels = [
    { name: 'Bedroom DHT', panelId: 'panel-14' },
    { name: 'Master Bedroom DHT', panelId: 'panel-15' },
    { name: 'Living Room Motion Sensor', panelId: 'panel-16' },
    { name: 'Living Room Display', panelId: 'panel-17' },
    { name: 'Bedroom RGB', panelId: 'panel-18' },
    { name: 'Bedroom IR', panelId: 'panel-19' },
  ];

  const systemPanels = [
    { name: 'Alarm Events', panelId: 'panel-20' },
    { name: 'People Count', panelId: 'panel-21' },
  ];

  const getIframeSrc = (panelId) => {
    return `http://localhost:3000/d-solo/iot-app-dashboard/iot-app-dashboard?orgId=1&refresh=5s&panelId=${panelId}&__feature.dashboardSceneSolo=true`;
  };

  const renderPanels = (panels) => {
    return (
      <div className="grafana-panels-grid">
        {panels.map((panel) => (
          <div key={panel.panelId} className="grafana-panel-item">
            <h4>{panel.name}</h4>
            <div className="iframe-container">
              <iframe
                src={getIframeSrc(panel.panelId)}
                frameBorder="0"
                title={panel.name}
              />
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="grafana-container">
      <div className="grafana-tabs">
        <button
          className={`grafana-tab ${activeTab === 'PI1' ? 'active' : ''}`}
          onClick={() => setActiveTab('PI1')}
        >
          PI1 - Front Door
        </button>
        <button
          className={`grafana-tab ${activeTab === 'PI2' ? 'active' : ''}`}
          onClick={() => setActiveTab('PI2')}
        >
          PI2 - Kitchen
        </button>
        <button
          className={`grafana-tab ${activeTab === 'PI3' ? 'active' : ''}`}
          onClick={() => setActiveTab('PI3')}
        >
          PI3 - Bedrooms
        </button>
        <button
          className={`grafana-tab ${activeTab === 'SYSTEM' ? 'active' : ''}`}
          onClick={() => setActiveTab('SYSTEM')}
        >
          🚨 System & Alarms
        </button>
      </div>

      <div className="grafana-content">
        {activeTab === 'PI1' && (
          <div>
            <h3>PI1 - Front Door (6 components)</h3>
            {renderPanels(pi1Panels)}
          </div>
        )}
        {activeTab === 'PI2' && (
          <div>
            <h3>PI2 - Kitchen + Second Door (7 components)</h3>
            {renderPanels(pi2Panels)}
          </div>
        )}
        {activeTab === 'PI3' && (
          <div>
            <h3>PI3 - Bedrooms + Living Room (6 components)</h3>
            {renderPanels(pi3Panels)}
          </div>
        )}
        {activeTab === 'SYSTEM' && (
          <div>
            <h3>🚨 System Events & Statistics (2 panels)</h3>
            {renderPanels(systemPanels)}
          </div>
        )}
      </div>

      <div style={{ marginTop: '20px', fontSize: '0.85rem', color: 'rgba(255,255,255,0.7)' }}>
        <p>ℹ️ Grafana Dashboard displays real-time data from all sensors.</p>
        <p>Direct access: <a href="http://localhost:3000" target="_blank" rel="noopener noreferrer" style={{ color: '#3498db' }}>http://localhost:3000</a></p>
        <p>Login: admin / admin_password</p>
      </div>
    </div>
  );
}

export default GrafanaPanel;
