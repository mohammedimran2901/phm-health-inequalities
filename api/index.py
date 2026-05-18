"""
Vercel Serverless Function Entry Point.

Note: Streamlit apps are not ideal for serverless deployment.
Consider using Streamlit Cloud (streamlit.io/cloud) instead.
"""

from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PHM Health Inequalities Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
                .info { background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin: 20px 0; }
                code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
                pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
                a { color: #0066cc; }
            </style>
        </head>
        <body>
            <h1>🏥 PHM Health Inequalities Dashboard</h1>
            
            <div class="warning">
                <strong>⚠️ Deployment Issue:</strong><br>
                This is a Streamlit application, which requires a long-running server.
                Vercel's serverless functions are not suitable for Streamlit apps.
            </div>
            
            <div class="info">
                <h3>✅ Recommended: Deploy to Streamlit Cloud (FREE)</h3>
                <ol>
                    <li>Go to <a href="https://streamlit.io/cloud" target="_blank">streamlit.io/cloud</a></li>
                    <li>Sign in with your GitHub account</li>
                    <li>Click "New app"</li>
                    <li>Select repository: <code>mohammedimran2901/phm-health-inequalities</code></li>
                    <li>Set Main file path: <code>src/dashboard/app.py</code></li>
                    <li>Click Deploy!</li>
                </ol>
            </div>
            
            <h3>🚀 Run Locally</h3>
            <pre>
git clone https://github.com/mohammedimran2901/phm-health-inequalities.git
cd phm-health-inequalities
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run src/dashboard/app.py
            </pre>
            
            <h3>📊 Features</h3>
            <ul>
                <li>32,844 LSOAs with IMD 2019 deprivation data</li>
                <li>Core20PLUS5 NHS framework tracking</li>
                <li>Interactive inequality analysis (SII, RII)</li>
                <li>Geographic visualization by Local Authority</li>
                <li>Real-time health indicators from OHID Fingertips API</li>
            </ul>
            
            <p><strong>GitHub:</strong> <a href="https://github.com/mohammedimran2901/phm-health-inequalities" target="_blank">
                github.com/mohammedimran2901/phm-health-inequalities
            </a></p>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
        return
    
    def do_POST(self):
        self.do_GET()