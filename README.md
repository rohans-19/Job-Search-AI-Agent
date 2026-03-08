# 💼 Job Search AI Agent

An AI-powered career assistant that searches live job listings via the **Adzuna API** and surfaces the results in a clean, interactive UI.

## Features

- Real-time job search across India powered by the Adzuna Jobs API
- Interactive Streamlit web app with job cards, table view, and CSV export
- Salary insights and per-search stats
- Naukri.com HTML scraper (bonus, no API key needed)
- Terminal chatbot mode inside the Jupyter notebook

## Live App

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

> Deploy your own copy — see the **Deployment** section below.

## Project Structure

```
app.py               ← Streamlit web app (deploy this)
requirements.txt     ← Python dependencies
.streamlit/
  config.toml        ← Theme configuration
jobSearch2.ipynb     ← Notebook with Adzuna API + Naukri scraper
```

## Getting Started Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploying to Streamlit Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select this repo → set **Main file path** to `app.py`.
4. Click **Deploy** — that's it!

Your Adzuna API credentials can be entered directly in the app's sidebar at runtime (no secrets needed for a personal deployment).

## API Keys

Free Adzuna API keys: [developer.adzuna.com](https://developer.adzuna.com/)

