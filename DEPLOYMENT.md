# EcoWavE Deployment Guide

## Recommended path: Streamlit Community Cloud

EcoWavE is a Streamlit app, so the simplest deployment path is Streamlit Community Cloud.

## Files needed in GitHub

Upload these project files to a GitHub repository:

- `app.py`
- `requirements.txt`
- `schema.sql`
- `README.md`
- `.streamlit/config.toml`
- `.streamlit/secrets.toml.example`
- `assets/mood_tunes_logo.png`

Do not upload:

- `.streamlit/secrets.toml`
- `.venv/` or `venv/`
- report files, PDFs, logs, generated folders, or local batch files

## Database requirement

The deployed app cannot use your laptop MySQL server at `localhost`.

Create an online MySQL database first, for example on Railway, Aiven, Clever Cloud, or any hosting provider that gives you:

- host
- port
- username
- password
- database name

The app will create its tables automatically on first run.

## Streamlit secrets

In Streamlit Community Cloud, open app settings and paste this in the Secrets box:

```toml
[mysql]
host = "YOUR_ONLINE_MYSQL_HOST"
port = 3306
user = "YOUR_ONLINE_MYSQL_USER"
password = "YOUR_ONLINE_MYSQL_PASSWORD"
database = "mood_tunes"
```

## Deploy steps

1. Push the needed files to GitHub.
2. Go to Streamlit Community Cloud.
3. Click `Create app`.
4. Select your GitHub repository.
5. Set main file path to `app.py`.
6. Add the MySQL secrets in Advanced settings.
7. Click `Deploy`.

## Important notes

- Online music playback depends on source availability and browser rules.
- If the app shows a MySQL connection error after deployment, the problem is almost always the cloud database credentials or database network access rules.
- Keep `.streamlit/secrets.toml` private. It contains passwords.
