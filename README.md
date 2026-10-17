# Mobile App Market Analysis

A bilingual Google Play research workspace with Arabic RTL and English LTR,
dark and light themes, competitor comparisons, rating-based sentiment, CSV
reports, and optional Gemini market-gap analysis.

## Run on Windows

```powershell
python -m venv .venv
python -m pip --python .venv/Scripts/python.exe install -r requirements.txt
.venv/Scripts/python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit. Search for apps, select two to four,
then start analysis. The header contains language and theme controls. Store
language/region is independent of interface language. The sidebar can collapse.
Gemini needs your own API key; search and comparisons do not.
Choose **Prepare CSV report** after analysis to create a UTF-8 review export.

## Review pipeline

Each Google Play request asks for exactly 500 reviews. Each page is deduplicated,
parsed and saved before requesting the next page. The final page may contain fewer
items if the store is exhausted. Analysis supports 500–10,000 reviews per app.
Transient failures retry twice and then display an error; previously saved
batches remain available. SQLite reads use chunks of 500, and review cards show
60 items per page. Store response time and availability remain network dependent.
Sentiment labels use star ratings, not an NLP classifier.

The wallpaper is local at `assets/market-wallpaper.jpeg`; no font CDN is required.
The SQLite database is created beside `app.py` on first analysis. API keys are
not written to the project. Optional environment variable: `GEMINI_API_KEY`.

## Verify

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

This clean project was adapted from the supplied Python application. Unrelated
audio/video, caches and the original runtime database are excluded from source.

Verification in this session: the full test suite passed, and the running app
was checked in a browser with Arabic RTL and English LTR in both themes. Live
Google Play requests and Gemini calls still depend on network access and a
Gemini API key, respectively.
