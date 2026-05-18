"""
Vercel Serverless Function - Minimal Entry Point.

This is a lightweight landing page that explains the deployment options.
The actual Streamlit app requires too many dependencies for serverless deployment.
"""

from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PHM Health Inequalities Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; 
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #1f77b4; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 1.1em; }
        .alert { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .alert strong { color: #856404; }
        .success { background: #d4edda; border-left-color: #28a745; }
        .success strong { color: #155724; }
        .steps { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .steps ol { margin-left: 20px; }
        .steps li { margin: 10px 0; }
        code { 
            background: #e9ecef; 
            padding: 2px 8px; 
            border-radius: 4px; 
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        pre { 
            background: #2d2d2d; 
            color: #f8f8f2;
            padding: 20px; 
            border-radius: 8px; 
            overflow-x: auto;
            margin: 15px 0;
        }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .btn {
            display: inline-block;
            background: #1f77b4;
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            margin: 10px 0;
            font-weight: 600;
        }
        .btn:hover { background: #145a8a; text-decoration: none; }
        .features { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }
        .feature { padding: 15px; background: #f8f9fa; border-radius: 8px; }
        @media (max-width: 600px) { .features { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 PHM Health Inequalities Dashboard</h1>
        <p class="subtitle">Population Health Management tool for analyzing health inequalities in England</p>
        
        <div class="alert">
            <strong>⚠️ Vercel Deployment Limitation</strong><br>
            This app requires heavy Python dependencies (pandas, numpy, plotly, streamlit) totaling ~800MB,
            which exceeds Vercel's 500MB Lambda limit. Please use one of the deployment options below.
        </div>
        
        <div class="success">
            <strong>✅ Recommended: Streamlit Cloud (Free)</strong>
            <p>The official platform for Streamlit apps - no configuration needed!</p>
        </div>
        
        <div class="steps">
            <h3>Deploy to Streamlit Cloud in 3 steps:</h3>
            <ol>
                <li>Go to <a href="https://streamlit.io/cloud" target="_blank">streamlit.io/cloud</a> and sign in with GitHub</li>
                <li>Click "New app" and select <code>mohammedimran2901/phm-health-inequalities</code></li>
                <li>Set Main file path to <code>src/dashboard/app.py</code> and click Deploy!</li>
            </ol>
            <a href="https://streamlit.io/cloud" class="btn" target="_blank">Go to Streamlit Cloud →</a>
        </div>
        
        <h3>🚀 Alternative: Run Locally</h3>
        <pre>git clone https://github.com/mohammedimran2901/phm-health-inequalities.git
cd phm-health-inequalities
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run src/dashboard/app.py</pre>
        
        <h3>📊 Features</h3>
        <div class="features">
            <div class="feature">✓ 32,844 LSOAs with IMD 2019 data</div>
            <div class="feature">✓ Core20PLUS5 NHS framework</div>
            <div class="feature">✓ Interactive inequality analysis</div>
            <div class="feature">✓ Geographic visualization</div>
            <div class="feature">✓ Slope Index of Inequality (SII)</div>
            <div class="feature">✓ OHID Fingertips API integration</div>
        </div>
        
        <p><strong>GitHub Repository:</strong><br>
        <a href="https://github.com/mohammedimran2901/phm-health-inequalities" target="_blank">
            github.com/mohammedimran2901/phm-health-inequalities
        </a></p>
    </div>
</body>
</html>"""
        
        self.wfile.write(html.encode())
        return
    
    def do_POST(self):
        self.do_GET()