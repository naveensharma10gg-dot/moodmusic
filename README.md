# Mood Tunes - AI Mood Music Player by Naveen Sharma

Mood Tunes is Naveen Sharma's AI mood music player for discovering Punjabi songs, saving favorites, creating playlists, and getting music recommendations by mood. The project is built with Python, Streamlit, SQLite/MySQL, and a lightweight recommendation scorer.

Live app: https://naveensharma10gg-dot-moodmusic-app-5cpsl4.streamlit.app

Search name: Mood Tunes AI Mood Music Player by Naveen Sharma

## Features

- Public user login and account creation
- Login and signup with hashed passwords
- Mood-based music recommendations
- Music source URL support for audio files, YouTube, Spotify, SoundCloud, or any web link
- Save favorite songs
- Create playlists and add songs
- Listening history with mood-time charts
- User profile section
- Add/remove music from user and admin panels
- Admin dashboard for library and listener analytics

## MySQL Setup

1. Create a MySQL database using `schema.sql`, or let the app create tables automatically.
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
3. Update the MySQL username and password.

```powershell
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

## Run Locally

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```

If the existing virtual environment has problems, create a fresh one:

```powershell
python -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

## Deploy

See `DEPLOYMENT.md`.
