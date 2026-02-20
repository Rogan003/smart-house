import React, { useState } from 'react';

function SensorStatus({ sensorData }) {
  const [activeTab, setActiveTab] = useState('PI1');

  // PI1 - Front Door sensors
  const pi1Sensors = [
    { key: 'DS1', name: 'Door Sensor 1', icon: '🚪', unit: '' },
    { key: 'DUS1', name: 'Distance 1', icon: '📏', unit: 'cm' },
    { key: 'DPIR1', name: 'Motion 1', icon: '👁️', unit: '' },
    { key: 'DL', name: 'Door LED', icon: '💡', unit: '' },
    { key: 'DB', name: 'Buzzer', icon: '🔔', unit: '' },
    { key: 'DMS', name: 'Membrane Switch', icon: '🔢', unit: '' },
  ];

  // PI2 - Kitchen + Second Door sensors
  const pi2Sensors = [
    { key: 'DS2', name: 'Door Sensor 2', icon: '🚪', unit: '' },
    { key: 'DUS2', name: 'Distance 2', icon: '📏', unit: 'cm' },
    { key: 'DPIR2', name: 'Motion 2', icon: '👁️', unit: '' },
    { key: 'DHT3', name: 'Temp Kitchen', icon: '🌡️', unit: '°C' },
    { key: 'GSG', name: 'Gyroscope', icon: '🔄', unit: '' },
    { key: 'BTN', name: 'Kitchen Button', icon: '🔘', unit: '' },
    { key: '4SD', name: '4-Digit Display', icon: '🔢', unit: '' },
  ];

  // PI3 - Bedrooms + Living Room sensors
  const pi3Sensors = [
    { key: 'DHT1', name: 'Temp Bedroom', icon: '🌡️', unit: '°C' },
    { key: 'DHT2', name: 'Temp Master Bedroom', icon: '🌡️', unit: '°C' },
    { key: 'DPIR3', name: 'Motion Living Room', icon: '👁️', unit: '' },
    { key: 'BRGB', name: 'RGB Light', icon: '🌈', unit: '' },
    { key: 'IR', name: 'IR Sensor', icon: '📡', unit: '' },
    { key: 'LCD', name: 'LCD Display', icon: '🖥️', unit: '' },
  ];

  const getValue = (key) => {
    if (sensorData && sensorData[key] !== undefined) {
      return sensorData[key];
    }
    return '-';
  };

  const formatValue = (value) => {
    // Round numeric values to 2 decimal places
    if (typeof value === 'number') {
      return Math.round(value * 100) / 100;
    }
    // Try to parse string as number and round it
    if (typeof value === 'string') {
      // Check if it's an RGB string like "rgb(255,0,0)"
      if (value.startsWith('rgb(')) {
        return <span style={{ 
          display: 'inline-block', 
          width: '20px', 
          height: '20px', 
          backgroundColor: value,
          borderRadius: '50%',
          verticalAlign: 'middle',
          border: '1px solid white'
        }}></span>;
      }

      const num = parseFloat(value);
      if (!isNaN(num) && value.match(/^-?\d+\.?\d*$/)) {
        return Math.round(num * 100) / 100;
      }
      // Truncate long strings
      if (value.length > 15) {
        return value.substring(0, 15) + '...';
      }
    }
    return value;
  };

  const renderSensorGrid = (sensors, isPi2 = false) => {
    return (
      <div className={`sensor-grid ${isPi2 ? 'pi2-grid' : ''}`}>
        {sensors.map((sensor) => (
          <div key={sensor.key} className="sensor-card">
            <div style={{ fontSize: '2rem' }}>{sensor.icon}</div>
            <div className="value" title={getValue(sensor.key)}>
              {formatValue(getValue(sensor.key))}{sensor.unit && getValue(sensor.key) !== '-' && ` ${sensor.unit}`}
            </div>
            <div className="label">{sensor.name}</div>
            <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.5)' }}>
              ({sensor.key})
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="panel" style={{ width: '100%' }}>
      <h3>📡 Current Sensor State</h3>
      
      <div className="sensor-tabs">
        <button
          className={`sensor-tab ${activeTab === 'PI1' ? 'active' : ''}`}
          onClick={() => setActiveTab('PI1')}
        >
          PI1 - Front Door
        </button>
        <button
          className={`sensor-tab ${activeTab === 'PI2' ? 'active' : ''}`}
          onClick={() => setActiveTab('PI2')}
        >
          PI2 - Kitchen
        </button>
        <button
          className={`sensor-tab ${activeTab === 'PI3' ? 'active' : ''}`}
          onClick={() => setActiveTab('PI3')}
        >
          PI3 - Bedrooms
        </button>
      </div>

      <div className="sensor-content">
        {activeTab === 'PI1' && (
          <div>
            <h4 style={{ marginBottom: '15px', color: '#3498db' }}>PI1 - Front Door (6 sensors)</h4>
            {renderSensorGrid(pi1Sensors)}
          </div>
        )}
        {activeTab === 'PI2' && (
          <div>
            <h4 style={{ marginBottom: '15px', color: '#3498db' }}>PI2 - Kitchen + Second Door (7 sensors)</h4>
            {renderSensorGrid(pi2Sensors, true)}
          </div>
        )}
        {activeTab === 'PI3' && (
          <div>
            <h4 style={{ marginBottom: '15px', color: '#3498db' }}>PI3 - Bedrooms + Living Room (6 sensors)</h4>
            {renderSensorGrid(pi3Sensors)}
          </div>
        )}
      </div>
    </div>
  );
}

export default SensorStatus;
