import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000';

function GrafanaPanel() {
  const [activeTab, setActiveTab] = useState('PI1');
  const [deleteLoading, setDeleteLoading] = useState(null);
  const [deleteMessage, setDeleteMessage] = useState(null);

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

  const handleDelete = async (target) => {
    const targetLabel = target === 'all' ? 'ALL' : target;
    if (!window.confirm(`Are you sure you want to delete ${targetLabel} data? This cannot be undone!`)) {
      return;
    }

    setDeleteLoading(target);
    setDeleteMessage(null);

    try {
      let url;
      if (target === 'all') {
        url = `${API_BASE}/data/delete/all`;
      } else if (target === 'server') {
        url = `${API_BASE}/data/delete/server`;
      } else {
        url = `${API_BASE}/data/delete/${target}`;
      }

      const response = await axios.delete(url);
      setDeleteMessage({ type: 'success', text: response.data.message });
      
      // Force refresh iframes
      setTimeout(() => {
        const iframes = document.querySelectorAll('.grafana-panel-item iframe');
        iframes.forEach(iframe => {
          iframe.src = iframe.src;
        });
      }, 500);
    } catch (error) {
      setDeleteMessage({ type: 'error', text: error.response?.data?.message || 'Error deleting data' });
    } finally {
      setDeleteLoading(null);
      // Clear message after 3 seconds
      setTimeout(() => setDeleteMessage(null), 3000);
    }
  };

  const renderDeleteButtons = (piName) => {
    return (
      <div className="tab-delete-buttons">
        <button 
          className={`tab-delete-btn ${piName.toLowerCase()}`}
          onClick={() => handleDelete(piName)}
          disabled={deleteLoading !== null}
        >
          {deleteLoading === piName ? '⏳...' : `🗑️ Delete ${piName} Data`}
        </button>
        <button 
          className="tab-delete-btn all"
          onClick={() => handleDelete('all')}
          disabled={deleteLoading !== null}
        >
          {deleteLoading === 'all' ? '⏳...' : '⚠️ Delete ALL Data'}
        </button>
        {deleteMessage && (
          <span className={`delete-message ${deleteMessage.type}`}>
            {deleteMessage.type === 'success' ? '✅' : '❌'} {deleteMessage.text}
          </span>
        )}
      </div>
    );
  };

  const renderSystemDeleteButtons = () => {
    return (
      <div className="tab-delete-buttons">
        <button 
          className="tab-delete-btn server"
          onClick={() => handleDelete('server')}
          disabled={deleteLoading !== null}
        >
          {deleteLoading === 'server' ? '⏳...' : '🖥️ Delete Server Data'}
        </button>
        <button 
          className="tab-delete-btn all"
          onClick={() => handleDelete('all')}
          disabled={deleteLoading !== null}
        >
          {deleteLoading === 'all' ? '⏳...' : '⚠️ Delete ALL Data'}
        </button>
        {deleteMessage && (
          <span className={`delete-message ${deleteMessage.type}`}>
            {deleteMessage.type === 'success' ? '✅' : '❌'} {deleteMessage.text}
          </span>
        )}
      </div>
    );
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
            <div className="tab-header">
              <h3>PI1 - Front Door (6 components)</h3>
              {renderDeleteButtons('PI1')}
            </div>
            {renderPanels(pi1Panels)}
          </div>
        )}
        {activeTab === 'PI2' && (
          <div>
            <div className="tab-header">
              <h3>PI2 - Kitchen + Second Door (7 components)</h3>
              {renderDeleteButtons('PI2')}
            </div>
            {renderPanels(pi2Panels)}
          </div>
        )}
        {activeTab === 'PI3' && (
          <div>
            <div className="tab-header">
              <h3>PI3 - Bedrooms + Living Room (6 components)</h3>
              {renderDeleteButtons('PI3')}
            </div>
            {renderPanels(pi3Panels)}
          </div>
        )}
        {activeTab === 'SYSTEM' && (
          <div>
            <div className="tab-header">
              <h3>🚨 System Events & Statistics (2 panels)</h3>
              {renderSystemDeleteButtons()}
            </div>
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
