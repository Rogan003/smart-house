import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000';

const COLORS = [
  { name: 'Red', hex: '#ff0000', rgb: [255, 0, 0] },
  { name: 'Green', hex: '#00ff00', rgb: [0, 255, 0] },
  { name: 'Blue', hex: '#0000ff', rgb: [0, 0, 255] },
  { name: 'Yellow', hex: '#ffff00', rgb: [255, 255, 0] },
  { name: 'Purple', hex: '#ff00ff', rgb: [255, 0, 255] },
  { name: 'Cyan', hex: '#00ffff', rgb: [0, 255, 255] },
  { name: 'Orange', hex: '#ff8000', rgb: [255, 128, 0] },
  { name: 'White', hex: '#ffffff', rgb: [255, 255, 255] },
];

function RGBPanel() {
  const [isOn, setIsOn] = useState(false);
  const [selectedColor, setSelectedColor] = useState(COLORS[0]);

  const handleToggle = async () => {
    try {
      if (isOn) {
        await axios.post(`${API_BASE}/rgb/off`);
        setIsOn(false);
      } else {
        await axios.post(`${API_BASE}/rgb/on`);
        setIsOn(true);
      }
    } catch (error) {
      console.error('Error toggling RGB:', error);
    }
  };

  const handleColorChange = async (color) => {
    try {
      setSelectedColor(color);
      await axios.post(`${API_BASE}/rgb/color`, { 
        r: color.rgb[0], 
        g: color.rgb[1], 
        b: color.rgb[2] 
      });
      if (!isOn) {
        setIsOn(true);
      }
    } catch (error) {
      console.error('Error changing color:', error);
    }
  };

  return (
    <div className="panel">
      <h3>💡 BRGB Light Bulb</h3>
      
      <div 
        className="rgb-preview" 
        style={{ 
          backgroundColor: isOn ? selectedColor.hex : '#333',
          boxShadow: isOn ? `0 0 30px ${selectedColor.hex}` : 'none'
        }}
      />

      <button 
        className={`btn ${isOn ? 'btn-danger' : 'btn-success'}`} 
        onClick={handleToggle}
        style={{ width: '100%', marginBottom: '15px' }}
      >
        {isOn ? '💡 Turn Off' : '💡 Turn On'}
      </button>

      <p style={{ marginBottom: '10px' }}>Choose color:</p>
      <div className="color-picker">
        {COLORS.map((color) => (
          <button
            key={color.name}
            className={`color-btn ${selectedColor.name === color.name ? 'active' : ''}`}
            style={{ backgroundColor: color.hex }}
            onClick={() => handleColorChange(color)}
            title={color.name}
          />
        ))}
      </div>

      <div style={{ marginTop: '15px', fontSize: '0.85rem', color: 'rgba(255,255,255,0.7)' }}>
        <p>ℹ️ The light bulb can also be controlled via IR remote.</p>
        <p>Current color: <strong>{selectedColor.name}</strong></p>
      </div>
    </div>
  );
}

export default RGBPanel;
