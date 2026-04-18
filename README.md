# 💼 Job Search AI Agent

An AI-powered career assistant that searches live job listings via the **Adzuna API** and surfaces the results in a clean, interactive UI, as well as a fully modular Command Line Interface (CLI) that ranks jobs based on your PDF resume.

## Features

- **Resume Parsing:** Automatically extracts your skills right from your PDF resume (`resume_parser.py`, `skills.py`).
- **Live Job Search:** Fetches real-time jobs across India powered by the Adzuna Jobs API and extensible mock endpoints (`jobs.py`).
- **Smart Matching Engine:** Ranks jobs intelligently based on how well they match your extracted skills, preferred location, and salary requirements (`matcher.py`).
- **Company Insights:** Automatically researches the top hiring companies and grabs their official career links using Google Search and DuckDuckGo (`company.py`).
- **Streamlit Web App:** Interactive web app with job cards, table view, and CSV export (`app.py`).

## Project Structure

```text
main.py              ← 🚀 START HERE (The modern interactive CLI)
app.py               ← Original Streamlit web app UI
requirements.txt     ← Python dependencies

# Core Modules
resume_parser.py     ← Extracts text from PDF resumes (uses PyPDF2)
skills.py            ← Extracts deduplicated skills from text
jobs.py              ← Fetches and merges jobs from Adzuna API
matcher.py           ← Scoring logic to rank jobs tailored to you
company.py           ← Web scraper fetching company profile links
```

## Getting Started Locally

### 1. Install Dependencies
Make sure you have all required packages (like `PyPDF2`, `googlesearch-python`, `streamlit`, `requests`, `bs4`, `pandas`):
```bash
pip install -r requirements.txt
pip install PyPDF2 googlesearch-python
```

### 2. Run the AI Career CLI
The recommended way to use the fully featured tool:
```bash
python main.py
```
*It will ask you for your job role, location, minimum salary, and the path to your PDF resume. It will then fetch, rank, and present the top 5 smartest job opportunities with organized company links!*

### 3. Run the Streamlit UI
If you prefer a visual web interface (does not include resume parsing features):
```bash
streamlit run app.py
```

## API Keys

Free Adzuna API keys: [developer.adzuna.com](https://developer.adzuna.com/)

You can use the default test keys included in the codebase, or provide your own globally via environment variables (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`). For the Streamlit app, you can enter them directly in the sidebar.
