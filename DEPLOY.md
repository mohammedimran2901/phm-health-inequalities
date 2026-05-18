# 🚀 Deployment Guide

## Recommended: Streamlit Cloud (FREE)

The easiest and most reliable way to deploy this Streamlit app.

### Steps:

1. **Go to Streamlit Cloud**
   - Visit: https://streamlit.io/cloud
   - Sign in with your GitHub account

2. **Create New App**
   - Click "New app"
   - Select repository: `mohammedimran2901/phm-health-inequalities`
   - Set Main file path: `src/dashboard/app.py`
   - Choose Python version: 3.9 or higher
   - Click "Deploy!"

3. **Wait for deployment**
   - Streamlit Cloud will install dependencies from `requirements.txt`
   - App will be live at: `https://[your-app-name].streamlit.app`

### Advantages:
- ✅ Free tier available
- ✅ Automatic deployments on git push
- ✅ Perfect for Streamlit apps
- ✅ No configuration needed

---

## Alternative: Render.com

### Steps:

1. Go to https://render.com
2. Create a new Web Service
3. Connect your GitHub repository
4. Set:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run src/dashboard/app.py --server.port $PORT`
5. Deploy

---

## Local Development

```bash
# Clone repository
git clone https://github.com/mohammedimran2901/phm-health-inequalities.git
cd phm-health-inequalities

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run src/dashboard/app.py
```

Access at: http://localhost:8501

---

## ⚠️ Why Not Vercel?

**Vercel uses serverless functions**, which are designed for short-lived requests (APIs, SSR pages).

**Streamlit requires a long-running server** because:
- It maintains WebSocket connections for real-time updates
- It runs a continuous Python process
- It handles interactive widgets and state

While it's technically possible to hack Streamlit onto Vercel, it's not recommended because:
- Cold start delays (5-10 seconds)
- Function timeout limits (10-60 seconds)
- WebSocket limitations
- Higher costs

**Use Streamlit Cloud instead - it's specifically built for this!**

---

## Environment Variables

If you need to set environment variables (e.g., for API keys):

### Streamlit Cloud:
1. Go to your app dashboard
2. Click "Settings" → "Secrets"
3. Add your secrets in TOML format:

```toml
[api_keys]
fingertips_api_key = "your_key_here"
```

### Local Development:
Create a `.env` file:

```bash
FINGERTIPS_API_KEY=your_key_here
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError`
**Solution**: Ensure all dependencies are in `requirements.txt`

### Issue: `Port already in use`
**Solution**: 
```bash
streamlit run src/dashboard/app.py --server.port 8502
```

### Issue: Data not loading
**Solution**: The app downloads IMD data on first run. Ensure you have internet connectivity.

---

## Support

For issues or questions:
- Open an issue on GitHub: https://github.com/mohammedimran2901/phm-health-inequalities/issues
- Streamlit docs: https://docs.streamlit.io