# Tableau SUS

A Tableau-like web app for exploring public health datasets, with no code.
Upload an `.xlsx` (or Brazilian-style `.csv`) and drag-and-drop your way through
the data using [PyGWalker](https://github.com/Kanaries/pygwalker) (Graphic Walker,
an open-source Tableau alternative) on top of Streamlit.

## Features

- **Upload `.xlsx`/`.xls`** and pick the sheet to explore.
- **Brazilian CSV support** — separator (`;`), encoding (`latin-1`), decimal (`,`),
  thousands (`.`) are all configurable in the sidebar.
- **Drag-and-drop visual analysis** (bars, lines, scatter, facets, filters, aggregations).
- **DuckDB mode** toggle for larger datasets.
- **Save / restore chart configs** as JSON (handy because Streamlit Cloud storage is ephemeral).
- Data stays in the user's session — nothing is persisted server-side.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501.

## Deploy on GitHub + Streamlit Community Cloud

1. Create the repo and push (you already have GitHub auth set up on Ubuntu):

   ```bash
   cd tableau-sus
   git init
   git add .
   git commit -m "Tableau SUS: pygwalker + streamlit data explorer"
   git branch -M main
   git remote add origin git@github.com:<your-user>/tableau-sus.git
   git push -u origin main
   ```

2. Go to https://share.streamlit.io → **New app** → pick this repo,
   branch `main`, main file `app.py` → **Deploy**.

That's it — you'll get a public URL like `https://tableau-sus.streamlit.app`.

## Notes

- **App language:** the user-facing labels are in Portuguese (intended for SUS data
  and interns). Switch the strings in `app.py` to English if you prefer.
- **Spelling:** you asked for "Tableu SUS"; I used the standard spelling **Tableau SUS**
  in the title. If you want the original, change `page_title` / `st.title` in `app.py`
  and the repo name.
- **Telemetry:** PyGWalker shares anonymous feature-usage events by default (no data you
  analyze is sent). To go fully offline when running locally:
  `pygwalker config --set privacy=offline`.
- **Sensitive data:** `.gitignore` excludes `*.xlsx`/`*.csv` so you don't accidentally
  commit patient-level data. Keep it that way for anything from SINAN/SIVEP.
