from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get('/dashboard', response_class=HTMLResponse)
async def dashboard():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Store Intelligence Dashboard</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-grad: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
      --glass-bg: rgba(255, 255, 255, 0.85);
      --glass-border: rgba(0, 0, 0, 0.05);
      --accent: #2563eb;
      --accent-hover: #1d4ed8;
      --accent-green: #10b981;
      --accent-green-hover: #059669;
      --text-main: #0f172a;
      --text-muted: #64748b;
    }
    body {
      font-family: 'Inter', sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg-grad);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    header {
      width: 100%;
      padding: 30px 20px;
      text-align: center;
      background: rgba(255, 255, 255, 0.7);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--glass-border);
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
      margin-bottom: 20px;
    }
    h1 { margin: 0 0 10px 0; font-size: 2.2rem; font-weight: 700; color: #1e293b; }
    p.subtitle { margin: 0; color: var(--text-muted); font-size: 1rem; }
    
    .controls {
      display: flex;
      gap: 15px;
      justify-content: center;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }
    input {
      background: #ffffff;
      border: 1px solid #cbd5e1;
      color: var(--text-main);
      border-radius: 8px;
      padding: 12px 20px;
      font-size: 1rem;
      outline: none;
      width: 250px;
      box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
    }
    input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2); }
    button {
      background: var(--accent);
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 10px rgba(37, 99, 235, 0.2);
      transition: background 0.3s ease;
    }
    button:hover { background: var(--accent-hover); transform: translateY(-2px); }
    
    .btn-track {
      background: var(--accent-green);
      box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
    }
    .btn-track:hover { background: var(--accent-green-hover); }

    .video-grid {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 20px;
      width: 100%;
      max-width: 1400px;
      margin: 0 auto;
    }
    .video-card {
      background: #1e293b;
      border-radius: 12px;
      overflow: hidden;
      position: relative;
      box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
      width: calc(25% - 20px);
    }
    .video-card img {
      width: 100%;
      display: block;
    }
    .video-label {
      position: absolute;
      top: 10px;
      left: 10px;
      background: rgba(0,0,0,0.7);
      color: white;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 600;
    }
    
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 24px;
      width: 100%;
      max-width: 1400px;
      padding: 0 20px 60px 20px;
    }
    .card {
      background: var(--glass-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--glass-border);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
    }
    .card h2 {
      margin: 0 0 16px 0;
      font-size: 1.2rem;
      font-weight: 600;
      color: #334155;
      display: flex;
      align-items: center;
      gap: 8px;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 10px;
    }
    .card h2::before {
      content: '';
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--accent);
    }
    
    .stat-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    .stat-box {
      background: #f1f5f9;
      padding: 12px;
      border-radius: 8px;
      text-align: center;
    }
    .stat-label { font-size: 0.85rem; color: var(--text-muted); font-weight: 500; text-transform: uppercase; }
    .stat-value { font-size: 1.5rem; font-weight: 700; color: var(--accent); margin-top: 4px; }
    
    .anomaly-item {
      background: #fff0f2;
      border-left: 4px solid #f43f5e;
      padding: 12px;
      border-radius: 0 8px 8px 0;
      margin-bottom: 10px;
    }
    .anomaly-item.INFO { background: #eff6ff; border-left-color: #3b82f6; }
    .anomaly-title { font-weight: 600; font-size: 0.95rem; margin-bottom: 4px; }
    .anomaly-msg { font-size: 0.85rem; color: #475569; }
    
    .heatmap-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #f1f5f9;
      padding: 10px;
      border-radius: 6px;
      margin-bottom: 8px;
    }
    .zone-name { font-weight: 500; font-size: 0.9rem; }
    .zone-count { background: var(--accent); color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    
    .funnel-step {
      display: flex;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px dashed #cbd5e1;
    }
    .funnel-step:last-child { border-bottom: none; }
    .funnel-label { font-weight: 500; }
    .funnel-val { font-weight: 700; color: #0f172a; }
  </style>
</head>
<body>

  <header>
    <h1>Store Intelligence Dashboard</h1>
    <p class="subtitle">Real-time edge analytics and deep computer vision insights</p>
  </header>

  <div class="controls">
    <input id="storeId" value="STORE_1" placeholder="Enter Store ID" />
    <button onclick="refresh()">Fetch Live Data</button>
    <button class="btn-track" onclick="startTracking()">▶️ Start Live Tracking</button>
    <button onclick="stopTracking()" style="background-color: #f59e0b; color: white;">⏸️ Stop Tracking</button>
    <button onclick="resetDatabase()" style="background-color: #ef4444; color: white;">🗑️ Reset Database</button>
  </div>

  <div id="videoContainer" class="video-grid"></div>

  <div class="grid">
    <div class="card">
      <h2>Core Metrics</h2>
      <div id="metrics" class="stat-grid">Loading...</div>
    </div>
    <div class="card">
      <h2>Conversion Funnel</h2>
      <div id="funnel">Loading...</div>
    </div>
    <div class="card">
      <h2>Spatial Heatmap</h2>
      <div id="heatmap">Loading...</div>
    </div>
    <div class="card">
      <h2>System Anomalies</h2>
      <div id="anomalies">Loading...</div>
    </div>
  </div>

  <script>
    let pollInterval = null;

    async function fetchJson(url) {
      const separator = url.includes('?') ? '&' : '?';
      const response = await fetch(url + separator + 't=' + Date.now());
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return await response.json();
    }

    function formatTime(ms) {
      if (!ms) return '0s';
      return (ms / 1000).toFixed(1) + 's';
    }

    async function startTracking() {
      // Force kill any hanging MJPEG streams from the previous store
      window.stop();

      const storeId = document.getElementById('storeId').value.trim();
      const container = document.getElementById('videoContainer');
      container.innerHTML = '<div style="color:var(--text-muted);">Initializing AI models...</div>';
      
      try {
        const oldImages = container.querySelectorAll('img');
        oldImages.forEach(img => { img.src = ''; });
        
        const data = await fetchJson(`/stores/${storeId}/cameras`);
        container.innerHTML = '';
        data.cameras.forEach(cam => {
          const div = document.createElement('div');
          div.className = 'video-card';
          div.innerHTML = `
            <div class="video-label">${cam}</div>
            <img src="/stores/${storeId}/stream/${cam}" alt="Loading ${cam}..." />
          `;
          container.appendChild(div);
        });

        // Start polling metrics every 2 seconds
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(refresh, 2000);
        } catch (err) {
          container.innerHTML = `<div style="color:#ef4444;">Failed to start tracking: ${err.message}</div>`;
        }
      }

      function stopTracking() {
        window.stop();
        const container = document.getElementById('videoContainer');
        container.querySelectorAll('img').forEach(img => { img.src = ''; });
        container.innerHTML = '';
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = null;
      }

      async function resetDatabase() {
        if (!confirm('Are you sure you want to completely clear the database?')) return;
        try {
          const res = await fetch('/api/reset_db', { method: 'POST' });
          if (!res.ok) throw new Error(res.statusText);
          alert('Database reset successfully!');
          refresh();
        } catch (err) {
          alert('Failed to reset DB: ' + err.message);
        }
      }

    async function refresh() {
      const storeId = document.getElementById('storeId').value.trim();
      
      try {
        const metricsData = await fetchJson(`/stores/${storeId}/metrics`);
        const funnelData = await fetchJson(`/stores/${storeId}/funnel`);
        const heatmapData = await fetchJson(`/stores/${storeId}/heatmap`);
        const anomaliesData = await fetchJson(`/stores/${storeId}/anomalies`);

        // Render Metrics
        document.getElementById('metrics').innerHTML = `
          <div class="stat-box" style="grid-column: span 2; background: #e0f2fe;">
            <div class="stat-label" style="color: #0369a1;">Currently In Store</div>
            <div class="stat-value" style="color: #0284c7; font-size: 2rem;">${metricsData.currently_in_store || 0}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Total Visitors</div>
            <div class="stat-value">${metricsData.unique_visitors || 0}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Total Exited</div>
            <div class="stat-value">${metricsData.total_exited || 0}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Conversion Rate</div>
            <div class="stat-value">${((metricsData.conversion_rate || 0) * 100).toFixed(1)}%</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Queue Depth</div>
            <div class="stat-value">${metricsData.queue_depth || 0}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Abandon Rate</div>
            <div class="stat-value">${((metricsData.abandonment_rate || 0) * 100).toFixed(1)}%</div>
          </div>
          <div class="stat-box" style="grid-column: span 2;">
            <div class="stat-label">Avg Billing Wait Time</div>
            <div class="stat-value">${formatTime((metricsData.avg_dwell_per_zone || {})['BILLING'] || 0)}</div>
          </div>
        `;

        // Render Funnel
        const f = funnelData.funnel || {};
        document.getElementById('funnel').innerHTML = `
          <div class="funnel-step">
            <span class="funnel-label">Total Store Sessions</span>
            <span class="funnel-val">${f.total_sessions || 0}</span>
          </div>
          <div class="funnel-step">
            <span class="funnel-label">Joined Billing Queue</span>
            <span class="funnel-val">${f.billing_queue_joins || 0}</span>
          </div>
          <div class="funnel-step">
            <span class="funnel-label">Successful Purchases</span>
            <span class="funnel-val">${f.purchases || 0}</span>
          </div>
          <div class="funnel-step" style="background: #e0e7ff; padding: 12px; border-radius: 6px; margin-top: 10px; border: none;">
            <span class="funnel-label" style="color: #4338ca;">Overall Conversion</span>
            <span class="funnel-val" style="color: #4338ca;">${((f.overall_conversion || 0) * 100).toFixed(1)}%</span>
          </div>
        `;

        // Render Heatmap
        const hm = heatmapData.heatmap || {};
        if (Object.keys(hm).length === 0) {
            document.getElementById('heatmap').innerHTML = '<div style="color: #64748b;">No zone activity detected.</div>';
        } else {
            document.getElementById('heatmap').innerHTML = Object.entries(hm)
              .sort((a, b) => b[1] - a[1])
              .map(([zone, count]) => `
                <div class="heatmap-bar">
                  <span class="zone-name">${zone}</span>
                  <span class="zone-count">${count} visits</span>
                </div>
              `).join('');
        }

        // Render Anomalies
        const an = anomaliesData.anomalies || [];
        if (an.length === 0) {
            document.getElementById('anomalies').innerHTML = '<div style="color: #10b981; font-weight: 500;">✓ All systems nominal. No anomalies.</div>';
        } else {
            document.getElementById('anomalies').innerHTML = an.map(a => `
              <div class="anomaly-item ${a.severity}">
                <div class="anomaly-title">[${a.severity}] ${a.type}</div>
                <div class="anomaly-msg">${a.message}</div>
                <div class="anomaly-msg" style="margin-top: 4px; font-style: italic;">Action: ${a.suggested_action}</div>
              </div>
            `).join('');
        }

      } catch (err) {
        // Silently fail during polling to avoid alert spam
        console.error('Connection Error:', err.message);
      }
    }
    
    refresh();
  </script>
</body>
</html>
'''
