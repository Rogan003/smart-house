import React, { useState } from 'react';

function WebCamera() {
  const [cameraUrl, setCameraUrl] = useState('http://192.168.107.145:8080/?action=stream');
  const [isConnected, setIsConnected] = useState(true);

  const handleUrlChange = (e) => {
    setCameraUrl(e.target.value);
  };

  const handleRefresh = () => {
    setIsConnected(false);
    setTimeout(() => setIsConnected(true), 100);
  };

  return (
    <div className="panel webcamera-panel">
      <h3>📹 Web Camera</h3>
      
      <div className="input-group">
        <label>Stream URL:</label>
        <input
          type="text"
          value={cameraUrl}
          onChange={handleUrlChange}
          placeholder="http://192.168.107.145:8080/?action=stream"
        />
        <button className="btn btn-primary" onClick={handleRefresh}>
          🔄 Refresh
        </button>
      </div>

      <div className="camera-container">
        {isConnected ? (
          <img
            src={cameraUrl}
            alt="Web Camera Stream"
            className="camera-stream"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'flex';
            }}
            onLoad={(e) => {
              e.target.style.display = 'block';
              if (e.target.nextSibling) {
                e.target.nextSibling.style.display = 'none';
              }
            }}
          />
        ) : null}
        <div className="camera-placeholder">
          <div className="camera-icon">📷</div>
          <p>Camera not available</p>
          <p className="camera-hint">
            Check if the Raspberry Pi with camera is on and the stream is active at:
          </p>
          <code>{cameraUrl}</code>
        </div>
      </div>

      <div className="camera-info">
        <p>ℹ️ To connect a web camera on Raspberry Pi:</p>
        <ol>
          <li>Start the stream on PI using mjpg-streamer</li>
          <li>Enter the stream URL above (e.g., http://192.168.107.145:8080/?action=stream)</li>
        </ol>
      </div>
    </div>
  );
}

export default WebCamera;
