import React, { useState, useEffect } from 'react';
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

function RGBPanel({ rgbState }) {
  const [isOn, setIsOn] = useState(false);
  const [selectedColor, setSelectedColor] = useState(COLORS[0]);

  // Sync with global state from props
  useEffect(() => {
    if (rgbState) {
      setIsOn(rgbState.on);
      
      // Find matching color in COLORS array by RGB values
      const matchingColor = COLORS.find(c => 
        c.rgb[0] === rgbState.color.r && 
        c.rgb[1] === rgbState.color.g && 
        c.rgb[2] === rgbState.color.b
      );
      
      if (matchingColor) {
        setSelectedColor(matchingColor);
      } else {
        // Fallback for custom colors if needed
        setSelectedColor({
          name: 'Custom',
          hex: `rgb(${rgbState.color.r}, ${rgbState.color.g}, ${rgbState.color.b})`,
          rgb: [rgbState.color.r, rgbState.color.g, rgbState.color.b]
        });
      }
    }
  }, [rgbState]);

  const handleToggle = async () => {
    console.log('handleToggle called, isOn:', isOn);
    try {
      const url = isOn ? `${API_BASE}/rgb/off` : `${API_BASE}/rgb/on`;
      console.log('Sending POST to', url);
      
      const response = await fetch(url, {
        method: 'POST',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({})
      });
      
      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);
      setIsOn(!isOn);
    } catch (error) {
      console.error('Error toggling RGB:', error.message);
      alert('Error: ' + error.message);
    }
  };

  const handleColorChange = async (color) => {
    console.log('handleColorChange called, color:', color);
    try {
      setSelectedColor(color);
      console.log('Sending POST to /rgb/color');
      
      const response = await fetch(`${API_BASE}/rgb/color`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          r: color.rgb[0], 
          g: color.rgb[1], 
          b: color.rgb[2] 
        })
      });
      
      const data = await response.json();
      console.log('Response:', data);
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
