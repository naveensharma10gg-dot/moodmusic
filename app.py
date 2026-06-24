import hashlib
import html
import json
import secrets as token_secrets
import math
import os
import re
import socket
import sqlite3
import time
import urllib.request
import base64
from collections import Counter
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pandas as pd
import plotly.express as px
import pymysql
import streamlit as st
import streamlit.components.v1 as components
from streamlit_cookies_controller import CookieController
from yt_dlp import YoutubeDL


APP_TITLE = "EcoWavE"
SEO_TITLE = "EcoWavE - AI Mood Music Player by Naveen Sharma"
SEO_DESCRIPTION = (
    "EcoWavE is Naveen Sharma's AI mood music player for discovering Punjabi songs, "
    "saving favorites, creating playlists, and getting music recommendations by mood."
)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "mood_tunes_logo.png")
AUTH_COOKIE_NAME = "mood_tunes_login"
AUTH_COOKIE_DAYS = 30
MOODS = ["Happy", "Sad", "Romantic", "Calm", "Energetic", "Focus", "Nostalgic"]
DEFAULT_VOLUME_BOOST = 2.4
MAX_VOLUME_BOOST = 3.5
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


@st.cache_data(show_spinner=False)
def image_data_uri(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def logo_img_html(class_name="brand-logo", alt="EcoWavE logo"):
    uri = image_data_uri(LOGO_PATH)
    if not uri:
        return '<div class="brand-logo-fallback">EW</div>'
    return f'<img class="{class_name}" src="{uri}" alt="{html.escape(alt)}" />'


def show_private_admin_login():
    if os.getenv("MOOD_TUNES_SHOW_ADMIN_LOGIN") == "1":
        return True
    try:
        return bool(st.secrets.get("show_admin_login", False))
    except Exception:
        return False


def show_public_demo_account():
    if os.getenv("MOOD_TUNES_SHOW_DEMO_ACCOUNT") == "1":
        return True
    try:
        return bool(st.secrets.get("show_demo_account", False))
    except Exception:
        return False

SEED_USERS = [
    ("Admin", "admin@moodtunes.local", "admin123", "admin", "Energetic", "Library manager"),
]
PUBLIC_DEMO_USER = ("Demo Listener", "user@moodtunes.local", "user123", "user", "Happy", "Mood explorer")

MOOD_LIBRARY = {
    "Happy": {
        "genre": "Pop",
        "energy": 78,
        "valence": 86,
        "tracks": [
            ("Sunrise Drive", "Neon Lake"),
            ("Golden Weekend", "The Daybreaks"),
            ("Sugar Sky", "Mina Bloom"),
            ("Pocket Sunshine", "Juno Park"),
            ("Bright Side Walk", "City Sparks"),
            ("Lemon Soda", "Kaya Ray"),
            ("Up All Morning", "The Good Hours"),
            ("Firefly Parade", "Nova Lane"),
            ("Smile in Stereo", "Melo Crew"),
            ("Carousel Lights", "Pia Stone"),
            ("Good News Radio", "Juniper Club"),
            ("Beach Day Beat", "Sol Vista"),
            ("Dancing Shoes", "Rumi Coast"),
            ("Cloud Nine Cafe", "Ava Moon"),
            ("Warm Breeze", "Pacific Bloom"),
            ("High Five Heart", "The Pop Tones"),
            ("Happy Little Signal", "Luca Wells"),
            ("Neon Picnic", "Mango Street"),
            ("Weekend Colors", "Ivy June"),
            ("Shine Again", "North Pier"),
        ],
    },
    "Sad": {
        "genre": "Acoustic",
        "energy": 31,
        "valence": 28,
        "tracks": [
            ("Soft Rain Letters", "Mira Vale"),
            ("Empty Platform", "Noah Reed"),
            ("Blue Apartment", "Elara Finch"),
            ("Last Train Home", "The Quiet Miles"),
            ("Paper Moon Goodbye", "Lena Hart"),
            ("Fading Polaroid", "Arlo Grey"),
            ("After the Storm", "Mila Stone"),
            ("Window Seat Tears", "Owen Vale"),
            ("Cold Coffee", "Hazel North"),
            ("Half Written Song", "June Harbor"),
            ("Slow Goodbye", "Nico Field"),
            ("The Room Remembers", "Vera Lane"),
            ("Rain on Ash Street", "Finn Lowell"),
            ("Tired Satellites", "The Small Hours"),
            ("Hollow Avenue", "Rhea Moss"),
            ("Moonlit Apology", "Eli Shore"),
            ("Letters Unsent", "Cora Skye"),
            ("Dim Porch Light", "Atlas Reed"),
            ("Quiet Collapse", "Mara Blue"),
            ("Goodnight Anyway", "The Low Tides"),
        ],
    },
    "Romantic": {
        "genre": "R&B",
        "energy": 46,
        "valence": 74,
        "tracks": [
            ("Velvet Evening", "Aria Blue"),
            ("Slow Dance Signal", "Leo Voss"),
            ("Rosewater Room", "Sana Miles"),
            ("Midnight Promise", "Theo Bloom"),
            ("Paris on Replay", "Mira Sol"),
            ("Honeylight", "Jules Rivera"),
            ("Hold You Close", "The Satin Keys"),
            ("Two Cups of Moon", "Amara Vale"),
            ("Love in Low Light", "Nolan Reed"),
            ("Silk Road Home", "Eva Coast"),
            ("Red Wine Rhythm", "Kai Monroe"),
            ("Only Your Name", "Liana Hart"),
            ("Balcony Song", "The Soft Notes"),
            ("Heartbeats at 2 AM", "Rafi Lane"),
            ("Warm Hands", "Nora West"),
            ("Forever Maybe", "Isla Grey"),
            ("Quiet Flame", "Milo Stone"),
            ("Sweetest Gravity", "Zara Bloom"),
            ("Close Enough", "The Velvet Hours"),
            ("Starlit Us", "Ari June"),
        ],
    },
    "Calm": {
        "genre": "Ambient",
        "energy": 22,
        "valence": 66,
        "tracks": [
            ("Quiet Windows", "Lumen Field"),
            ("Still Lake", "Orion Vale"),
            ("Morning Incense", "Aya Moss"),
            ("Soft Horizon", "The Gentle North"),
            ("Blue Tea", "Nima Coast"),
            ("Cloud Garden", "Eden Shore"),
            ("Slow Lanterns", "Mara Sol"),
            ("Breathing Room", "Violet Field"),
            ("Open Palms", "Anya Reed"),
            ("Salt Air", "The Quiet Tides"),
            ("Low Tide Light", "Rio Hale"),
            ("Feather Path", "Suri Lane"),
            ("Moon Pool", "Noor Sky"),
            ("Sunday Silence", "Ilan Park"),
            ("Mist Over Pines", "Faye North"),
            ("Driftwood", "Luca Vale"),
            ("Gentle Orbit", "Nova Moss"),
            ("Small River", "The Soft Atlas"),
            ("Quiet Bloom", "Mina Wells"),
            ("Evening Exhale", "Ona Blue"),
        ],
    },
    "Energetic": {
        "genre": "Dance",
        "energy": 94,
        "valence": 81,
        "tracks": [
            ("Pulse Circuit", "DJ Atlas"),
            ("Run the Lights", "Volt Avenue"),
            ("Electric Jump", "Kira Flash"),
            ("Turbo Heart", "Max Neon"),
            ("Afterburn", "The Night Runners"),
            ("Stadium Sparks", "Rex Vibe"),
            ("Full Charge", "Zane Pulse"),
            ("Heatwave Sprint", "Nova Rush"),
            ("Bassline Rocket", "DJ Solstice"),
            ("No Brakes", "The Wild Tempo"),
            ("Adrenaline City", "Mika Volt"),
            ("Flashpoint", "Aero Lane"),
            ("Move Faster", "Juno Blaze"),
            ("Glowstick Gravity", "The Beat Patrol"),
            ("Redline", "Kai Circuit"),
            ("Ignition Mode", "Vera Vox"),
            ("Skyline Rush", "Milo Fire"),
            ("Amped Again", "The Charge Crew"),
            ("Festival Engine", "Luna Beat"),
            ("High Voltage Tonight", "Nico Spark"),
        ],
    },
    "Focus": {
        "genre": "Lo-fi",
        "energy": 41,
        "valence": 63,
        "tracks": [
            ("Deep Work", "Mono Desk"),
            ("Cafe Equations", "Pixel Rain"),
            ("Quiet Keyboard", "Nora Byte"),
            ("Deadline Drizzle", "The Study Loop"),
            ("Blue Notebook", "Atlas Page"),
            ("Late Night Syntax", "Milo Keys"),
            ("Paper Plan", "Sana Grid"),
            ("Clean Desk", "Lumen Code"),
            ("Soft Compiler", "Nova Tabs"),
            ("Library Glow", "The Focus Room"),
            ("Margin Notes", "Ivy Signal"),
            ("Steady Cursor", "Kai Method"),
            ("Reading Lamp", "Cora Plain"),
            ("Mind Map", "Vera Lines"),
            ("Silent Sprint", "Theo Draft"),
            ("Task Flow", "Eden Work"),
            ("Low Volume Logic", "Rafi Stack"),
            ("Inbox Zero", "The Calm Clicks"),
            ("Outline Mode", "Juniper Desk"),
            ("Finished Thought", "Owen Loop"),
        ],
    },
    "Nostalgic": {
        "genre": "Indie",
        "energy": 52,
        "valence": 48,
        "tracks": [
            ("Old Polaroids", "The Harbor"),
            ("Summer of 09", "Juniper Lane"),
            ("Cassette Heart", "Milo North"),
            ("Backseat Stars", "The Long Roads"),
            ("First Phone Call", "Lena Coast"),
            ("Faded Denim", "Aria Wells"),
            ("Corner Store Lights", "Nico Vale"),
            ("Home Movie", "The Attic Days"),
            ("Drive-In Moon", "Owen Park"),
            ("Schoolyard Echo", "Mira Stone"),
            ("Postcard Weather", "Theo Harbor"),
            ("Old Street Names", "Kaya Reed"),
            ("Mixtape Summer", "The Side B"),
            ("Porch Swing", "Hazel Bloom"),
            ("Then Again", "Rumi Field"),
            ("Photo Booth Smile", "Nova Grey"),
            ("Analog Dreams", "Ava Shore"),
            ("Last Bus Back", "Finn Lane"),
            ("Small Town Static", "Ivy Coast"),
            ("Remember When", "The Golden Hours"),
        ],
    },
}


def build_seed_songs():
    songs = []
    first_sources = {
        "Happy": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "Sad": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "Romantic": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "Calm": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
        "Energetic": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
        "Focus": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
        "Nostalgic": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3",
    }
    for mood_index, mood in enumerate(MOODS, start=1):
        library = MOOD_LIBRARY[mood]
        for track_index, (title, artist) in enumerate(library["tracks"], start=1):
            if track_index == 1:
                source_url = first_sources[mood]
            else:
                audio_index = ((mood_index * 20 + track_index) % 16) + 1
                mood_slug = mood.lower().replace(" ", "-")
                source_url = (
                    f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{audio_index}.mp3"
                    f"?mood={mood_slug}&track={track_index}"
                )
            duration = 210 + ((mood_index * 17 + track_index * 11) % 120)
            energy = max(0, min(100, library["energy"] + ((track_index % 5) - 2) * 3))
            valence = max(0, min(100, library["valence"] + ((track_index % 7) - 3) * 2))
            songs.append((title, artist, mood, library["genre"], source_url, duration, energy, valence))
    return songs


PUNJABI_HITS = [
    ("Winning Speech", "Karan Aujla", "Happy", "Punjabi Hip-Hop", "ytsearch1:Winning Speech Karan Aujla official video", 228, 88, 86),
    ("Softly", "Karan Aujla", "Happy", "Punjabi Pop", "ytsearch1:Softly Karan Aujla official video", 176, 82, 84),
    ("Players", "Karan Aujla", "Energetic", "Punjabi Hip-Hop", "ytsearch1:Players Karan Aujla Badshah official video", 190, 90, 82),
    ("Mexico", "Karan Aujla", "Energetic", "Punjabi Pop", "ytsearch1:Mexico Karan Aujla official video", 202, 86, 78),
    ("Admirin You", "Karan Aujla", "Romantic", "Punjabi Pop", "ytsearch1:Admirin You Karan Aujla official video", 214, 75, 76),
    ("52 Bars", "Karan Aujla", "Energetic", "Punjabi Hip-Hop", "ytsearch1:52 Bars Karan Aujla official video", 205, 92, 72),
    ("Tauba Tauba", "Karan Aujla", "Happy", "Punjabi Pop", "ytsearch1:Tauba Tauba Karan Aujla official video", 167, 90, 88),
    ("Old Skool", "Prem Dhillon", "Happy", "Punjabi Hip-Hop", "ytsearch1:Old Skool Prem Dhillon Sidhu Moose Wala official video", 236, 89, 82),
    ("Boot Cut", "Prem Dhillon", "Energetic", "Punjabi Pop", "ytsearch1:Boot Cut Prem Dhillon official video", 188, 84, 77),
    ("Lost Love", "Prem Dhillon", "Sad", "Punjabi", "ytsearch1:Lost Love Prem Dhillon official video", 214, 48, 38),
    ("Majha Block", "Prem Dhillon", "Energetic", "Punjabi Hip-Hop", "ytsearch1:Majha Block Prem Dhillon official video", 198, 88, 74),
    ("Brown Shortie", "Sidhu Moose Wala", "Happy", "Punjabi Hip-Hop", "ytsearch1:Brown Shortie Sidhu Moose Wala official audio", 196, 83, 78),
    ("295", "Sidhu Moose Wala", "Nostalgic", "Punjabi Hip-Hop", "ytsearch1:295 Sidhu Moose Wala official video", 270, 68, 48),
    ("So High", "Sidhu Moose Wala", "Energetic", "Punjabi Hip-Hop", "ytsearch1:So High Sidhu Moose Wala official video", 233, 92, 74),
    ("Levels", "Sidhu Moose Wala", "Energetic", "Punjabi Hip-Hop", "ytsearch1:Levels Sidhu Moose Wala Sunny Malton official video", 228, 94, 72),
    ("The Last Ride", "Sidhu Moose Wala", "Nostalgic", "Punjabi Hip-Hop", "ytsearch1:The Last Ride Sidhu Moose Wala official video", 254, 74, 45),
    ("Never Fold", "Sidhu Moose Wala", "Energetic", "Punjabi Hip-Hop", "ytsearch1:Never Fold Sidhu Moose Wala official audio", 203, 86, 68),
    ("Talja", "Jassa Dhillon", "Energetic", "Punjabi Pop", "ytsearch1:Talja Jassa Dhillon official video", 180, 90, 82),
    ("Raule", "Jassa Dhillon", "Happy", "Punjabi Pop", "ytsearch1:Raule Jassa Dhillon official video", 202, 82, 80),
    ("Above All", "Jassa Dhillon", "Energetic", "Punjabi Hip-Hop", "ytsearch1:Above All Jassa Dhillon official video", 186, 86, 72),
    ("Jatt Disda", "Jassa Dhillon", "Happy", "Punjabi Pop", "ytsearch1:Jatt Disda Jassa Dhillon official video", 190, 83, 79),
    ("25-25", "Arjan Dhillon", "Happy", "Punjabi Pop", "ytsearch1:25 25 Arjan Dhillon official video", 196, 82, 80),
    ("My Fellas", "Arjan Dhillon", "Energetic", "Punjabi Hip-Hop", "ytsearch1:My Fellas Arjan Dhillon official video", 214, 86, 76),
    ("Punjab Intro", "Arjan Dhillon", "Nostalgic", "Punjabi", "ytsearch1:Punjab Intro Arjan Dhillon official audio", 236, 72, 58),
    ("Mandeer", "Arjan Dhillon", "Energetic", "Punjabi Pop", "ytsearch1:Mandeer Arjan Dhillon official video", 205, 84, 75),
    ("Unbothered", "Navaan Sandhu", "Happy", "Punjabi Hip-Hop", "ytsearch1:Unbothered Navaan Sandhu official video", 205, 80, 77),
    ("Straight Outta Majha", "Navaan Sandhu", "Energetic", "Punjabi Hip-Hop", "ytsearch1:Straight Outta Majha Navaan Sandhu official video", 210, 88, 74),
    ("Jatt Life", "Navaan Sandhu", "Happy", "Punjabi Pop", "ytsearch1:Jatt Life Navaan Sandhu official video", 195, 82, 78),
    ("Brown Munde", "AP Dhillon", "Happy", "Punjabi Pop", "ytsearch1:Brown Munde AP Dhillon official video", 255, 84, 86),
    ("Excuses", "AP Dhillon", "Romantic", "Punjabi Pop", "ytsearch1:Excuses AP Dhillon official video", 176, 70, 76),
]

ARTIST_ALBUMS = {
    "Karan Aujla": ["Making Memories", "B.T.F.U", "Way Ahead", "Street Dreams", "Four Me"],
    "Prem Dhillon": ["No Lookin' Back", "Limitless", "Archives", "Old Skool"],
    "Sidhu Moose Wala": ["Moosetape", "PBX 1", "Snitches Get Stitches", "No Name", "The Last Ride"],
    "Jassa Dhillon": ["Above All", "Talja", "Bhalwani Gedi", "Jatt Disda"],
    "Arjan Dhillon": ["Awara", "A For Arjan", "Saroor", "Punjab Intro"],
    "Navaan Sandhu": ["Way Maker", "Relentless", "Straight Outta Majha", "Jatt Life"],
    "AP Dhillon": ["Not By Chance", "Two Hearts Never Break The Same", "Brown Munde", "Hidden Gems"],
    "Diljit Dosanjh": ["MoonChild Era", "G.O.A.T.", "Drive Thru", "Ghost"],
    "Shubh": ["Still Rollin", "Leo", "No Love", "Elevated"],
    "Nimrat Khaira": ["Nimmo", "Manmatti", "Designer", "Suit"],
}

TRACK_ALBUMS = {
    "Winning Speech": "Four Me",
    "Softly": "Making Memories",
    "Players": "Street Dreams",
    "Mexico": "Way Ahead",
    "Admirin You": "Making Memories",
    "52 Bars": "B.T.F.U",
    "Tauba Tauba": "Four Me",
    "Old Skool": "Old Skool",
    "Boot Cut": "No Lookin' Back",
    "Lost Love": "Archives",
    "Majha Block": "Limitless",
    "Brown Shortie": "Moosetape",
    "295": "Moosetape",
    "So High": "PBX 1",
    "Levels": "No Name",
    "The Last Ride": "The Last Ride",
    "Never Fold": "Snitches Get Stitches",
    "Talja": "Talja",
    "Raule": "Bhalwani Gedi",
    "Above All": "Above All",
    "Jatt Disda": "Jatt Disda",
    "25-25": "A For Arjan",
    "My Fellas": "Awara",
    "Punjab Intro": "Punjab Intro",
    "Mandeer": "Saroor",
    "Unbothered": "Relentless",
    "Straight Outta Majha": "Straight Outta Majha",
    "Jatt Life": "Jatt Life",
    "Brown Munde": "Not By Chance",
    "Excuses": "Hidden Gems",
}

MORE_PUNJABI_ARTIST_TRACKS = [
    ("G.O.A.T.", "Diljit Dosanjh", "Happy", "Punjabi Pop", "ytsearch1:G.O.A.T Diljit Dosanjh official video", 224, 88, 84),
    ("Born To Shine", "Diljit Dosanjh", "Happy", "Punjabi Pop", "ytsearch1:Born To Shine Diljit Dosanjh official video", 213, 86, 86),
    ("Lover", "Diljit Dosanjh", "Romantic", "Punjabi Pop", "ytsearch1:Lover Diljit Dosanjh official video", 190, 72, 82),
    ("Peaches", "Diljit Dosanjh", "Happy", "Punjabi Pop", "ytsearch1:Peaches Diljit Dosanjh official video", 198, 78, 80),
    ("No Love", "Shubh", "Energetic", "Punjabi Hip-Hop", "ytsearch1:No Love Shubh official video", 180, 86, 72),
    ("Still Rollin", "Shubh", "Energetic", "Punjabi Hip-Hop", "ytsearch1:Still Rollin Shubh official video", 176, 88, 74),
    ("Elevated", "Shubh", "Energetic", "Punjabi Hip-Hop", "ytsearch1:Elevated Shubh official video", 185, 90, 76),
    ("Cheques", "Shubh", "Happy", "Punjabi Hip-Hop", "ytsearch1:Cheques Shubh official video", 183, 82, 78),
    ("Designer", "Nimrat Khaira", "Happy", "Punjabi Pop", "ytsearch1:Designer Nimrat Khaira official video", 205, 76, 84),
    ("Suit", "Nimrat Khaira", "Happy", "Punjabi Pop", "ytsearch1:Suit Nimrat Khaira official video", 198, 74, 82),
    ("SP De Rank Wargi", "Nimrat Khaira", "Energetic", "Punjabi Pop", "ytsearch1:SP De Rank Wargi Nimrat Khaira official video", 214, 78, 80),
    ("Time Chakda", "Nimrat Khaira", "Happy", "Punjabi Pop", "ytsearch1:Time Chakda Nimrat Khaira official video", 190, 76, 78),
]

TRACK_ALBUMS.update(
    {
        "G.O.A.T.": "G.O.A.T.",
        "Born To Shine": "G.O.A.T.",
        "Lover": "MoonChild Era",
        "Peaches": "Drive Thru",
        "No Love": "No Love",
        "Still Rollin": "Still Rollin",
        "Elevated": "Elevated",
        "Cheques": "Still Rollin",
        "Designer": "Designer",
        "Suit": "Suit",
        "SP De Rank Wargi": "Nimmo",
        "Time Chakda": "Manmatti",
    }
)

ARTIST_ALBUMS.update(
    {
        "Arijit Singh": ["Sad Bollywood Essentials", "Romantic Bollywood Essentials", "Calm Bollywood Essentials"],
        "Jubin Nautiyal": ["Romantic Bollywood Essentials", "Sad Bollywood Essentials"],
        "Atif Aslam": ["Romantic Bollywood Essentials", "Nostalgic Bollywood Essentials"],
        "Shreya Ghoshal": ["Romantic Bollywood Essentials", "Calm Bollywood Essentials"],
        "B Praak": ["Sad Punjabi Essentials", "Romantic Punjabi Essentials"],
        "Amrinder Gill": ["Sad Punjabi Essentials", "Nostalgic Punjabi Essentials"],
        "Satinder Sartaaj": ["Calm Punjabi Essentials", "Nostalgic Punjabi Essentials"],
        "A.R. Rahman": ["Focus Bollywood Essentials", "Calm Bollywood Essentials"],
        "Pritam": ["Happy Bollywood Essentials", "Energetic Bollywood Essentials"],
    }
)

ALBUM_ARTIST_TRACKS = [
    ("Karan Aujla", "Making Memories", "Try Me", "Happy", "Punjabi Pop"),
    ("Karan Aujla", "Making Memories", "What...?", "Energetic", "Punjabi Hip-Hop"),
    ("Karan Aujla", "Making Memories", "Jee Ni Lagda", "Romantic", "Punjabi Pop"),
    ("Karan Aujla", "Making Memories", "Bachke Bachke", "Happy", "Punjabi Pop"),
    ("Karan Aujla", "B.T.F.U", "Click That B Kickin It", "Energetic", "Punjabi Hip-Hop"),
    ("Karan Aujla", "B.T.F.U", "Chu Gon Do", "Energetic", "Punjabi Hip-Hop"),
    ("Karan Aujla", "B.T.F.U", "Ask About Me", "Energetic", "Punjabi Hip-Hop"),
    ("Karan Aujla", "Way Ahead", "Game Over", "Energetic", "Punjabi Hip-Hop"),
    ("Karan Aujla", "Way Ahead", "They Know", "Energetic", "Punjabi Hip-Hop"),
    ("Karan Aujla", "Street Dreams", "Y.D.G.", "Energetic", "Punjabi Hip-Hop"),
    ("Karan Aujla", "Street Dreams", "God Damn", "Energetic", "Punjabi Hip-Hop"),
    ("Karan Aujla", "Four Me", "Who They", "Happy", "Punjabi Hip-Hop"),
    ("Prem Dhillon", "No Lookin' Back", "Pehla Wale", "Nostalgic", "Punjabi"),
    ("Prem Dhillon", "No Lookin' Back", "Jatt Hunde Aa", "Energetic", "Punjabi Pop"),
    ("Prem Dhillon", "Limitless", "Just A Dream", "Romantic", "Punjabi Pop"),
    ("Prem Dhillon", "Limitless", "Liv In", "Happy", "Punjabi Pop"),
    ("Prem Dhillon", "Archives", "Blames", "Sad", "Punjabi"),
    ("Prem Dhillon", "Archives", "Moonlight", "Romantic", "Punjabi"),
    ("Prem Dhillon", "Old Skool", "Badmashi", "Energetic", "Punjabi Hip-Hop"),
    ("Sidhu Moose Wala", "Moosetape", "Bitch I'm Back", "Energetic", "Punjabi Hip-Hop"),
    ("Sidhu Moose Wala", "Moosetape", "Celebrity Killer", "Energetic", "Punjabi Hip-Hop"),
    ("Sidhu Moose Wala", "Moosetape", "Aroma", "Nostalgic", "Punjabi Hip-Hop"),
    ("Sidhu Moose Wala", "Moosetape", "Signed To God", "Energetic", "Punjabi Hip-Hop"),
    ("Sidhu Moose Wala", "PBX 1", "Badfella", "Energetic", "Punjabi Hip-Hop"),
    ("Sidhu Moose Wala", "PBX 1", "Jatt Da Muqabala", "Energetic", "Punjabi Hip-Hop"),
    ("Sidhu Moose Wala", "Snitches Get Stitches", "Aj Kal Ve", "Romantic", "Punjabi"),
    ("Sidhu Moose Wala", "Snitches Get Stitches", "G-Shit", "Energetic", "Punjabi Hip-Hop"),
    ("Sidhu Moose Wala", "No Name", "Love Sick", "Sad", "Punjabi Hip-Hop"),
    ("Jassa Dhillon", "Above All", "Love Like Me", "Romantic", "Punjabi Pop"),
    ("Jassa Dhillon", "Above All", "Surma", "Happy", "Punjabi Pop"),
    ("Jassa Dhillon", "Talja", "Pyar Bolda", "Romantic", "Punjabi Pop"),
    ("Jassa Dhillon", "Bhalwani Gedi", "Spain", "Happy", "Punjabi Pop"),
    ("Jassa Dhillon", "Jatt Disda", "Mutiyare Ni", "Happy", "Punjabi Pop"),
    ("Arjan Dhillon", "Awara", "Kath", "Nostalgic", "Punjabi"),
    ("Arjan Dhillon", "Awara", "Danabaad", "Energetic", "Punjabi Pop"),
    ("Arjan Dhillon", "A For Arjan", "Jawani", "Happy", "Punjabi Pop"),
    ("Arjan Dhillon", "A For Arjan", "Hommie Call", "Energetic", "Punjabi Hip-Hop"),
    ("Arjan Dhillon", "Saroor", "Maharani Jindan", "Nostalgic", "Punjabi"),
    ("Arjan Dhillon", "Saroor", "Tape", "Energetic", "Punjabi Pop"),
    ("Navaan Sandhu", "Way Maker", "2 Asle", "Energetic", "Punjabi Hip-Hop"),
    ("Navaan Sandhu", "Way Maker", "Plug Talk", "Energetic", "Punjabi Hip-Hop"),
    ("Navaan Sandhu", "Relentless", "Rhyme Ain't Done", "Energetic", "Punjabi Hip-Hop"),
    ("Navaan Sandhu", "Relentless", "Sick Tone", "Energetic", "Punjabi Hip-Hop"),
    ("Navaan Sandhu", "Straight Outta Majha", "Black Life", "Energetic", "Punjabi Hip-Hop"),
    ("AP Dhillon", "Not By Chance", "Saada Pyaar", "Romantic", "Punjabi Pop"),
    ("AP Dhillon", "Not By Chance", "Majhail", "Energetic", "Punjabi Hip-Hop"),
    ("AP Dhillon", "Two Hearts Never Break The Same", "Summer High", "Romantic", "Punjabi Pop"),
    ("AP Dhillon", "Two Hearts Never Break The Same", "All Night", "Romantic", "Punjabi Pop"),
    ("AP Dhillon", "Hidden Gems", "Insane", "Happy", "Punjabi Pop"),
    ("AP Dhillon", "Hidden Gems", "Toxic", "Sad", "Punjabi Pop"),
    ("Diljit Dosanjh", "MoonChild Era", "Black & White", "Romantic", "Punjabi Pop"),
    ("Diljit Dosanjh", "MoonChild Era", "Vibe", "Happy", "Punjabi Pop"),
    ("Diljit Dosanjh", "G.O.A.T.", "Clash", "Energetic", "Punjabi Pop"),
    ("Diljit Dosanjh", "G.O.A.T.", "Patola", "Happy", "Punjabi Pop"),
    ("Diljit Dosanjh", "Drive Thru", "Lemonade", "Happy", "Punjabi Pop"),
    ("Diljit Dosanjh", "Ghost", "Case", "Energetic", "Punjabi Pop"),
    ("Shubh", "Still Rollin", "Dior", "Happy", "Punjabi Hip-Hop"),
    ("Shubh", "Still Rollin", "Baller", "Energetic", "Punjabi Hip-Hop"),
    ("Shubh", "Leo", "King Shit", "Energetic", "Punjabi Hip-Hop"),
    ("Shubh", "Leo", "Safety Off", "Energetic", "Punjabi Hip-Hop"),
    ("Nimrat Khaira", "Nimmo", "Sohne Sohne Suit", "Happy", "Punjabi Pop"),
    ("Nimrat Khaira", "Nimmo", "Lehnga", "Happy", "Punjabi Pop"),
    ("Nimrat Khaira", "Manmatti", "Rohab Rakhdi", "Happy", "Punjabi Pop"),
    ("Nimrat Khaira", "Designer", "Ajj Kal Ajj Kal", "Romantic", "Punjabi Pop"),
    ("Arijit Singh", "Sad Bollywood Essentials", "Humdard", "Sad", "Bollywood Sad"),
    ("Arijit Singh", "Sad Bollywood Essentials", "Lo Maan Liya", "Sad", "Bollywood Sad"),
    ("Arijit Singh", "Sad Bollywood Essentials", "Uska Hi Banana", "Sad", "Bollywood Sad"),
    ("Arijit Singh", "Romantic Bollywood Essentials", "Sooraj Dooba Hain", "Happy", "Bollywood Pop"),
    ("Arijit Singh", "Romantic Bollywood Essentials", "Zaalima", "Romantic", "Bollywood Romantic"),
    ("Arijit Singh", "Romantic Bollywood Essentials", "Sanam Re", "Romantic", "Bollywood Romantic"),
    ("Arijit Singh", "Calm Bollywood Essentials", "Safar", "Calm", "Bollywood Calm"),
    ("Arijit Singh", "Calm Bollywood Essentials", "Alizeh", "Calm", "Bollywood Calm"),
    ("Jubin Nautiyal", "Romantic Bollywood Essentials", "Raatan Lambiyan", "Romantic", "Bollywood Romantic"),
    ("Jubin Nautiyal", "Romantic Bollywood Essentials", "Dil Galti Kar Baitha Hai", "Romantic", "Bollywood Romantic"),
    ("Jubin Nautiyal", "Sad Bollywood Essentials", "Tujhe Kitna Chahein Aur", "Sad", "Bollywood Sad"),
    ("Atif Aslam", "Romantic Bollywood Essentials", "Dil Diyan Gallan", "Romantic", "Bollywood Romantic"),
    ("Atif Aslam", "Romantic Bollywood Essentials", "Dekhte Dekhte", "Romantic", "Bollywood Romantic"),
    ("Atif Aslam", "Nostalgic Bollywood Essentials", "Tere Sang Yaara", "Nostalgic", "Bollywood Nostalgic"),
    ("Shreya Ghoshal", "Romantic Bollywood Essentials", "Sun Raha Hai", "Romantic", "Bollywood Romantic"),
    ("Shreya Ghoshal", "Romantic Bollywood Essentials", "Manwa Laage", "Romantic", "Bollywood Romantic"),
    ("Shreya Ghoshal", "Calm Bollywood Essentials", "Aadha Ishq", "Calm", "Bollywood Calm"),
    ("B Praak", "Sad Punjabi Essentials", "Ranjha", "Sad", "Punjabi Sad"),
    ("B Praak", "Sad Punjabi Essentials", "Dil Tod Ke", "Sad", "Punjabi Sad"),
    ("B Praak", "Romantic Punjabi Essentials", "Teri Mitti", "Nostalgic", "Bollywood"),
    ("Amrinder Gill", "Sad Punjabi Essentials", "Mil Ke Baithange", "Sad", "Punjabi Sad"),
    ("Amrinder Gill", "Nostalgic Punjabi Essentials", "Mera Deewanapan", "Nostalgic", "Punjabi Nostalgic"),
    ("Satinder Sartaaj", "Calm Punjabi Essentials", "Sai", "Calm", "Punjabi Sufi"),
    ("Satinder Sartaaj", "Nostalgic Punjabi Essentials", "Masoomiyat", "Nostalgic", "Punjabi Sufi"),
    ("A.R. Rahman", "Focus Bollywood Essentials", "Maa Tujhe Salaam", "Focus", "Bollywood Focus"),
    ("A.R. Rahman", "Calm Bollywood Essentials", "Rehna Tu", "Calm", "Bollywood Calm"),
    ("Pritam", "Happy Bollywood Essentials", "Badtameez Dil", "Happy", "Bollywood Pop"),
    ("Pritam", "Energetic Bollywood Essentials", "Balam Pichkari", "Energetic", "Bollywood Dance"),
]

ALBUM_ARTIST_TRACKS.extend(
    [
        ("Karan Aujla", "Making Memories", "Champions Anthem", "Energetic", "Punjabi Hip-Hop"),
        ("Karan Aujla", "Making Memories", "IDK How", "Happy", "Punjabi Pop"),
        ("Karan Aujla", "Making Memories", "White Brown Black", "Energetic", "Punjabi Hip-Hop"),
        ("Karan Aujla", "B.T.F.U", "Gangsta", "Energetic", "Punjabi Hip-Hop"),
        ("Karan Aujla", "B.T.F.U", "On Top", "Energetic", "Punjabi Hip-Hop"),
        ("Karan Aujla", "Way Ahead", "Don't Look", "Energetic", "Punjabi Hip-Hop"),
        ("Karan Aujla", "Street Dreams", "Nothing Lasts", "Nostalgic", "Punjabi Hip-Hop"),
        ("Karan Aujla", "Four Me", "Antidote", "Happy", "Punjabi Pop"),
        ("Prem Dhillon", "No Lookin' Back", "Lost Life", "Sad", "Punjabi"),
        ("Prem Dhillon", "No Lookin' Back", "Geda Geda", "Happy", "Punjabi Pop"),
        ("Prem Dhillon", "Limitless", "Rich Life", "Energetic", "Punjabi Hip-Hop"),
        ("Prem Dhillon", "Limitless", "Schedule", "Energetic", "Punjabi Pop"),
        ("Prem Dhillon", "Archives", "Ain't Died In Vain", "Sad", "Punjabi"),
        ("Prem Dhillon", "Archives", "Rabba Ve", "Romantic", "Punjabi"),
        ("Prem Dhillon", "Old Skool", "Chitta Kurta", "Happy", "Punjabi Hip-Hop"),
        ("Sidhu Moose Wala", "Moosetape", "Burberry", "Energetic", "Punjabi Hip-Hop"),
        ("Sidhu Moose Wala", "Moosetape", "Regret", "Sad", "Punjabi Hip-Hop"),
        ("Sidhu Moose Wala", "Moosetape", "Malwa Block", "Energetic", "Punjabi Hip-Hop"),
        ("Sidhu Moose Wala", "Moosetape", "Me And My Girlfriend", "Romantic", "Punjabi Hip-Hop"),
        ("Sidhu Moose Wala", "PBX 1", "Selfmade", "Energetic", "Punjabi Hip-Hop"),
        ("Sidhu Moose Wala", "PBX 1", "Death Route", "Energetic", "Punjabi Hip-Hop"),
        ("Sidhu Moose Wala", "Snitches Get Stitches", "B-Town", "Energetic", "Punjabi Hip-Hop"),
        ("Sidhu Moose Wala", "No Name", "Everybody Hurts", "Sad", "Punjabi Hip-Hop"),
        ("Sidhu Moose Wala", "The Last Ride", "Dear Mama", "Nostalgic", "Punjabi"),
        ("Jassa Dhillon", "Above All", "Nishani", "Romantic", "Punjabi Pop"),
        ("Jassa Dhillon", "Above All", "Ki Haal", "Happy", "Punjabi Pop"),
        ("Jassa Dhillon", "Talja", "Keh Len De", "Energetic", "Punjabi Hip-Hop"),
        ("Jassa Dhillon", "Bhalwani Gedi", "Faraar", "Energetic", "Punjabi Pop"),
        ("Jassa Dhillon", "Jatt Disda", "Jhanjar", "Happy", "Punjabi Pop"),
        ("Arjan Dhillon", "Awara", "Youth Flow", "Energetic", "Punjabi Hip-Hop"),
        ("Arjan Dhillon", "Awara", "My Rules", "Energetic", "Punjabi Hip-Hop"),
        ("Arjan Dhillon", "A For Arjan", "Mxrci Season", "Happy", "Punjabi Pop"),
        ("Arjan Dhillon", "A For Arjan", "Sangdi Sangdi", "Romantic", "Punjabi Pop"),
        ("Arjan Dhillon", "Saroor", "Heer", "Romantic", "Punjabi"),
        ("Arjan Dhillon", "Saroor", "Raah Warga", "Nostalgic", "Punjabi"),
        ("Arjan Dhillon", "Punjab Intro", "Punjab Bolda", "Nostalgic", "Punjabi"),
        ("Navaan Sandhu", "Way Maker", "Radio", "Happy", "Punjabi Hip-Hop"),
        ("Navaan Sandhu", "Way Maker", "Hood Famous", "Energetic", "Punjabi Hip-Hop"),
        ("Navaan Sandhu", "Relentless", "Takeover", "Energetic", "Punjabi Hip-Hop"),
        ("Navaan Sandhu", "Relentless", "No Safety", "Energetic", "Punjabi Hip-Hop"),
        ("Navaan Sandhu", "Straight Outta Majha", "Majha Flow", "Energetic", "Punjabi Hip-Hop"),
        ("Navaan Sandhu", "Jatt Life", "Jatt Life 2", "Happy", "Punjabi Pop"),
        ("AP Dhillon", "Not By Chance", "Goat", "Energetic", "Punjabi Hip-Hop"),
        ("AP Dhillon", "Not By Chance", "Faraar", "Energetic", "Punjabi Pop"),
        ("AP Dhillon", "Two Hearts Never Break The Same", "Wo Noor", "Romantic", "Punjabi Pop"),
        ("AP Dhillon", "Two Hearts Never Break The Same", "Dil Nu", "Romantic", "Punjabi Pop"),
        ("AP Dhillon", "Hidden Gems", "Desires", "Romantic", "Punjabi Pop"),
        ("AP Dhillon", "Brown Munde", "Brown Munde Remix", "Happy", "Punjabi Pop"),
        ("Diljit Dosanjh", "MoonChild Era", "Void", "Calm", "Punjabi Pop"),
        ("Diljit Dosanjh", "MoonChild Era", "Champagne", "Happy", "Punjabi Pop"),
        ("Diljit Dosanjh", "G.O.A.T.", "Peed", "Romantic", "Punjabi Pop"),
        ("Diljit Dosanjh", "G.O.A.T.", "Whiskey", "Happy", "Punjabi Pop"),
        ("Diljit Dosanjh", "Drive Thru", "Vanilla", "Happy", "Punjabi Pop"),
        ("Diljit Dosanjh", "Ghost", "Kinni Kinni", "Romantic", "Punjabi Pop"),
        ("Diljit Dosanjh", "Ghost", "Feel My Love", "Romantic", "Punjabi Pop"),
        ("Shubh", "Still Rollin", "We Rollin", "Energetic", "Punjabi Hip-Hop"),
        ("Shubh", "Still Rollin", "OG", "Energetic", "Punjabi Hip-Hop"),
        ("Shubh", "Leo", "You And Me", "Romantic", "Punjabi Hip-Hop"),
        ("Shubh", "Leo", "Hood Anthem", "Energetic", "Punjabi Hip-Hop"),
        ("Shubh", "Elevated", "Her", "Romantic", "Punjabi Hip-Hop"),
        ("Nimrat Khaira", "Nimmo", "Photo", "Romantic", "Punjabi Pop"),
        ("Nimrat Khaira", "Nimmo", "Blink", "Happy", "Punjabi Pop"),
        ("Nimrat Khaira", "Manmatti", "Suit Patiala", "Happy", "Punjabi Pop"),
        ("Nimrat Khaira", "Designer", "Gall Mukk Gayi", "Romantic", "Punjabi Pop"),
        ("Nimrat Khaira", "Suit", "Jodi", "Romantic", "Punjabi Pop"),
        ("Arijit Singh", "Sad Bollywood Essentials", "Saware Reprise", "Sad", "Bollywood Sad"),
        ("Arijit Singh", "Sad Bollywood Essentials", "Darkhaast", "Sad", "Bollywood Sad"),
        ("Arijit Singh", "Sad Bollywood Essentials", "Khamoshiyan", "Sad", "Bollywood Sad"),
        ("Arijit Singh", "Romantic Bollywood Essentials", "Nashe Si Chadh Gayi", "Happy", "Bollywood Pop"),
        ("Arijit Singh", "Romantic Bollywood Essentials", "Dilliwaali Girlfriend", "Happy", "Bollywood Pop"),
        ("Arijit Singh", "Romantic Bollywood Essentials", "Itni Si Baat Hain", "Romantic", "Bollywood Romantic"),
        ("Arijit Singh", "Calm Bollywood Essentials", "Tose Naina", "Calm", "Bollywood Calm"),
        ("Arijit Singh", "Calm Bollywood Essentials", "Chunar", "Calm", "Bollywood Calm"),
        ("Jubin Nautiyal", "Romantic Bollywood Essentials", "Tum Hi Aana", "Romantic", "Bollywood Romantic"),
        ("Jubin Nautiyal", "Romantic Bollywood Essentials", "Meri Aashiqui", "Romantic", "Bollywood Romantic"),
        ("Jubin Nautiyal", "Sad Bollywood Essentials", "Bewafa Tera Masoom Chehra", "Sad", "Bollywood Sad"),
        ("Jubin Nautiyal", "Sad Bollywood Essentials", "Barsaat Ki Dhun", "Sad", "Bollywood Sad"),
        ("Atif Aslam", "Romantic Bollywood Essentials", "Main Rang Sharbaton Ka", "Romantic", "Bollywood Romantic"),
        ("Atif Aslam", "Romantic Bollywood Essentials", "Jeena Jeena", "Romantic", "Bollywood Romantic"),
        ("Atif Aslam", "Nostalgic Bollywood Essentials", "O Saathi", "Nostalgic", "Bollywood Nostalgic"),
        ("Atif Aslam", "Nostalgic Bollywood Essentials", "Be Intehaan", "Nostalgic", "Bollywood Nostalgic"),
        ("Shreya Ghoshal", "Romantic Bollywood Essentials", "Deewani Mastani", "Romantic", "Bollywood Romantic"),
        ("Shreya Ghoshal", "Romantic Bollywood Essentials", "Teri Meri", "Romantic", "Bollywood Romantic"),
        ("Shreya Ghoshal", "Calm Bollywood Essentials", "Saans", "Calm", "Bollywood Calm"),
        ("Shreya Ghoshal", "Calm Bollywood Essentials", "Hasi Ban Gaye", "Calm", "Bollywood Calm"),
        ("B Praak", "Sad Punjabi Essentials", "Baarish Ki Jaaye", "Sad", "Punjabi Sad"),
        ("B Praak", "Sad Punjabi Essentials", "Jaani Ve Jaani", "Sad", "Punjabi Sad"),
        ("B Praak", "Romantic Punjabi Essentials", "Mann Bharrya 2.0", "Romantic", "Punjabi Romantic"),
        ("B Praak", "Romantic Punjabi Essentials", "Kuch Bhi Ho Jaye", "Romantic", "Punjabi Romantic"),
        ("Amrinder Gill", "Sad Punjabi Essentials", "Supna", "Sad", "Punjabi Sad"),
        ("Amrinder Gill", "Sad Punjabi Essentials", "Ki Samjhaiye", "Sad", "Punjabi Sad"),
        ("Amrinder Gill", "Nostalgic Punjabi Essentials", "Judaa 2", "Nostalgic", "Punjabi Nostalgic"),
        ("Amrinder Gill", "Nostalgic Punjabi Essentials", "Kurta Suha", "Nostalgic", "Punjabi Nostalgic"),
        ("Satinder Sartaaj", "Calm Punjabi Essentials", "Udaarian Reprise", "Calm", "Punjabi Sufi"),
        ("Satinder Sartaaj", "Calm Punjabi Essentials", "Jalsa", "Calm", "Punjabi Sufi"),
        ("Satinder Sartaaj", "Nostalgic Punjabi Essentials", "Rutba", "Nostalgic", "Punjabi Sufi"),
        ("Satinder Sartaaj", "Nostalgic Punjabi Essentials", "Sajjan Raazi Reprise", "Nostalgic", "Punjabi Sufi"),
        ("A.R. Rahman", "Focus Bollywood Essentials", "Raanjhanaa Theme", "Focus", "Bollywood Focus"),
        ("A.R. Rahman", "Focus Bollywood Essentials", "Guru Theme", "Focus", "Bollywood Focus"),
        ("A.R. Rahman", "Calm Bollywood Essentials", "Aaromale", "Calm", "Bollywood Calm"),
        ("A.R. Rahman", "Calm Bollywood Essentials", "Khwaja Mere Khwaja", "Calm", "Bollywood Calm"),
        ("Pritam", "Happy Bollywood Essentials", "Galti Se Mistake", "Happy", "Bollywood Pop"),
        ("Pritam", "Happy Bollywood Essentials", "Character Dheela", "Happy", "Bollywood Pop"),
        ("Pritam", "Energetic Bollywood Essentials", "Jhoome Jo Pathaan", "Energetic", "Bollywood Dance"),
        ("Pritam", "Energetic Bollywood Essentials", "Malhari", "Energetic", "Bollywood Dance"),
    ]
)

ALBUM_TRACK_SEED_SONGS = [
    (
        title,
        artist,
        mood,
        genre,
        f"ytsearch1:{title} {artist} official song",
        185 + (index % 8) * 12,
        {"Happy": 82, "Energetic": 90, "Sad": 34, "Romantic": 66, "Calm": 32, "Focus": 42, "Nostalgic": 50}[mood],
        {"Happy": 84, "Energetic": 76, "Sad": 28, "Romantic": 74, "Calm": 62, "Focus": 58, "Nostalgic": 48}[mood],
    )
    for index, (artist, album, title, mood, genre) in enumerate(ALBUM_ARTIST_TRACKS, start=1)
]

for artist, album, title, _mood, _genre in ALBUM_ARTIST_TRACKS:
    ARTIST_ALBUMS.setdefault(artist, []).append(album)
    ARTIST_ALBUMS[artist] = sorted(set(ARTIST_ALBUMS[artist]))
    TRACK_ALBUMS.setdefault(title, album)


def build_mood_expansion():
    mood_tracks = {
        "Happy": [
            ("Gallan Goodiyaan", "Shankar Mahadevan", "Bollywood Pop"),
            ("London Thumakda", "Labh Janjua", "Bollywood Pop"),
            ("Kala Chashma", "Amar Arshi", "Bollywood Dance"),
            ("Nachde Ne Saare", "Jasleen Royal", "Bollywood Pop"),
            ("Morni Banke", "Guru Randhawa", "Punjabi Bollywood"),
        ],
        "Energetic": [
            ("Kar Gayi Chull", "Badshah", "Bollywood Dance"),
            ("Abhi Toh Party Shuru Hui Hai", "Badshah", "Bollywood Dance"),
            ("Proper Patola", "Diljit Dosanjh", "Punjabi Pop"),
            ("Sauda Khara Khara", "Diljit Dosanjh", "Punjabi Bollywood"),
            ("High Rated Gabru", "Guru Randhawa", "Punjabi Pop"),
        ],
        "Sad": [
            ("Channa Mereya", "Arijit Singh", "Bollywood Sad"),
            ("Agar Tum Saath Ho", "Arijit Singh", "Bollywood Sad"),
            ("Phir Bhi Tumko Chaahunga", "Arijit Singh", "Bollywood Sad"),
            ("Hamari Adhuri Kahani", "Arijit Singh", "Bollywood Sad"),
            ("Tujhe Kitna Chahne Lage", "Arijit Singh", "Bollywood Sad"),
            ("Bekhayali", "Arijit Singh", "Bollywood Sad"),
            ("Khairiyat", "Arijit Singh", "Bollywood Sad"),
            ("Kalank", "Arijit Singh", "Bollywood Sad"),
            ("Aayat", "Arijit Singh", "Bollywood Sad"),
            ("Laal Ishq", "Arijit Singh", "Bollywood Sad"),
            ("Duaa", "Arijit Singh", "Bollywood Sad"),
            ("Muskurane", "Arijit Singh", "Bollywood Sad"),
            ("Tera Yaar Hoon Main", "Arijit Singh", "Bollywood Sad"),
            ("Main Dhoondne Ko Zamaane Mein", "Arijit Singh", "Bollywood Sad"),
            ("Mann Bharrya", "B Praak", "Punjabi Sad"),
            ("Qismat", "Ammy Virk", "Punjabi Sad"),
            ("Khaab", "Akhil", "Punjabi Sad"),
            ("Judaa", "Amrinder Gill", "Punjabi Sad"),
            ("Diary", "Amrinder Gill", "Punjabi Sad"),
            ("Filhall", "B Praak", "Punjabi Sad"),
            ("Soch", "Hardy Sandhu", "Punjabi Sad"),
        ],
        "Romantic": [
            ("Tum Hi Ho", "Arijit Singh", "Bollywood Romantic"),
            ("Raabta", "Arijit Singh", "Bollywood Romantic"),
            ("Gerua", "Arijit Singh", "Bollywood Romantic"),
            ("Hawayein", "Arijit Singh", "Bollywood Romantic"),
            ("Shayad", "Arijit Singh", "Bollywood Romantic"),
            ("Kesariya", "Arijit Singh", "Bollywood Romantic"),
            ("Ae Dil Hai Mushkil", "Arijit Singh", "Bollywood Romantic"),
            ("Enna Sona", "Arijit Singh", "Bollywood Romantic"),
            ("Janam Janam", "Arijit Singh", "Bollywood Romantic"),
            ("Samjhawan", "Arijit Singh", "Bollywood Romantic"),
            ("Mast Magan", "Arijit Singh", "Bollywood Romantic"),
            ("Pal", "Arijit Singh", "Bollywood Romantic"),
            ("Roke Na Ruke Naina", "Arijit Singh", "Bollywood Romantic"),
            ("Pehli Dafa", "Atif Aslam", "Bollywood Romantic"),
            ("Jeene Laga Hoon", "Atif Aslam", "Bollywood Romantic"),
            ("Humnava Mere", "Jubin Nautiyal", "Bollywood Romantic"),
            ("Lut Gaye", "Jubin Nautiyal", "Bollywood Romantic"),
            ("Pani Da Rang", "Ayushmann Khurrana", "Punjabi Romantic"),
            ("Ikk Kudi", "Shahid Mallya", "Punjabi Romantic"),
            ("Khaab", "Akhil", "Punjabi Romantic"),
        ],
        "Calm": [
            ("Agar Tum Saath Ho Unplugged", "Arijit Singh", "Bollywood Calm"),
            ("Kabira Encore", "Arijit Singh", "Bollywood Calm"),
            ("Phir Le Aya Dil", "Arijit Singh", "Bollywood Calm"),
            ("Saware", "Arijit Singh", "Bollywood Calm"),
            ("Naina", "Arijit Singh", "Bollywood Calm"),
            ("Qaafirana", "Arijit Singh", "Bollywood Calm"),
            ("Hamdard", "Arijit Singh", "Bollywood Calm"),
            ("Sukoon Mila", "Arijit Singh", "Bollywood Calm"),
            ("Ilahi", "Arijit Singh", "Bollywood Calm"),
            ("Kun Faya Kun", "A.R. Rahman", "Bollywood Calm"),
            ("Tu Bin Bataye", "A.R. Rahman", "Bollywood Calm"),
            ("Jashn-E-Bahaaraa", "Javed Ali", "Bollywood Calm"),
            ("Iktara", "Kavita Seth", "Bollywood Calm"),
            ("Saibo", "Shreya Ghoshal", "Bollywood Calm"),
            ("Teri Ore", "Shreya Ghoshal", "Bollywood Calm"),
            ("Rabba Main Toh Mar Gaya Oye", "Shahid Mallya", "Bollywood Calm"),
            ("Saiyyan", "Kailash Kher", "Bollywood Calm"),
            ("Udaarian", "Satinder Sartaaj", "Punjabi Calm"),
            ("Sajjan Raazi", "Satinder Sartaaj", "Punjabi Calm"),
            ("Ikko Mikke", "Satinder Sartaaj", "Punjabi Calm"),
        ],
        "Focus": [
            ("Roobaroo Instrumental", "A.R. Rahman", "Bollywood Focus"),
            ("Tamasha Theme", "A.R. Rahman", "Bollywood Focus"),
            ("Rockstar Theme", "A.R. Rahman", "Bollywood Focus"),
            ("Bombay Theme", "A.R. Rahman", "Bollywood Focus"),
            ("Swades Theme", "A.R. Rahman", "Bollywood Focus"),
            ("Barfi Theme", "Pritam", "Bollywood Focus"),
            ("Wake Up Sid Theme", "Amit Trivedi", "Bollywood Focus"),
            ("Kai Po Che Theme", "Amit Trivedi", "Bollywood Focus"),
            ("Udaan Theme", "Amit Trivedi", "Bollywood Focus"),
            ("Lootera Theme", "Amit Trivedi", "Bollywood Focus"),
            ("Dear Zindagi Theme", "Amit Trivedi", "Bollywood Focus"),
            ("Piku Theme", "Anupam Roy", "Bollywood Focus"),
            ("October Theme", "Shantanu Moitra", "Bollywood Focus"),
            ("Yeh Haseen Vadiyan Instrumental", "A.R. Rahman", "Bollywood Focus"),
            ("Dil Se Re Instrumental", "A.R. Rahman", "Bollywood Focus"),
            ("Punjab Instrumental Lofi", "Punjabi Lofi", "Punjabi Focus"),
            ("Arijit Singh Lofi Study Mix", "Arijit Singh", "Bollywood Focus"),
            ("Bollywood Lofi Study Mix", "Bollywood Lofi", "Bollywood Focus"),
            ("Punjabi Chill Focus Mix", "Punjabi Lofi", "Punjabi Focus"),
            ("Sufi Focus Instrumental", "A.R. Rahman", "Bollywood Focus"),
        ],
        "Nostalgic": [
            ("Tera Hone Laga Hoon", "Atif Aslam", "Bollywood Nostalgic"),
            ("Pehli Nazar Mein", "Atif Aslam", "Bollywood Nostalgic"),
            ("Tu Jaane Na", "Atif Aslam", "Bollywood Nostalgic"),
            ("Woh Lamhe", "Atif Aslam", "Bollywood Nostalgic"),
            ("Tera Mera Rishta", "Mustafa Zahid", "Bollywood Nostalgic"),
            ("Maula Mere Maula", "Roop Kumar Rathod", "Bollywood Nostalgic"),
            ("Tujh Mein Rab Dikhta Hai", "Roop Kumar Rathod", "Bollywood Nostalgic"),
            ("Pee Loon", "Mohit Chauhan", "Bollywood Nostalgic"),
            ("Tum Se Hi", "Mohit Chauhan", "Bollywood Nostalgic"),
            ("Masakali", "Mohit Chauhan", "Bollywood Nostalgic"),
            ("Dooriyan", "Mohit Chauhan", "Bollywood Nostalgic"),
            ("Kabira", "Tochi Raina", "Bollywood Nostalgic"),
            ("Aaj Din Chadheya", "Rahat Fateh Ali Khan", "Bollywood Nostalgic"),
            ("Teri Deewani", "Kailash Kher", "Bollywood Nostalgic"),
            ("Yaar Anmulle", "Sharry Mann", "Punjabi Nostalgic"),
            ("3 Peg", "Sharry Mann", "Punjabi Nostalgic"),
            ("Bapu Zimidar", "Jassi Gill", "Punjabi Nostalgic"),
            ("Yaarian", "Amrinder Gill", "Punjabi Nostalgic"),
            ("Dildarian", "Amrinder Gill", "Punjabi Nostalgic"),
            ("Akhiyan", "Amrinder Gill", "Punjabi Nostalgic"),
        ],
    }
    songs = []
    mood_energy = {"Happy": 78, "Energetic": 92, "Sad": 36, "Romantic": 62, "Calm": 28, "Focus": 38, "Nostalgic": 48}
    mood_valence = {"Happy": 84, "Energetic": 76, "Sad": 30, "Romantic": 72, "Calm": 62, "Focus": 58, "Nostalgic": 46}
    for mood, tracks in mood_tracks.items():
        for index, (title, artist, genre) in enumerate(tracks, start=1):
            source_url = f"ytsearch1:{title} {artist} official song"
            songs.append(
                (
                    title,
                    artist,
                    mood,
                    genre,
                    source_url,
                    180 + (index % 7) * 13,
                    mood_energy[mood],
                    mood_valence[mood],
                )
            )
            TRACK_ALBUMS.setdefault(title, f"{mood} Essentials")
            ARTIST_ALBUMS.setdefault(artist, []).append(f"{mood} Essentials")
            ARTIST_ALBUMS[artist] = sorted(set(ARTIST_ALBUMS[artist]))
    return songs


MOOD_EXPANSION_TRACKS = build_mood_expansion()

SEED_SONGS = PUNJABI_HITS + MORE_PUNJABI_ARTIST_TRACKS + ALBUM_TRACK_SEED_SONGS + MOOD_EXPANSION_TRACKS


st.set_page_config(page_title=SEO_TITLE, page_icon="EW", layout="wide", initial_sidebar_state="collapsed")


def inject_styles():
    st.markdown(
        """
        <style>
        :root {
            --ink: #f8fbff;
            --panel: rgba(15, 20, 26, .82);
            --panel-strong: #10161d;
            --muted: #a7b4c3;
            --line: rgba(255, 255, 255, 0.13);
            --mint: #2dd4bf;
            --coral: #ff5f57;
            --gold: #f8c14a;
            --sky: #5aa9e6;
            --rose: #ef6f9f;
            --paper: #0b0f14;
        }
        .stApp {
            background:
                linear-gradient(145deg, rgba(45, 212, 191, .18) 0%, transparent 28%),
                linear-gradient(225deg, rgba(255, 95, 87, .16) 0%, transparent 26%),
                repeating-linear-gradient(90deg, rgba(255,255,255,.025) 0 1px, transparent 1px 84px),
                #0b0f14;
            color: var(--ink);
        }
        [data-testid="stSidebar"] {
            background: #090d12;
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] * { color: #f8fbff !important; }
        .main .block-container { padding-top: 1.25rem; max-width: 1320px; }
        h1, h2, h3, h4, p, label, span, div { letter-spacing: 0 !important; }
        .hero {
            min-height: 238px;
            border: 1px solid rgba(255,255,255,.18);
            border-radius: 8px;
            padding: 30px;
            background:
                linear-gradient(105deg, rgba(11,15,20,.96) 0%, rgba(16,22,29,.88) 50%, rgba(45,212,191,.46) 100%),
                url("https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=1600&q=80");
            background-size: cover;
            background-position: center;
            color: white;
            box-shadow: 0 22px 60px rgba(0,0,0,.32);
            position: relative;
            overflow: hidden;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 28px;
        }
        .hero h1 { font-size: 3.3rem; margin: 0 0 8px; letter-spacing: 0; }
        .hero p { font-size: 1.02rem; max-width: 650px; margin: 0; color: rgba(255,255,255,.82); }
        .hero-kicker {
            color: var(--gold);
            font-size: .78rem;
            font-weight: 900;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .hero-deck {
            width: 250px;
            min-width: 210px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,.18);
            background: rgba(255,255,255,.08);
            padding: 18px;
            backdrop-filter: blur(12px);
        }
        .deck-title { color: var(--muted); font-size: .82rem; font-weight: 800; margin-bottom: 12px; }
        .visualizer {
            height: 92px;
            display: flex;
            align-items: end;
            gap: 8px;
        }
        .visualizer span {
            flex: 1;
            min-width: 10px;
            border-radius: 4px 4px 0 0;
            background: var(--mint);
            box-shadow: 0 0 18px rgba(45,212,191,.34);
        }
        .visualizer span:nth-child(2), .visualizer span:nth-child(6) { background: var(--coral); }
        .visualizer span:nth-child(3), .visualizer span:nth-child(7) { background: var(--gold); }
        .visualizer span:nth-child(1) { height: 36%; }
        .visualizer span:nth-child(2) { height: 78%; }
        .visualizer span:nth-child(3) { height: 54%; }
        .visualizer span:nth-child(4) { height: 92%; }
        .visualizer span:nth-child(5) { height: 46%; }
        .visualizer span:nth-child(6) { height: 70%; }
        .visualizer span:nth-child(7) { height: 58%; }
        .visualizer span:nth-child(8) { height: 84%; }
        .hero, .welcome-stage {
            animation: welcome-rise .7s ease both;
        }
        .hero .visualizer span, .welcome-stage .visualizer span {
            transform-origin: bottom;
            animation: beat-bars 1.45s ease-in-out infinite;
        }
        .hero .visualizer span:nth-child(2), .welcome-stage .visualizer span:nth-child(2) { animation-delay: -.18s; }
        .hero .visualizer span:nth-child(3), .welcome-stage .visualizer span:nth-child(3) { animation-delay: -.34s; }
        .hero .visualizer span:nth-child(4), .welcome-stage .visualizer span:nth-child(4) { animation-delay: -.52s; }
        .hero .visualizer span:nth-child(5), .welcome-stage .visualizer span:nth-child(5) { animation-delay: -.26s; }
        .hero .visualizer span:nth-child(6), .welcome-stage .visualizer span:nth-child(6) { animation-delay: -.44s; }
        .hero .visualizer span:nth-child(7), .welcome-stage .visualizer span:nth-child(7) { animation-delay: -.62s; }
        .hero .visualizer span:nth-child(8), .welcome-stage .visualizer span:nth-child(8) { animation-delay: -.12s; }
        .welcome-stage {
            min-height: 330px;
            border: 1px solid rgba(255,255,255,.18);
            border-radius: 8px;
            padding: 32px;
            background:
                linear-gradient(105deg, rgba(11,15,20,.98) 0%, rgba(16,22,29,.9) 52%, rgba(90,169,230,.38) 100%),
                url("https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&w=1600&q=80");
            background-size: cover;
            background-position: center;
            color: white;
            box-shadow: 0 22px 60px rgba(0,0,0,.34);
            position: relative;
            overflow: hidden;
            display: grid;
            grid-template-columns: minmax(0, 1.15fr) minmax(280px, .85fr);
            align-items: center;
            gap: 28px;
        }
        .welcome-copy {
            position: relative;
            z-index: 1;
        }
        .welcome-kicker {
            color: var(--gold);
            font-size: .78rem;
            font-weight: 900;
            text-transform: uppercase;
            margin-bottom: 10px;
            animation: text-focus .75s ease .1s both;
        }
        .welcome-stage h1 {
            font-size: clamp(2.25rem, 5vw, 4.7rem);
            line-height: .96;
            margin: 0 0 14px;
            max-width: 760px;
            animation: text-focus .8s ease .22s both;
        }
        .welcome-stage p {
            font-size: 1.04rem;
            line-height: 1.65;
            max-width: 660px;
            margin: 0;
            color: rgba(255,255,255,.82);
            animation: text-focus .8s ease .34s both;
        }
        .welcome-moods {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 22px;
            animation: text-focus .8s ease .46s both;
        }
        .mood-chip {
            display: inline-flex;
            align-items: center;
            border: 1px solid rgba(255,255,255,.2);
            border-radius: 999px;
            padding: 7px 12px;
            background: rgba(255,255,255,.09);
            color: white;
            font-size: .82rem;
            font-weight: 800;
            backdrop-filter: blur(10px);
        }
        .welcome-player {
            position: relative;
            z-index: 1;
            min-height: 250px;
            border: 1px solid rgba(255,255,255,.18);
            border-radius: 8px;
            padding: 22px;
            background: rgba(255,255,255,.08);
            backdrop-filter: blur(14px);
            animation: player-float 4.8s ease-in-out infinite;
        }
        .record-wrap {
            width: min(190px, 54vw);
            aspect-ratio: 1;
            margin: 0 auto 20px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background:
                radial-gradient(circle at center, #f8c14a 0 8%, #111820 8% 16%, transparent 16%),
                repeating-radial-gradient(circle at center, rgba(255,255,255,.2) 0 2px, transparent 2px 14px),
                conic-gradient(from 90deg, #2dd4bf, #5aa9e6, #ef6f9f, #ff5f57, #f8c14a, #2dd4bf);
            box-shadow: 0 18px 48px rgba(0,0,0,.34), inset 0 0 0 12px rgba(0,0,0,.45);
            animation: spin-record 7s linear infinite;
        }
        .record-label {
            width: 58px;
            height: 58px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: #f8fbff;
            color: #111820;
            font-weight: 900;
            box-shadow: inset 0 0 0 8px #f8c14a;
        }
        .welcome-trackline {
            color: rgba(255,255,255,.78);
            font-size: .86rem;
            font-weight: 800;
            text-align: center;
            margin-bottom: 14px;
            text-transform: uppercase;
        }
        .metric-card, .song-card, .profile-panel {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 14px 36px rgba(0,0,0,.22);
            color: var(--ink);
            backdrop-filter: blur(14px);
        }
        .profile-head {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 16px;
        }
        .profile-avatar-img,
        .profile-avatar-fallback {
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid rgba(41,240,192,.7);
            box-shadow: 0 16px 34px rgba(0,0,0,.3);
            flex: 0 0 auto;
        }
        .profile-avatar-fallback {
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, var(--mint), var(--gold));
            color: #120d12;
            font-weight: 1000;
            font-size: 1.45rem;
        }
        .profile-head h2 {
            margin: 0;
            color: #fffaf2;
        }
        .profile-head p {
            margin: 4px 0 0;
            color: var(--muted);
            font-weight: 800;
        }
        .metric-card {
            border-left: 4px solid var(--mint);
            min-height: 104px;
        }
        .metric-card .label { color: var(--muted); font-size: .82rem; text-transform: uppercase; font-weight: 800; }
        .metric-card .value { font-size: 2rem; font-weight: 900; color: #ffffff; }
        .song-card {
            margin-top: 16px;
            border-left: 4px solid var(--coral);
        }
        .track-row {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .album-mark {
            width: 58px;
            height: 58px;
            border-radius: 8px;
            display: grid;
            place-items: center;
            color: #111820;
            font-weight: 900;
            background:
                linear-gradient(135deg, var(--mint), var(--gold) 52%, var(--coral));
            box-shadow: inset 0 0 0 1px rgba(255,255,255,.38), 0 12px 28px rgba(0,0,0,.24);
            flex: 0 0 auto;
        }
        .song-card h3 { margin: 0 0 2px; font-size: 1.16rem; color: #ffffff; }
        .song-card .meta { color: var(--muted); font-size: .9rem; margin-bottom: 10px; }
        .pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: 1px solid rgba(255,255,255,.22);
            border-radius: 999px;
            padding: 5px 10px;
            background: rgba(255,255,255,.08);
            color: #ffffff;
            font-size: .8rem;
            font-weight: 700;
        }
        .history-icon {
            width: 46px;
            height: 46px;
            border-radius: 8px;
            display: inline-grid;
            place-items: center;
            background: linear-gradient(135deg, var(--mint), var(--coral));
            box-shadow: 0 12px 26px rgba(244,93,72,.25);
            margin-right: 10px;
            vertical-align: middle;
        }
        .history-icon svg { width: 26px; height: 26px; stroke: white; }
        a { color: var(--mint); }
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input {
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,.16);
            background: rgba(255,255,255,.92);
            color: #111820;
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            border-radius: 8px;
            background: rgba(255,255,255,.92);
            color: #111820;
        }
        div[data-testid="stButton"] > button {
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,.16);
            background: #f8c14a;
            color: #111820;
            min-height: 42px;
            box-shadow: 0 10px 22px rgba(248,193,74,.18);
            font-weight: 900;
        }
        div[data-testid="stButton"] > button:hover {
            border-color: var(--mint);
            background: var(--mint);
            color: #071014;
        }
        div[data-testid="stLinkButton"] > a {
            border-radius: 8px;
            border-color: rgba(255,255,255,.18);
            background: var(--panel-strong);
            color: white;
            font-weight: 700;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            flex-wrap: wrap;
            background: rgba(255,255,255,.05);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            border: 1px solid var(--line);
            background: rgba(255,255,255,.08);
            min-height: 46px;
            padding: 8px 14px;
        }
        .stTabs [data-baseweb="tab"] p {
            color: #f8fbff !important;
            font-weight: 800 !important;
            font-size: .95rem !important;
            margin: 0 !important;
            white-space: nowrap;
        }
        .stTabs [aria-selected="true"] {
            background: #f8c14a;
            border-color: #f8c14a;
            box-shadow: none;
        }
        .stTabs [aria-selected="true"] p {
            color: #111820 !important;
        }
        [data-testid="stDataFrame"], [data-testid="stAlert"] {
            border-radius: 8px;
            overflow: hidden;
        }
        .mobile-install {
            display: none;
            margin: 14px 0 18px;
            border: 1px solid rgba(255,255,255,.16);
            border-left: 4px solid var(--mint);
            border-radius: 8px;
            padding: 14px;
            background: rgba(16,22,29,.82);
            color: var(--ink);
        }
        .mobile-install strong {
            display: block;
            margin-bottom: 4px;
            color: #ffffff;
        }
        .mobile-install span {
            color: var(--muted);
            font-size: .9rem;
        }
        .section-intro {
            border: 1px solid var(--line);
            border-left: 4px solid var(--mint);
            border-radius: 8px;
            padding: 16px 18px;
            margin: 8px 0 18px;
            background: rgba(16,22,29,.78);
            box-shadow: 0 12px 32px rgba(0,0,0,.18);
        }
        .section-intro.online {
            border-left-color: var(--gold);
        }
        .section-intro h2 {
            margin: 0 0 4px;
            color: #ffffff;
            font-size: 1.25rem;
        }
        .section-intro p {
            margin: 0;
            color: var(--muted);
            font-size: .92rem;
            line-height: 1.5;
        }
        .now-playing {
            border: 1px solid rgba(45,212,191,.35);
            border-left: 4px solid var(--mint);
            border-radius: 8px;
            padding: 12px 14px;
            margin: 12px 0;
            background: rgba(45,212,191,.1);
            color: #ffffff;
            font-weight: 800;
        }
        .now-playing span {
            display: block;
            color: var(--muted);
            font-size: .82rem;
            font-weight: 700;
            margin-top: 3px;
        }
        .login-burst {
            position: fixed;
            inset: 0;
            z-index: 9999;
            display: grid;
            place-items: center;
            padding: 24px;
            background:
                radial-gradient(circle at 24% 24%, rgba(45,212,191,.24), transparent 32%),
                radial-gradient(circle at 76% 72%, rgba(248,193,74,.2), transparent 28%),
                rgba(7, 10, 14, .86);
            backdrop-filter: blur(14px);
            pointer-events: none;
            animation: login-overlay-out 5.8s ease forwards;
        }
        .login-card {
            width: min(520px, 92vw);
            border: 1px solid rgba(255,255,255,.18);
            border-radius: 8px;
            padding: 28px;
            background:
                linear-gradient(145deg, rgba(16,22,29,.96), rgba(11,15,20,.9)),
                url("https://images.unsplash.com/photo-1516280440614-37939bbacd81?auto=format&fit=crop&w=1200&q=80");
            background-size: cover;
            background-position: center;
            box-shadow: 0 28px 80px rgba(0,0,0,.42);
            color: white;
            text-align: center;
            overflow: hidden;
            animation: login-card-pop 5.45s ease forwards;
        }
        .login-orbit {
            width: 108px;
            height: 108px;
            margin: 0 auto 18px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background:
                radial-gradient(circle, #f8fbff 0 24%, transparent 25%),
                conic-gradient(from 0deg, var(--mint), var(--gold), var(--coral), var(--sky), var(--mint));
            box-shadow: 0 0 42px rgba(45,212,191,.38);
            animation: login-spin 1.8s linear infinite;
        }
        .login-note {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: #10161d;
            color: var(--gold);
            font-size: 1.65rem;
            font-weight: 900;
            animation: login-note-pulse .72s ease-in-out infinite alternate;
        }
        .login-card h2 {
            margin: 0 0 8px;
            font-size: clamp(1.8rem, 5vw, 3rem);
            line-height: 1.02;
        }
        .login-card p {
            margin: 0 auto 18px;
            max-width: 390px;
            color: rgba(255,255,255,.8);
            line-height: 1.55;
        }
        .login-card .visualizer {
            height: 54px;
            max-width: 290px;
            margin: 0 auto;
        }
        .login-burst .visualizer span {
            transform-origin: bottom;
            animation: beat-bars .82s ease-in-out infinite;
        }
        @keyframes welcome-rise {
            from { opacity: 0; transform: translateY(18px) scale(.985); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes text-focus {
            from { opacity: 0; transform: translateY(14px); filter: blur(8px); }
            to { opacity: 1; transform: translateY(0); filter: blur(0); }
        }
        @keyframes beat-bars {
            0%, 100% { transform: scaleY(.72); filter: brightness(.95); }
            45% { transform: scaleY(1.08); filter: brightness(1.2); }
        }
        @keyframes spin-record {
            to { transform: rotate(360deg); }
        }
        @keyframes player-float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }
        @keyframes login-overlay-out {
            0%, 78% { opacity: 1; }
            100% { opacity: 0; visibility: hidden; }
        }
        @keyframes login-card-pop {
            0% { opacity: 0; transform: translateY(24px) scale(.92); filter: blur(8px); }
            14%, 78% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
            100% { opacity: 0; transform: translateY(-18px) scale(.98); filter: blur(4px); }
        }
        @keyframes login-spin {
            to { transform: rotate(360deg); }
        }
        @keyframes login-note-pulse {
            from { transform: scale(.92); }
            to { transform: scale(1.08); }
        }
        @media (prefers-reduced-motion: reduce) {
            .hero, .welcome-stage, .welcome-kicker, .welcome-stage h1,
            .welcome-stage p, .welcome-moods, .welcome-player,
            .record-wrap, .visualizer span, .login-burst, .login-card,
            .login-orbit, .login-note {
                animation: none !important;
            }
        }
        @media (max-width: 780px) {
            html, body, [data-testid="stAppViewContainer"] {
                overflow-x: hidden;
            }
            .main .block-container {
                padding: .8rem .85rem max(1rem, env(safe-area-inset-bottom));
                max-width: 100%;
            }
            [data-testid="stSidebar"] {
                min-width: min(86vw, 320px) !important;
                max-width: min(86vw, 320px) !important;
            }
            .hero {
                display: block;
                min-height: 0;
                padding: 20px;
                background-position: center;
            }
            .hero h1 {
                font-size: 2.15rem;
                line-height: 1.05;
                margin-bottom: 10px;
            }
            .hero p {
                font-size: .95rem;
                line-height: 1.55;
            }
            .hero-deck { width: auto; margin-top: 20px; }
            .welcome-stage {
                grid-template-columns: 1fr;
                min-height: 0;
                padding: 20px;
                gap: 20px;
            }
            .welcome-stage h1 {
                font-size: 2.35rem;
                line-height: 1.04;
            }
            .welcome-stage p {
                font-size: .95rem;
                line-height: 1.55;
            }
            .welcome-player {
                min-height: 0;
                padding: 18px;
            }
            .record-wrap {
                width: min(150px, 56vw);
                margin-bottom: 16px;
            }
            .section-intro {
                padding: 14px;
                margin-bottom: 14px;
            }
            .section-intro h2 {
                font-size: 1.08rem;
            }
            .login-card {
                padding: 22px;
            }
            .login-orbit {
                width: 92px;
                height: 92px;
            }
            .login-note {
                width: 42px;
                height: 42px;
                font-size: 1.35rem;
            }
            .visualizer { height: 64px; gap: 6px; }
            .metric-card, .song-card, .profile-panel {
                padding: 14px;
                box-shadow: 0 10px 26px rgba(0,0,0,.22);
            }
            .metric-card {
                min-height: 88px;
            }
            .metric-card .value {
                font-size: 1.55rem;
                overflow-wrap: anywhere;
            }
            .track-row {
                align-items: flex-start;
                gap: 12px;
            }
            .album-mark { width: 48px; height: 48px; }
            .song-card h3 {
                font-size: 1rem;
                line-height: 1.25;
                overflow-wrap: anywhere;
            }
            .song-card .meta {
                font-size: .82rem;
                line-height: 1.45;
            }
            .pill {
                margin-top: 6px;
                max-width: 100%;
                overflow-wrap: anywhere;
            }
            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }
            div[data-testid="stButton"] > button,
            div[data-testid="stFormSubmitButton"] > button,
            div[data-testid="stLinkButton"] > a {
                width: 100%;
                min-height: 48px;
            }
            .stTabs [data-baseweb="tab-list"] {
                flex-wrap: nowrap;
                overflow-x: auto;
                scrollbar-width: none;
                justify-content: flex-start;
            }
            .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
                display: none;
            }
            .stTabs [data-baseweb="tab"] {
                flex: 0 0 auto;
                min-height: 44px;
                padding: 7px 12px;
            }
            .stTabs [data-baseweb="tab"] p {
                font-size: .88rem !important;
            }
            [data-testid="stDataFrame"] {
                max-width: 100%;
                overflow-x: auto;
            }
            iframe, video, audio {
                max-width: 100% !important;
            }
            .mobile-install {
                display: block;
            }
        }
        @media (max-width: 420px) {
            .hero {
                padding: 18px;
            }
            .hero h1 {
                font-size: 1.9rem;
            }
            .welcome-stage h1 {
                font-size: 2rem;
            }
            .mood-chip {
                font-size: .76rem;
                padding: 6px 10px;
            }
            .hero-kicker {
                font-size: .72rem;
            }
            .history-icon {
                width: 38px;
                height: 38px;
            }
        }

        /* EcoWavE studio refresh */
        :root {
            --ink: #f9fbf7;
            --panel: rgba(12, 14, 18, .86);
            --panel-strong: #101114;
            --muted: #b9c3bd;
            --line: rgba(255, 255, 255, .16);
            --mint: #26e0b8;
            --coral: #ff5f57;
            --gold: #ffd166;
            --sky: #72d6ff;
            --rose: #f071a8;
            --paper: #07080b;
        }
        .stApp {
            background:
                linear-gradient(115deg, rgba(38,224,184,.18), transparent 34%),
                linear-gradient(245deg, rgba(255,95,87,.14), transparent 30%),
                repeating-linear-gradient(0deg, rgba(255,255,255,.035) 0 1px, transparent 1px 42px),
                repeating-linear-gradient(90deg, rgba(255,255,255,.025) 0 1px, transparent 1px 78px),
                #07080b;
            color: var(--ink);
        }
        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(255,209,102,.08), transparent 22%),
                #08090c;
            border-right: 1px solid rgba(255,255,255,.18);
            box-shadow: 16px 0 48px rgba(0,0,0,.28);
        }
        [data-testid="stSidebar"] h1 {
            color: var(--gold) !important;
        }
        .main .block-container {
            max-width: 1240px;
            padding-top: 1rem;
        }
        .hero {
            min-height: 286px;
            border: 1px solid rgba(255,255,255,.22);
            background:
                linear-gradient(105deg, rgba(7,8,11,.97) 0%, rgba(12,14,18,.9) 42%, rgba(38,224,184,.18) 69%, rgba(255,209,102,.24) 100%),
                url("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1800&q=80");
            background-size: cover;
            background-position: center;
            box-shadow: 0 30px 80px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.2);
        }
        .hero::after {
            content: "";
            position: absolute;
            right: -42px;
            bottom: -74px;
            width: 235px;
            height: 235px;
            border-radius: 50%;
            background:
                radial-gradient(circle at center, #f8fbff 0 8%, #101114 9% 16%, transparent 17%),
                repeating-radial-gradient(circle at center, rgba(255,255,255,.18) 0 2px, transparent 2px 16px),
                conic-gradient(from 40deg, var(--mint), var(--gold), var(--coral), var(--sky), var(--mint));
            opacity: .78;
            box-shadow: 0 20px 54px rgba(0,0,0,.38);
            animation: spin-record 16s linear infinite;
        }
        .hero > div {
            position: relative;
            z-index: 1;
        }
        .hero h1 {
            font-size: clamp(2.6rem, 6vw, 5.1rem);
            line-height: .95;
            text-shadow: 0 14px 38px rgba(0,0,0,.45);
        }
        .hero-kicker {
            display: inline-flex;
            padding: 7px 11px;
            border: 1px solid rgba(255,209,102,.38);
            border-radius: 999px;
            background: rgba(255,209,102,.12);
            color: var(--gold);
        }
        .hero-deck {
            border-color: rgba(255,255,255,.22);
            background: rgba(8, 9, 12, .55);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.18), 0 20px 44px rgba(0,0,0,.26);
        }
        .metric-card, .song-card, .profile-panel {
            background:
                linear-gradient(145deg, rgba(255,255,255,.08), rgba(255,255,255,.025)),
                rgba(12,14,18,.86);
            border-color: rgba(255,255,255,.18);
            box-shadow: 0 18px 48px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.12);
        }
        .metric-card {
            border-left: 0;
            position: relative;
            overflow: hidden;
        }
        .metric-card::before {
            content: "";
            position: absolute;
            inset: 0 0 auto;
            height: 4px;
            background: linear-gradient(90deg, var(--mint), var(--gold), var(--coral));
        }
        .metric-card .value {
            color: var(--gold);
        }
        .song-card {
            border-left: 0;
            transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
        }
        .song-card:hover {
            transform: translateY(-2px);
            border-color: rgba(38,224,184,.42);
            box-shadow: 0 24px 58px rgba(0,0,0,.32), 0 0 0 1px rgba(38,224,184,.16);
        }
        .album-mark {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            color: #07080b;
            background:
                radial-gradient(circle at center, #f8fbff 0 18%, transparent 19%),
                conic-gradient(from 120deg, var(--gold), var(--mint), var(--sky), var(--coral), var(--gold));
            box-shadow: 0 14px 34px rgba(0,0,0,.34), inset 0 0 0 8px rgba(7,8,11,.28);
        }
        .pill {
            border-color: rgba(255,209,102,.36);
            background: rgba(255,209,102,.12);
            color: #fff8dc;
        }
        .section-intro {
            background:
                linear-gradient(135deg, rgba(38,224,184,.12), rgba(255,255,255,.035)),
                rgba(12,14,18,.78);
            border-left-color: var(--mint);
        }
        .section-intro.online {
            background:
                linear-gradient(135deg, rgba(255,209,102,.13), rgba(255,95,87,.08)),
                rgba(12,14,18,.78);
        }
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(255,255,255,.055);
            border-color: rgba(255,255,255,.16);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.1);
        }
        .stTabs [data-baseweb="tab"] {
            background: rgba(255,255,255,.065);
            border-color: rgba(255,255,255,.14);
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--gold), var(--mint));
            border-color: transparent;
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, var(--gold), #ffb347);
            color: #0b0f14;
            border: 0;
            box-shadow: 0 12px 26px rgba(255,209,102,.22);
            transition: transform .16s ease, box-shadow .16s ease, filter .16s ease;
        }
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-1px);
            filter: brightness(1.04);
            box-shadow: 0 16px 34px rgba(38,224,184,.22);
        }
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            border: 1px solid rgba(38,224,184,.28);
            box-shadow: 0 10px 26px rgba(0,0,0,.16);
        }
        .welcome-stage {
            background:
                linear-gradient(105deg, rgba(7,8,11,.98) 0%, rgba(12,14,18,.9) 48%, rgba(255,95,87,.22) 100%),
                url("https://images.unsplash.com/photo-1516280440614-37939bbacd81?auto=format&fit=crop&w=1800&q=80");
            background-size: cover;
            background-position: center;
            box-shadow: 0 30px 80px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.18);
        }
        .welcome-player, .login-card {
            background:
                linear-gradient(145deg, rgba(255,255,255,.1), rgba(255,255,255,.025)),
                rgba(7,8,11,.7);
        }
        .now-playing {
            background:
                linear-gradient(90deg, rgba(38,224,184,.16), rgba(255,209,102,.1)),
                rgba(12,14,18,.72);
            border-color: rgba(38,224,184,.42);
        }
        div[data-testid="stDialog"] > div {
            background:
                linear-gradient(145deg, rgba(18,20,25,.96), rgba(7,8,11,.94)) !important;
            border: 1px solid rgba(255,255,255,.18) !important;
            box-shadow: 0 34px 90px rgba(0,0,0,.55) !important;
            color: var(--ink) !important;
        }
        .startup-popup {
            position: relative;
            overflow: hidden;
            padding: 6px 0 0;
            font-family: "Trebuchet MS", "Segoe UI", Arial, sans-serif;
        }
        .startup-popup::after {
            content: "EW";
            position: absolute;
            right: -18px;
            top: -24px;
            width: 116px;
            height: 116px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background:
                radial-gradient(circle at center, #f8fbff 0 12%, transparent 13%),
                conic-gradient(from 120deg, var(--gold), var(--mint), var(--sky), var(--coral), var(--gold));
            color: #07080b;
            font-weight: 900;
            opacity: .65;
            box-shadow: 0 18px 48px rgba(0,0,0,.32);
            animation: spin-record 14s linear infinite;
        }
        .startup-kicker {
            display: inline-flex;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid rgba(255,209,102,.34);
            background: rgba(255,209,102,.12);
            color: var(--gold);
            font-size: .78rem;
            font-weight: 900;
            text-transform: uppercase;
            margin-bottom: 12px;
        }
        .startup-popup h2 {
            position: relative;
            z-index: 1;
            margin: 0 0 8px;
            color: #ffffff;
            font-size: clamp(1.8rem, 5vw, 3.15rem);
            line-height: 1;
        }
        .startup-popup p {
            position: relative;
            z-index: 1;
            color: var(--muted);
            line-height: 1.55;
            margin: 0 0 16px;
        }
        .startup-grid {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin: 16px 0 18px;
        }
        .startup-feature {
            border: 1px solid rgba(255,255,255,.14);
            border-radius: 8px;
            padding: 14px 12px;
            background: rgba(255,255,255,.06);
            color: #ffffff;
            font-size: .98rem;
            font-weight: 900;
            min-height: 118px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }
        .feature-icon {
            width: 42px;
            height: 42px;
            display: grid !important;
            place-items: center;
            border-radius: 8px;
            margin: 0 0 10px !important;
            background: linear-gradient(135deg, rgba(45,212,191,.95), rgba(248,193,74,.95));
            color: #101216 !important;
            font-size: 1.35rem !important;
            font-weight: 1000 !important;
            line-height: 1 !important;
        }
        .startup-feature span {
            display: block;
            margin-top: 4px;
            color: var(--muted);
            font-size: .78rem;
            font-weight: 700;
            line-height: 1.35;
        }
        .startup-link {
            position: relative;
            z-index: 1;
            border: 1px solid rgba(38,224,184,.28);
            border-radius: 8px;
            padding: 10px 12px;
            background: rgba(38,224,184,.09);
            color: var(--mint);
            font-weight: 900;
            overflow-wrap: anywhere;
        }
        @media (max-width: 780px) {
            .hero::after {
                width: 150px;
                height: 150px;
                right: -44px;
                bottom: -50px;
            }
            .album-mark {
                width: 52px;
                height: 52px;
            }
            .startup-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Premium jukebox refresh */
        :root {
            --ink: #fffaf2;
            --panel: rgba(20, 16, 22, .88);
            --panel-strong: #171018;
            --muted: #d6c8bd;
            --line: rgba(255, 250, 242, .18);
            --mint: #29f0c0;
            --coral: #ff4d6d;
            --gold: #ffd166;
            --sky: #64c7ff;
            --rose: #ff85b3;
            --paper: #09070b;
        }
        .stApp {
            background:
                linear-gradient(120deg, rgba(255,77,109,.2), transparent 30%),
                linear-gradient(250deg, rgba(41,240,192,.16), transparent 32%),
                linear-gradient(180deg, rgba(255,209,102,.08), transparent 45%),
                repeating-linear-gradient(90deg, rgba(255,250,242,.035) 0 1px, transparent 1px 92px),
                #09070b;
        }
        .main .block-container {
            max-width: 1180px;
            padding-top: .75rem;
        }
        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(255,77,109,.18), rgba(9,7,11,.94) 32%),
                #09070b;
            border-right: 1px solid rgba(255,209,102,.2);
        }
        [data-testid="stSidebar"] h1 {
            color: #ffffff !important;
            text-shadow: 0 0 22px rgba(255,77,109,.38);
        }
        .welcome-stage, .hero {
            border: 1px solid rgba(255,255,255,.22);
            background:
                linear-gradient(95deg, rgba(9,7,11,.98), rgba(23,16,24,.86) 46%, rgba(255,77,109,.26)),
                url("https://images.unsplash.com/photo-1540039155733-5bb30b53aa14?auto=format&fit=crop&w=1800&q=80");
            background-size: cover;
            background-position: center;
            box-shadow: 0 28px 78px rgba(0,0,0,.48), inset 0 1px 0 rgba(255,255,255,.18);
        }
        .welcome-stage h1, .hero h1 {
            color: #fffaf2;
            text-shadow: 0 10px 34px rgba(0,0,0,.5), 0 0 28px rgba(255,77,109,.24);
        }
        .welcome-kicker, .hero-kicker, .startup-kicker {
            background: linear-gradient(135deg, rgba(255,209,102,.18), rgba(255,77,109,.12));
            border-color: rgba(255,209,102,.44);
            color: var(--gold);
        }
        .welcome-player, .hero-deck, .login-card, .startup-feature {
            background:
                linear-gradient(145deg, rgba(255,250,242,.12), rgba(255,250,242,.035)),
                rgba(15, 10, 17, .72);
            border-color: rgba(255,250,242,.2);
        }
        .record-wrap, .login-orbit {
            background:
                radial-gradient(circle at center, #fffaf2 0 8%, #171018 9% 17%, transparent 18%),
                repeating-radial-gradient(circle at center, rgba(255,250,242,.2) 0 2px, transparent 2px 15px),
                conic-gradient(from 20deg, var(--coral), var(--gold), var(--mint), var(--sky), var(--rose), var(--coral));
        }
        .visualizer span {
            background: linear-gradient(180deg, var(--gold), var(--coral));
            box-shadow: 0 0 20px rgba(255,77,109,.36);
        }
        .visualizer span:nth-child(2), .visualizer span:nth-child(6) {
            background: linear-gradient(180deg, var(--mint), var(--sky));
        }
        .visualizer span:nth-child(3), .visualizer span:nth-child(7) {
            background: linear-gradient(180deg, var(--gold), #ff9f1c);
        }
        .metric-card {
            background:
                linear-gradient(145deg, rgba(255,209,102,.14), rgba(255,77,109,.07)),
                rgba(20,16,22,.9);
        }
        .metric-card::before {
            height: 5px;
            background: linear-gradient(90deg, var(--coral), var(--gold), var(--mint), var(--sky));
        }
        .metric-card .label {
            color: #eadfd4;
        }
        .metric-card .value {
            color: #ffffff;
            text-shadow: 0 0 22px rgba(255,209,102,.26);
        }
        .song-card {
            background:
                linear-gradient(110deg, rgba(255,250,242,.11), rgba(255,250,242,.035) 55%, rgba(41,240,192,.08)),
                rgba(20,16,22,.9);
            border: 1px solid rgba(255,250,242,.17);
        }
        .song-card:hover {
            border-color: rgba(255,209,102,.46);
            box-shadow: 0 26px 62px rgba(0,0,0,.38), 0 0 0 1px rgba(255,209,102,.18);
        }
        .album-mark {
            background:
                radial-gradient(circle at center, #fffaf2 0 16%, transparent 17%),
                conic-gradient(from 90deg, var(--coral), var(--gold), var(--mint), var(--sky), var(--rose), var(--coral));
        }
        .song-card h3 {
            color: #fffaf2;
        }
        .song-card .meta {
            color: #d7c7bd;
        }
        .pill {
            background: rgba(41,240,192,.12);
            border-color: rgba(41,240,192,.34);
            color: #dffef5;
        }
        .section-intro {
            background:
                linear-gradient(110deg, rgba(255,77,109,.13), rgba(41,240,192,.08)),
                rgba(20,16,22,.84);
            border-left-color: var(--coral);
        }
        .section-intro.online {
            border-left-color: var(--gold);
        }
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(20,16,22,.82);
            border-color: rgba(255,250,242,.18);
        }
        .stTabs [data-baseweb="tab"] {
            background: rgba(255,250,242,.07);
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--coral), var(--gold));
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, var(--mint), var(--gold));
            color: #120d12;
            box-shadow: 0 14px 30px rgba(41,240,192,.18);
        }
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            box-shadow: 0 16px 36px rgba(255,77,109,.24);
        }
        .startup-popup h2 {
            color: #fffaf2;
        }
        div[data-testid="stDialog"] > div {
            background:
                linear-gradient(145deg, rgba(23,16,24,.98), rgba(9,7,11,.96)) !important;
        }
        .startup-page {
            min-height: calc(100vh - 130px);
            display: grid;
            place-items: center;
            padding: 24px 12px 56px;
        }
        .startup-card {
            width: min(680px, 100%);
            border: 1px solid rgba(255,250,242,.14);
            background:
                radial-gradient(circle at 88% 12%, rgba(45,212,191,.22), transparent 28%),
                linear-gradient(145deg, rgba(16,20,27,.98), rgba(8,10,14,.98));
            box-shadow: 0 34px 90px rgba(0,0,0,.42);
            border-radius: 8px;
            padding: 30px;
            margin: 0 auto;
        }
        .playlist-player {
            border: 1px solid rgba(255,250,242,.18);
            border-radius: 8px;
            padding: 16px;
            background:
                linear-gradient(110deg, rgba(41,240,192,.14), rgba(255,77,109,.08)),
                rgba(20,16,22,.9);
            color: #fffaf2;
            font-family: Arial, sans-serif;
        }
        .playlist-player-title {
            color: #ffd166;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .playlist-player button {
            border: 0;
            border-radius: 8px;
            padding: 9px 14px;
            background: linear-gradient(135deg, #29f0c0, #ffd166);
            color: #120d12;
            font-weight: 800;
            cursor: pointer;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
            font-size: .92rem;
            font-weight: 950;
        }
        .song-card {
            position: relative;
            overflow: hidden;
            margin-top: 12px;
            padding: 16px 18px;
            border-radius: 8px;
            border: 1px solid rgba(255, 250, 242, .18);
            background:
                linear-gradient(120deg, rgba(41, 240, 192, .12), transparent 34%),
                linear-gradient(145deg, rgba(255, 255, 255, .09), rgba(255, 255, 255, .025)),
                rgba(13, 15, 20, .92);
            box-shadow: 0 18px 42px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.08);
        }
        .song-card::after {
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            background: linear-gradient(90deg, rgba(255,209,102,.18), transparent 22%);
            opacity: .55;
        }
        .song-card:hover {
            transform: translateY(-1px);
            border-color: rgba(41,240,192,.5);
            box-shadow: 0 22px 54px rgba(0,0,0,.42), 0 0 0 1px rgba(41,240,192,.18);
        }
        .track-row {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 74px minmax(0, 1fr);
            align-items: center;
            gap: 18px;
        }
        .album-mark {
            width: 74px;
            height: 74px;
            border-radius: 8px;
            display: grid;
            place-items: center;
            color: #0d0f14;
            font-size: 1rem;
            font-weight: 1000;
            background:
                radial-gradient(circle at center, #fffaf2 0 18%, transparent 19%),
                repeating-radial-gradient(circle at center, rgba(255,255,255,.28) 0 2px, transparent 2px 12px),
                conic-gradient(from 35deg, var(--mint), var(--gold), var(--coral), var(--sky), var(--mint));
            box-shadow: 0 14px 30px rgba(0,0,0,.34), inset 0 0 0 7px rgba(10,12,18,.18);
        }
        .song-card h3 {
            margin: 0 0 8px;
            color: #fffaf2;
            font-size: 1.22rem;
            line-height: 1.12;
            font-weight: 1000;
        }
        .song-card .meta {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            color: #d9cec8;
            font-size: .92rem;
            font-weight: 750;
            line-height: 1.35;
        }
        .pill {
            border: 1px solid rgba(41,240,192,.48);
            border-radius: 999px;
            padding: 6px 12px;
            background: rgba(41,240,192,.16);
            color: #e8fff9;
            font-size: .78rem;
            font-weight: 1000;
        }
        .stApp {
            background:
                radial-gradient(circle at 8% 8%, rgba(41,240,192,.16), transparent 30%),
                radial-gradient(circle at 92% 18%, rgba(255,209,102,.14), transparent 28%),
                linear-gradient(135deg, #0b070d 0%, #10151a 48%, #070b0f 100%) !important;
        }
        .main .block-container {
            max-width: 1280px;
        }
        .section-intro,
        .profile-panel,
        .playlist-player,
        .metric-card {
            border-radius: 8px !important;
            border: 1px solid rgba(255,255,255,.14) !important;
            background:
                linear-gradient(135deg, rgba(255,255,255,.09), rgba(255,255,255,.03)),
                rgba(12, 14, 18, .88) !important;
            box-shadow: 0 18px 44px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.08) !important;
        }
        .section-intro {
            border-left: 5px solid var(--mint) !important;
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stDownloadButton"] > button {
            border-radius: 8px !important;
            min-height: 46px !important;
            border: 1px solid rgba(255,255,255,.16) !important;
            background:
                linear-gradient(135deg, rgba(41,240,192,.95), rgba(255,209,102,.96)) !important;
            color: #100d12 !important;
            font-weight: 950 !important;
            box-shadow: 0 12px 28px rgba(41,240,192,.16) !important;
        }
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 18px 38px rgba(255,209,102,.22) !important;
            filter: brightness(1.04);
        }
        div[data-testid="stButton"] > button:disabled {
            opacity: .45 !important;
            background: rgba(255,255,255,.08) !important;
            color: rgba(255,255,255,.62) !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
            background:
                linear-gradient(135deg, rgba(255,255,255,.09), rgba(255,255,255,.035)),
                rgba(15, 18, 24, .92) !important;
            color: #fffaf2 !important;
            border-color: rgba(255,255,255,.16) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 10px 26px rgba(0,0,0,.22) !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button:hover {
            border-color: rgba(41,240,192,.6) !important;
            background:
                linear-gradient(135deg, rgba(41,240,192,.2), rgba(255,209,102,.12)),
                rgba(18, 21, 27, .94) !important;
        }
        .song-card {
            border-radius: 8px !important;
            border: 1px solid rgba(255,255,255,.16) !important;
            background:
                linear-gradient(120deg, rgba(41,240,192,.13), transparent 30%),
                linear-gradient(145deg, rgba(255,255,255,.1), rgba(255,255,255,.035)),
                rgba(13, 15, 20, .94) !important;
            box-shadow: 0 18px 44px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.08) !important;
        }
        .album-mark {
            border-radius: 8px !important;
            box-shadow: 0 14px 30px rgba(0,0,0,.34), inset 0 0 0 7px rgba(10,12,18,.18) !important;
            overflow: hidden !important;
            background:
                linear-gradient(145deg, rgba(255,255,255,.12), rgba(255,255,255,.04)),
                rgba(8,10,14,.9) !important;
        }
        .album-art {
            width: 100%;
            height: 100%;
            display: grid;
            place-items: center;
            border-radius: 8px;
        }
        .creative-cover {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 28% 22%, rgba(255,255,255,.78), transparent 0 10%, transparent 32%),
                radial-gradient(circle at 72% 78%, rgba(255,255,255,.18), transparent 0 18%, transparent 42%),
                linear-gradient(135deg, var(--cover-a), var(--cover-b) 52%, var(--cover-c));
            box-shadow: inset 0 0 0 1px rgba(255,255,255,.34);
        }
        .creative-cover::before {
            content: "";
            position: absolute;
            inset: -18%;
            background:
                repeating-radial-gradient(circle at center, rgba(255,255,255,.28) 0 2px, transparent 2px 12px);
            opacity: .72;
        }
        .cover-ring {
            position: absolute;
            width: 48%;
            height: 48%;
            border-radius: 50%;
            background: rgba(8,10,14,.88);
            box-shadow: 0 0 0 6px rgba(255,255,255,.72), 0 0 0 12px rgba(8,10,14,.16);
        }
        .cover-initials {
            position: relative;
            z-index: 1;
            color: #fffaf2;
            font-size: .9rem;
            font-weight: 1000;
            text-shadow: 0 2px 10px rgba(0,0,0,.5);
        }
        .cover-tag {
            position: absolute;
            right: 6px;
            bottom: 6px;
            z-index: 1;
            border-radius: 999px;
            padding: 2px 6px;
            background: rgba(8,10,14,.78);
            color: #fffaf2;
            font-size: .62rem;
            font-weight: 1000;
        }
        .song-card h3 {
            font-family: "Trebuchet MS", "Segoe UI", Arial, sans-serif;
            letter-spacing: 0 !important;
        }
        .song-card .meta span:not(.pill) {
            border: 1px solid rgba(255,255,255,.1);
            border-radius: 999px;
            padding: 5px 10px;
            background: rgba(255,255,255,.055);
        }
        .pill {
            background: rgba(41,240,192,.18) !important;
            border-color: rgba(41,240,192,.52) !important;
            color: #eafff9 !important;
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input {
            border-radius: 8px !important;
            border: 1px solid rgba(41,240,192,.28) !important;
            background: rgba(255,255,255,.94) !important;
        }

        /* Final 2026 Neon Studio UI refresh */
        :root {
            --studio-bg: #07080d;
            --studio-card: rgba(17, 20, 28, .88);
            --studio-card-2: rgba(27, 30, 40, .82);
            --studio-line: rgba(255,255,255,.14);
            --studio-text: #fffaf3;
            --studio-soft: #c6c1bc;
            --studio-green: #32f5c8;
            --studio-yellow: #ffe169;
            --studio-red: #ff5d7a;
            --studio-blue: #63b3ff;
        }
        .stApp {
            background:
                linear-gradient(120deg, rgba(255,93,122,.18), transparent 23%),
                linear-gradient(240deg, rgba(50,245,200,.18), transparent 26%),
                linear-gradient(180deg, rgba(255,225,105,.07), transparent 45%),
                repeating-linear-gradient(90deg, rgba(255,255,255,.035) 0 1px, transparent 1px 118px),
                repeating-linear-gradient(0deg, rgba(255,255,255,.025) 0 1px, transparent 1px 118px),
                var(--studio-bg) !important;
            color: var(--studio-text) !important;
        }
        .main .block-container {
            max-width: 1380px !important;
            padding-top: 1.05rem !important;
            padding-bottom: 4rem !important;
        }
        h1, h2, h3, h4, h5, h6,
        .section-intro h2,
        .song-card h3 {
            font-family: "Segoe UI Black", "Arial Black", "Segoe UI", Arial, sans-serif !important;
            letter-spacing: 0 !important;
        }
        p, label, span, div, button, input, textarea {
            font-family: "Segoe UI", "Trebuchet MS", Arial, sans-serif !important;
            letter-spacing: 0 !important;
        }
        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(255,93,122,.14), transparent 35%),
                rgba(8, 10, 15, .98) !important;
            border-right: 1px solid rgba(255,255,255,.12) !important;
        }
        .hero,
        .welcome-stage {
            border: 1px solid rgba(255,255,255,.16) !important;
            border-radius: 8px !important;
            background:
                linear-gradient(110deg, rgba(7,8,13,.98) 0%, rgba(15,18,25,.9) 48%, rgba(50,245,200,.22) 100%),
                radial-gradient(circle at 83% 16%, rgba(255,225,105,.25), transparent 0 20%, transparent 42%),
                url("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1800&q=80") !important;
            background-size: cover !important;
            background-position: center !important;
            box-shadow: 0 24px 70px rgba(0,0,0,.48), inset 0 1px 0 rgba(255,255,255,.08) !important;
        }
        .welcome-stage h1,
        .hero h1 {
            color: #fffdf6 !important;
            text-shadow: 0 10px 34px rgba(0,0,0,.42);
        }
        .welcome-kicker,
        .hero-kicker {
            color: var(--studio-yellow) !important;
            background: rgba(255,225,105,.1);
            border: 1px solid rgba(255,225,105,.28);
            border-radius: 999px;
            width: fit-content;
            padding: 7px 12px;
        }
        .section-intro {
            position: relative;
            overflow: hidden;
            padding: 24px !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255,255,255,.14) !important;
            border-left: 0 !important;
            background:
                linear-gradient(135deg, rgba(50,245,200,.16), transparent 30%),
                linear-gradient(270deg, rgba(255,93,122,.14), transparent 38%),
                rgba(14, 17, 25, .88) !important;
            box-shadow: 0 18px 52px rgba(0,0,0,.36), inset 0 1px 0 rgba(255,255,255,.08) !important;
        }
        .section-intro::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 6px;
            background: linear-gradient(180deg, var(--studio-green), var(--studio-yellow), var(--studio-red));
        }
        .section-intro h2 {
            margin: 0 0 8px !important;
            color: var(--studio-text) !important;
            font-size: clamp(1.75rem, 3.2vw, 3rem) !important;
        }
        .section-intro p {
            color: var(--studio-soft) !important;
            font-size: 1rem !important;
        }
        .metric-card,
        .profile-panel,
        .playlist-player,
        [data-testid="stAlert"],
        [data-testid="stDataFrame"] {
            border-radius: 8px !important;
            border: 1px solid rgba(255,255,255,.13) !important;
            background:
                linear-gradient(145deg, rgba(255,255,255,.08), rgba(255,255,255,.025)),
                rgba(13, 16, 23, .9) !important;
            box-shadow: 0 18px 46px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.08) !important;
        }
        .metric-card {
            min-height: 118px;
            display: grid;
            align-content: center;
        }
        .metric-card .label {
            color: var(--studio-soft) !important;
            font-size: .78rem !important;
        }
        .metric-card .value {
            color: var(--studio-text) !important;
            font-size: clamp(1.45rem, 2.4vw, 2.35rem) !important;
        }
        .song-card {
            position: relative;
            overflow: hidden;
            border-radius: 8px !important;
            border: 1px solid rgba(255,255,255,.15) !important;
            background:
                linear-gradient(100deg, rgba(50,245,200,.13), transparent 32%),
                linear-gradient(260deg, rgba(255,93,122,.12), transparent 42%),
                rgba(15, 18, 26, .93) !important;
            box-shadow: 0 22px 54px rgba(0,0,0,.38), inset 0 1px 0 rgba(255,255,255,.08) !important;
            transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease !important;
        }
        .song-card::before {
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            background: linear-gradient(90deg, rgba(255,255,255,.06), transparent 18%, transparent 82%, rgba(255,255,255,.04));
        }
        .song-card:hover {
            transform: translateY(-2px);
            border-color: rgba(50,245,200,.46) !important;
            box-shadow: 0 28px 70px rgba(0,0,0,.48), 0 0 0 1px rgba(50,245,200,.18) !important;
        }
        .song-card h3 {
            color: #fffdf7 !important;
            font-size: clamp(1.1rem, 2vw, 1.55rem) !important;
            line-height: 1.15 !important;
        }
        .song-card .meta {
            color: var(--studio-soft) !important;
            line-height: 1.8 !important;
        }
        .song-card .meta span:not(.pill) {
            display: inline-flex;
            align-items: center;
            min-height: 30px;
            border: 1px solid rgba(255,255,255,.12) !important;
            border-radius: 999px !important;
            padding: 4px 11px !important;
            background: rgba(255,255,255,.065) !important;
            margin-right: 5px;
            margin-bottom: 5px;
        }
        .pill {
            display: inline-flex !important;
            align-items: center !important;
            min-height: 30px !important;
            border-radius: 999px !important;
            padding: 4px 12px !important;
            background: rgba(50,245,200,.16) !important;
            border: 1px solid rgba(50,245,200,.48) !important;
            color: #dffff7 !important;
            font-weight: 900 !important;
        }
        .album-mark {
            width: 92px !important;
            height: 92px !important;
            min-width: 92px !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255,255,255,.22) !important;
            box-shadow: 0 18px 42px rgba(0,0,0,.42), inset 0 0 0 8px rgba(7,8,13,.16) !important;
        }
        .creative-cover {
            border-radius: 8px !important;
            background:
                radial-gradient(circle at 25% 18%, rgba(255,255,255,.95), transparent 0 9%, transparent 33%),
                radial-gradient(circle at 76% 82%, rgba(255,255,255,.2), transparent 0 18%, transparent 44%),
                conic-gradient(from 130deg, var(--cover-a), var(--cover-b), var(--cover-c), var(--cover-a)) !important;
        }
        .cover-ring {
            width: 52% !important;
            height: 52% !important;
            background: rgba(7,8,13,.88) !important;
            box-shadow: 0 0 0 7px rgba(255,255,255,.82), 0 0 0 14px rgba(7,8,13,.14) !important;
        }
        .cover-initials {
            font-size: 1rem !important;
            color: white !important;
        }
        .cover-tag {
            right: 7px !important;
            bottom: 7px !important;
            background: rgba(7,8,13,.84) !important;
            border: 1px solid rgba(255,255,255,.18);
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stDownloadButton"] > button,
        div[data-testid="stLinkButton"] > a {
            border-radius: 8px !important;
            min-height: 48px !important;
            border: 1px solid rgba(255,255,255,.16) !important;
            background: linear-gradient(135deg, var(--studio-green), var(--studio-yellow)) !important;
            color: #0a0b10 !important;
            font-weight: 950 !important;
            box-shadow: 0 16px 36px rgba(50,245,200,.16) !important;
            transition: transform .16s ease, filter .16s ease, box-shadow .16s ease !important;
        }
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover,
        div[data-testid="stLinkButton"] > a:hover {
            transform: translateY(-2px);
            filter: saturate(1.08) brightness(1.04);
            box-shadow: 0 22px 48px rgba(255,225,105,.2) !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
            background:
                linear-gradient(145deg, rgba(255,255,255,.09), rgba(255,255,255,.03)),
                rgba(14,17,25,.9) !important;
            color: var(--studio-text) !important;
            border-color: rgba(255,255,255,.14) !important;
            box-shadow: 0 14px 34px rgba(0,0,0,.26) !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button:hover {
            background:
                linear-gradient(145deg, rgba(50,245,200,.18), rgba(255,225,105,.1)),
                rgba(14,17,25,.96) !important;
            border-color: rgba(50,245,200,.45) !important;
        }
        div[data-testid="stButton"] > button:disabled,
        div[data-testid="stFormSubmitButton"] > button:disabled {
            background: rgba(255,255,255,.08) !important;
            color: rgba(255,255,255,.48) !important;
            border-color: rgba(255,255,255,.08) !important;
            transform: none !important;
            box-shadow: none !important;
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input {
            min-height: 46px !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255,255,255,.14) !important;
            background: rgba(255,255,255,.96) !important;
            color: #11131a !important;
            box-shadow: 0 10px 26px rgba(0,0,0,.14) !important;
        }
        div[data-testid="stFileUploader"] section {
            border-radius: 8px !important;
            border: 1px dashed rgba(50,245,200,.4) !important;
            background: rgba(255,255,255,.055) !important;
        }
        .stAudio {
            border-radius: 8px !important;
            overflow: hidden !important;
            border: 1px solid rgba(255,255,255,.12) !important;
            box-shadow: 0 14px 34px rgba(0,0,0,.26) !important;
        }
        @media (max-width: 760px) {
            .main .block-container {
                padding-left: .8rem !important;
                padding-right: .8rem !important;
            }
            .welcome-stage {
                grid-template-columns: 1fr !important;
                padding: 22px !important;
            }
            .hero {
                display: block !important;
                padding: 22px !important;
            }
            .album-mark {
                width: 76px !important;
                height: 76px !important;
                min-width: 76px !important;
            }
            .song-card {
                padding: 14px !important;
            }
            .section-intro h2 {
                font-size: 1.8rem !important;
            }
        }

        /* Final creative pass: premium music-room interface */
        .stApp::before,
        .stApp::after {
            content: "";
            position: fixed;
            pointer-events: none;
            z-index: 0;
            filter: blur(2px);
        }
        .stApp::before {
            inset: 0;
            background:
                radial-gradient(circle at 12% 18%, rgba(255, 68, 116, .24), transparent 0 23%),
                radial-gradient(circle at 88% 12%, rgba(67, 236, 190, .22), transparent 0 24%),
                radial-gradient(circle at 72% 82%, rgba(255, 220, 90, .16), transparent 0 26%);
            animation: aurora-shift 13s ease-in-out infinite alternate;
        }
        .stApp::after {
            inset: 0;
            background-image:
                linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px);
            background-size: 48px 48px;
            mask-image: linear-gradient(to bottom, rgba(0,0,0,.7), transparent 72%);
        }
        .main .block-container {
            position: relative;
            z-index: 1;
        }
        [data-testid="stHeader"] {
            background: transparent !important;
        }
        .hero,
        .welcome-stage {
            min-height: 360px !important;
            isolation: isolate;
            background:
                linear-gradient(115deg, rgba(6,8,15,.98) 0%, rgba(12,14,22,.9) 46%, rgba(26,33,44,.74) 100%),
                radial-gradient(circle at 82% 28%, rgba(255,220,90,.34), transparent 0 18%, transparent 38%),
                radial-gradient(circle at 72% 76%, rgba(67,236,190,.24), transparent 0 22%, transparent 42%),
                url("https://images.unsplash.com/photo-1516280440614-37939bbacd81?auto=format&fit=crop&w=1800&q=80") !important;
        }
        .brand-lockup {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 18px;
        }
        .brand-logo,
        .hero-logo,
        .startup-logo {
            display: block;
            width: clamp(86px, 11vw, 138px);
            aspect-ratio: 1;
            object-fit: contain;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,.16);
            background: rgba(0,0,0,.28);
            box-shadow: 0 20px 50px rgba(0,0,0,.36), 0 0 34px rgba(67,236,190,.2);
        }
        .hero-logo {
            width: clamp(92px, 12vw, 150px);
        }
        .startup-logo {
            width: 112px;
            margin-bottom: 14px;
        }
        .brand-logo-fallback {
            width: 92px;
            aspect-ratio: 1;
            display: grid;
            place-items: center;
            border-radius: 8px;
            background: linear-gradient(135deg, #ff4474, #ffdc5a, #43ecbe);
            color: #080a10;
            font-weight: 1000;
            font-size: 1.5rem;
        }
        .brand-copy {
            display: grid;
            gap: 4px;
        }
        .brand-copy .brand-name {
            color: #fffdf6;
            font-family: "Segoe UI Black", "Arial Black", "Segoe UI", Arial, sans-serif;
            font-size: clamp(1.4rem, 2.6vw, 2.2rem);
            line-height: 1;
        }
        .brand-copy .brand-subtitle {
            color: rgba(255,255,255,.7);
            font-weight: 800;
            font-size: .9rem;
        }
        .spotify-splash {
            position: fixed;
            inset: 0;
            z-index: 999999;
            display: grid;
            place-items: center;
            background:
                radial-gradient(circle at 50% 42%, rgba(67,236,190,.18), transparent 0 24%, transparent 44%),
                radial-gradient(circle at 38% 62%, rgba(255,68,116,.13), transparent 0 20%, transparent 42%),
                #050608;
            overflow: hidden;
        }
        .spotify-splash::before {
            content: "";
            position: absolute;
            width: 420px;
            height: 420px;
            border-radius: 50%;
            background: conic-gradient(from 90deg, rgba(67,236,190,.18), rgba(255,220,90,.16), rgba(255,68,116,.14), rgba(67,236,190,.18));
            filter: blur(20px);
            animation: spin-record 8s linear infinite;
        }
        .splash-logo-wrap {
            position: relative;
            display: grid;
            justify-items: center;
            gap: 18px;
            animation: splash-pop .72s cubic-bezier(.2,.8,.2,1) both;
        }
        .splash-logo {
            width: min(44vw, 250px);
            aspect-ratio: 1;
            object-fit: contain;
            border-radius: 22px;
            box-shadow: 0 0 70px rgba(67,236,190,.26), 0 34px 80px rgba(0,0,0,.55);
            animation: splash-pulse 1.7s ease-in-out infinite;
        }
        .splash-title {
            color: #fffdf6;
            font-family: "Segoe UI Black", "Arial Black", "Segoe UI", Arial, sans-serif;
            font-size: clamp(2rem, 7vw, 4rem);
            line-height: 1;
            text-shadow: 0 0 34px rgba(67,236,190,.24);
        }
        .splash-loader {
            width: min(52vw, 310px);
            height: 5px;
            border-radius: 999px;
            overflow: hidden;
            background: rgba(255,255,255,.14);
        }
        .splash-loader span {
            display: block;
            height: 100%;
            width: 42%;
            border-radius: inherit;
            background: linear-gradient(90deg, #ff4474, #ffdc5a, #43ecbe);
            animation: splash-load 1.25s ease-in-out infinite;
        }
        @keyframes splash-pop {
            from { transform: translateY(18px) scale(.94); opacity: 0; }
            to { transform: translateY(0) scale(1); opacity: 1; }
        }
        @keyframes splash-pulse {
            0%, 100% { transform: scale(1); filter: brightness(1); }
            50% { transform: scale(1.035); filter: brightness(1.08); }
        }
        @keyframes splash-load {
            0% { transform: translateX(-120%); }
            100% { transform: translateX(260%); }
        }
        .hero::after,
        .welcome-stage::after {
            content: "";
            position: absolute;
            right: clamp(18px, 6vw, 80px);
            top: 50%;
            width: clamp(170px, 24vw, 310px);
            aspect-ratio: 1;
            border-radius: 50%;
            transform: translateY(-50%);
            background:
                radial-gradient(circle at center, #fff8dd 0 8%, #0c0f18 8% 18%, transparent 18%),
                repeating-radial-gradient(circle at center, rgba(255,255,255,.22) 0 2px, transparent 2px 15px),
                conic-gradient(from 35deg, #ff4474, #ffdc5a, #43ecbe, #5ab6ff, #ff4474);
            box-shadow: 0 28px 90px rgba(0,0,0,.42), inset 0 0 0 18px rgba(0,0,0,.36);
            opacity: .62;
            z-index: -1;
            animation: spin-record 12s linear infinite;
        }
        .hero h1,
        .welcome-stage h1 {
            max-width: 760px !important;
            font-size: clamp(2.5rem, 6vw, 5.4rem) !important;
            line-height: .9 !important;
        }
        .welcome-player,
        .hero-deck {
            background:
                linear-gradient(145deg, rgba(255,255,255,.15), rgba(255,255,255,.045)),
                rgba(9, 12, 20, .74) !important;
            border: 1px solid rgba(255,255,255,.2) !important;
            box-shadow: 0 24px 70px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.12) !important;
        }
        .section-intro {
            display: grid;
            gap: 6px;
            background:
                linear-gradient(135deg, rgba(67,236,190,.18), transparent 36%),
                radial-gradient(circle at 96% 12%, rgba(255,220,90,.16), transparent 0 20%, transparent 38%),
                rgba(11, 14, 22, .9) !important;
        }
        .section-intro::after {
            content: "";
            position: absolute;
            right: 22px;
            top: 22px;
            width: 86px;
            height: 86px;
            border-radius: 50%;
            background:
                radial-gradient(circle at center, rgba(255,255,255,.95) 0 10%, rgba(10,12,18,.92) 10% 22%, transparent 22%),
                conic-gradient(from 120deg, #43ecbe, #5ab6ff, #ff4474, #ffdc5a, #43ecbe);
            opacity: .5;
            box-shadow: inset 0 0 0 10px rgba(0,0,0,.25);
        }
        div[data-testid="stHorizontalBlock"] {
            gap: .85rem !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
            min-height: 52px !important;
            border-radius: 8px !important;
            text-transform: none !important;
            background:
                linear-gradient(180deg, rgba(255,255,255,.105), rgba(255,255,255,.035)),
                rgba(9, 12, 20, .9) !important;
        }
        .song-card {
            min-height: 124px;
            padding: 18px 20px !important;
            background:
                linear-gradient(110deg, rgba(255,255,255,.1), transparent 18%),
                radial-gradient(circle at 4% 24%, rgba(67,236,190,.2), transparent 0 18%, transparent 38%),
                radial-gradient(circle at 98% 88%, rgba(255,68,116,.15), transparent 0 20%, transparent 42%),
                rgba(10, 13, 21, .92) !important;
        }
        .track-row {
            display: grid !important;
            grid-template-columns: 104px minmax(0, 1fr) !important;
            align-items: center !important;
            gap: 18px !important;
        }
        .album-mark {
            width: 104px !important;
            height: 104px !important;
            min-width: 104px !important;
            position: relative !important;
            transform: rotate(-2deg);
            transition: transform .18s ease !important;
        }
        .song-card:hover .album-mark {
            transform: rotate(0deg) scale(1.035);
        }
        .creative-cover::after {
            content: "";
            position: absolute;
            inset: 10px;
            border-radius: 50%;
            background:
                radial-gradient(circle at center, rgba(255,255,255,.98) 0 10%, rgba(6,8,15,.95) 10% 25%, transparent 25%),
                repeating-radial-gradient(circle at center, rgba(255,255,255,.18) 0 1px, transparent 1px 9px);
            mix-blend-mode: screen;
            opacity: .7;
        }
        .cover-initials,
        .cover-tag {
            z-index: 3 !important;
        }
        .song-card h3 {
            margin-bottom: 10px !important;
            text-wrap: balance;
        }
        .song-card .meta {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 7px !important;
            align-items: center !important;
        }
        .song-card .meta span:not(.pill),
        .pill {
            margin: 0 !important;
        }
        .metric-card {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 95% 10%, rgba(255,220,90,.2), transparent 0 28%, transparent 50%),
                linear-gradient(145deg, rgba(255,255,255,.1), rgba(255,255,255,.03)),
                rgba(10, 13, 21, .88) !important;
        }
        .metric-card::after {
            content: "";
            position: absolute;
            right: -26px;
            bottom: -26px;
            width: 96px;
            height: 96px;
            border-radius: 50%;
            background: conic-gradient(#43ecbe, #ffdc5a, #ff4474, #43ecbe);
            opacity: .2;
        }
        .playlist-player {
            position: relative;
            overflow: hidden;
            padding: 22px !important;
            background:
                linear-gradient(135deg, rgba(67,236,190,.14), transparent 34%),
                radial-gradient(circle at 100% 0%, rgba(255,220,90,.18), transparent 0 22%, transparent 42%),
                rgba(10, 13, 21, .92) !important;
        }
        .playlist-player-title {
            font-size: 1.45rem !important;
            color: #fffdf7 !important;
        }
        .playlist-player audio {
            filter: saturate(1.2);
        }
        .profile-panel {
            padding: 24px !important;
            background:
                radial-gradient(circle at 92% 12%, rgba(90,182,255,.18), transparent 0 24%, transparent 46%),
                linear-gradient(145deg, rgba(255,255,255,.1), rgba(255,255,255,.03)),
                rgba(10,13,21,.9) !important;
        }
        .profile-avatar-img,
        .profile-avatar-fallback {
            border-radius: 18px !important;
            border-color: rgba(255,220,90,.8) !important;
            transform: rotate(-2deg);
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stDownloadButton"] > button,
        div[data-testid="stLinkButton"] > a {
            position: relative;
            overflow: hidden;
        }
        div[data-testid="stButton"] > button::before,
        div[data-testid="stFormSubmitButton"] > button::before,
        div[data-testid="stDownloadButton"] > button::before {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,.42), transparent);
            transform: translateX(-110%);
            transition: transform .45s ease;
        }
        div[data-testid="stButton"] > button:hover::before,
        div[data-testid="stFormSubmitButton"] > button:hover::before,
        div[data-testid="stDownloadButton"] > button:hover::before {
            transform: translateX(110%);
        }
        div[data-testid="stTabs"] [role="tablist"] {
            gap: 8px;
            border-radius: 8px;
            background: rgba(255,255,255,.06);
            padding: 8px;
        }
        div[data-testid="stTabs"] [role="tab"] {
            border-radius: 8px;
            color: var(--studio-soft);
        }
        div[data-testid="stTabs"] [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(67,236,190,.22), rgba(255,220,90,.14));
            color: #fffdf7 !important;
        }
        @keyframes aurora-shift {
            from { transform: scale(1) translate3d(0,0,0); opacity: .85; }
            to { transform: scale(1.08) translate3d(-2%, 1%, 0); opacity: 1; }
        }
        @media (max-width: 760px) {
            .hero,
            .welcome-stage {
                min-height: 440px !important;
            }
            .hero::after,
            .welcome-stage::after {
                right: -38px;
                top: 18px;
                transform: none;
                width: 180px;
                opacity: .38;
            }
            .track-row {
                grid-template-columns: 82px minmax(0, 1fr) !important;
                gap: 12px !important;
            }
            .album-mark {
                width: 82px !important;
                height: 82px !important;
                min-width: 82px !important;
            }
            .section-intro::after {
                width: 58px;
                height: 58px;
                right: 12px;
                top: 12px;
            }
            .brand-lockup {
                align-items: flex-start;
                gap: 12px;
            }
            .startup-logo,
            .hero-logo {
                width: 82px;
            }
        }

        /* Spotify-style final interface */
        :root {
            --spotify-bg: #000000;
            --spotify-shell: #121212;
            --spotify-card: #181818;
            --spotify-card-hover: #282828;
            --spotify-panel: #1f1f1f;
            --spotify-green: #1db954;
            --spotify-green-bright: #1ed760;
            --spotify-text: #ffffff;
            --spotify-muted: #b3b3b3;
            --spotify-faint: #727272;
        }
        .stApp {
            background: var(--spotify-bg) !important;
            color: var(--spotify-text) !important;
        }
        .stApp::before,
        .stApp::after {
            display: none !important;
        }
        .main .block-container {
            max-width: 1360px !important;
            padding: 18px 24px 64px !important;
        }
        [data-testid="stSidebar"] {
            background: #000000 !important;
            border-right: 8px solid #000 !important;
        }
        [data-testid="stSidebar"] img {
            border-radius: 12px !important;
            background: #121212 !important;
            padding: 8px;
        }
        [data-testid="stSidebar"] h1 {
            color: var(--spotify-text) !important;
            font-size: 1.35rem !important;
        }
        [data-testid="stSidebar"] * {
            color: var(--spotify-muted) !important;
        }
        [data-testid="stSidebar"] strong {
            color: var(--spotify-text) !important;
        }
        .hero,
        .welcome-stage {
            min-height: 330px !important;
            border: 0 !important;
            border-radius: 8px !important;
            background:
                linear-gradient(180deg, rgba(29,185,84,.34) 0%, rgba(18,18,18,.98) 72%),
                #121212 !important;
            box-shadow: none !important;
            padding: 34px !important;
        }
        .hero::after,
        .welcome-stage::after,
        .section-intro::after {
            display: none !important;
        }
        .brand-lockup {
            gap: 18px !important;
            margin-bottom: 22px !important;
        }
        .hero-logo,
        .startup-logo,
        .brand-logo {
            border-radius: 8px !important;
            border: 0 !important;
            background: #181818 !important;
            box-shadow: 0 16px 48px rgba(0,0,0,.55) !important;
        }
        .brand-copy .brand-name {
            color: #fff !important;
            font-family: "Segoe UI", Arial, sans-serif !important;
            font-weight: 900 !important;
        }
        .brand-copy .brand-subtitle,
        .hero p,
        .welcome-stage p {
            color: var(--spotify-muted) !important;
            font-weight: 600 !important;
        }
        .hero h1,
        .welcome-stage h1 {
            font-family: "Segoe UI", Arial, sans-serif !important;
            font-size: clamp(2.7rem, 6.2vw, 5.8rem) !important;
            font-weight: 950 !important;
            letter-spacing: -1px !important;
            color: #fff !important;
            text-shadow: none !important;
        }
        .hero-deck,
        .welcome-player,
        .startup-card,
        .startup-popup,
        .profile-panel,
        .playlist-player,
        .metric-card,
        .section-intro {
            border: 0 !important;
            border-radius: 8px !important;
            background: var(--spotify-shell) !important;
            box-shadow: none !important;
        }
        .section-intro {
            padding: 24px !important;
            margin-top: 12px !important;
        }
        .section-intro::before {
            display: none !important;
        }
        .section-intro h2 {
            color: #fff !important;
            font-family: "Segoe UI", Arial, sans-serif !important;
            font-size: clamp(1.8rem, 3vw, 2.6rem) !important;
            font-weight: 900 !important;
            letter-spacing: -0.5px !important;
        }
        .section-intro p,
        .metric-card .label {
            color: var(--spotify-muted) !important;
        }
        .metric-card {
            min-height: 112px !important;
            transition: background .18s ease, transform .18s ease !important;
        }
        .metric-card::after,
        .metric-card::before {
            display: none !important;
        }
        .metric-card:hover {
            background: var(--spotify-card-hover) !important;
            transform: translateY(-1px);
        }
        .metric-card .value {
            color: #fff !important;
            font-family: "Segoe UI", Arial, sans-serif !important;
            font-weight: 900 !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
            min-height: 48px !important;
            border-radius: 999px !important;
            border: 0 !important;
            background: #1f1f1f !important;
            color: #fff !important;
            box-shadow: none !important;
            font-weight: 800 !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button:hover {
            background: #2a2a2a !important;
            color: #fff !important;
            transform: scale(1.02) !important;
            border: 0 !important;
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stDownloadButton"] > button,
        div[data-testid="stLinkButton"] > a {
            border-radius: 999px !important;
            border: 0 !important;
            min-height: 46px !important;
            background: var(--spotify-green) !important;
            color: #000 !important;
            box-shadow: none !important;
            font-weight: 900 !important;
        }
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover,
        div[data-testid="stLinkButton"] > a:hover {
            background: var(--spotify-green-bright) !important;
            transform: scale(1.035) !important;
            box-shadow: none !important;
            filter: none !important;
        }
        div[data-testid="stButton"] > button::before,
        div[data-testid="stFormSubmitButton"] > button::before,
        div[data-testid="stDownloadButton"] > button::before {
            display: none !important;
        }
        div[data-testid="stButton"] > button:disabled,
        div[data-testid="stFormSubmitButton"] > button:disabled {
            background: #1f1f1f !important;
            color: #666 !important;
        }
        .song-card {
            min-height: 92px !important;
            border: 0 !important;
            border-radius: 8px !important;
            background: transparent !important;
            box-shadow: none !important;
            padding: 10px 14px !important;
            transition: background .15s ease !important;
        }
        .song-card::before,
        .song-card::after {
            display: none !important;
        }
        .song-card:hover {
            background: rgba(255,255,255,.08) !important;
            transform: none !important;
            border: 0 !important;
            box-shadow: none !important;
        }
        .track-row {
            grid-template-columns: 64px minmax(0, 1fr) !important;
            gap: 16px !important;
        }
        .album-mark {
            width: 64px !important;
            height: 64px !important;
            min-width: 64px !important;
            border-radius: 6px !important;
            border: 0 !important;
            transform: none !important;
            box-shadow: 0 8px 18px rgba(0,0,0,.35) !important;
        }
        .song-card:hover .album-mark {
            transform: none !important;
        }
        .creative-cover {
            border-radius: 6px !important;
            background:
                linear-gradient(135deg, #1db954, #191414 48%, #535353) !important;
            box-shadow: none !important;
        }
        .creative-cover::before {
            opacity: .25 !important;
        }
        .creative-cover::after,
        .cover-ring {
            display: none !important;
        }
        .cover-initials {
            color: #fff !important;
            font-size: .9rem !important;
            text-shadow: none !important;
        }
        .cover-tag {
            background: rgba(0,0,0,.72) !important;
            color: #1ed760 !important;
            border: 0 !important;
        }
        .song-card h3 {
            color: #fff !important;
            font-family: "Segoe UI", Arial, sans-serif !important;
            font-size: 1.02rem !important;
            font-weight: 800 !important;
            margin: 0 0 6px !important;
        }
        .song-card .meta {
            color: var(--spotify-muted) !important;
            font-size: .9rem !important;
            gap: 5px !important;
            line-height: 1.45 !important;
        }
        .song-card .meta span:not(.pill) {
            min-height: 0 !important;
            padding: 0 !important;
            border: 0 !important;
            border-radius: 0 !important;
            background: transparent !important;
            color: var(--spotify-muted) !important;
        }
        .pill,
        .mood-chip {
            min-height: 0 !important;
            border-radius: 999px !important;
            border: 0 !important;
            background: rgba(29,185,84,.18) !important;
            color: #1ed760 !important;
            padding: 4px 10px !important;
            font-size: .78rem !important;
            font-weight: 900 !important;
        }
        div[data-testid="stTabs"] [role="tablist"] {
            background: var(--spotify-shell) !important;
            border-radius: 999px !important;
            padding: 6px !important;
        }
        div[data-testid="stTabs"] [role="tab"] {
            border-radius: 999px !important;
            color: var(--spotify-muted) !important;
            font-weight: 800 !important;
        }
        div[data-testid="stTabs"] [aria-selected="true"] {
            background: #2a2a2a !important;
            color: #fff !important;
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input {
            border: 0 !important;
            border-radius: 6px !important;
            background: #242424 !important;
            color: #fff !important;
            box-shadow: none !important;
        }
        div[data-testid="stSelectbox"] *,
        div[data-testid="stTextInput"] input::placeholder,
        div[data-testid="stTextArea"] textarea::placeholder {
            color: var(--spotify-muted) !important;
        }
        .stAudio {
            border: 0 !important;
            border-radius: 8px !important;
            box-shadow: none !important;
            background: #181818 !important;
        }
        .spotify-splash {
            background: #000 !important;
        }
        .spotify-splash::before {
            display: none !important;
        }
        .splash-logo {
            border-radius: 12px !important;
            box-shadow: 0 24px 80px rgba(0,0,0,.65) !important;
        }
        .splash-title {
            color: #fff !important;
            text-shadow: none !important;
        }
        .splash-loader span {
            background: var(--spotify-green-bright) !important;
        }
        @media (max-width: 760px) {
            .main .block-container {
                padding: 12px 12px 56px !important;
            }
            .hero,
            .welcome-stage {
                min-height: 360px !important;
                padding: 22px !important;
            }
            .track-row {
                grid-template-columns: 56px minmax(0, 1fr) !important;
            }
            .album-mark {
                width: 56px !important;
                height: 56px !important;
                min-width: 56px !important;
            }
        }

        /* EcoWavE streaming-app polish, intentionally distinct branding */
        body {
            background: #000 !important;
        }
        .stApp {
            background:
                linear-gradient(180deg, rgba(30, 215, 96, .11) 0, transparent 260px),
                #000 !important;
        }
        [data-testid="stAppViewContainer"] > .main {
            background: transparent !important;
        }
        .main .block-container {
            background: #121212 !important;
            border-radius: 8px !important;
            margin-top: 10px !important;
            min-height: calc(100vh - 24px);
        }
        [data-testid="stSidebar"] {
            padding-top: 10px !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: .55rem !important;
        }
        [data-testid="stSidebar"] button {
            border-radius: 999px !important;
            background: #1f1f1f !important;
            color: #fff !important;
        }
        .hero {
            display: grid !important;
            grid-template-columns: minmax(0, 1.4fr) 320px !important;
            gap: 28px !important;
            align-items: end !important;
            background:
                linear-gradient(180deg, rgba(30,215,96,.42), rgba(18,18,18,.96) 78%),
                #121212 !important;
            padding: 38px !important;
        }
        .hero h1 {
            margin-top: 8px !important;
            margin-bottom: 14px !important;
        }
        .hero p {
            max-width: 720px !important;
            font-size: 1.04rem !important;
        }
        .hero-deck {
            align-self: stretch !important;
            display: grid !important;
            align-content: center !important;
            background: rgba(0,0,0,.24) !important;
        }
        .visualizer span {
            background: #1ed760 !important;
            box-shadow: none !important;
        }
        .visualizer span:nth-child(2),
        .visualizer span:nth-child(3),
        .visualizer span:nth-child(6),
        .visualizer span:nth-child(7) {
            background: #b3b3b3 !important;
        }
        .section-intro,
        .profile-panel,
        .playlist-player {
            background: #181818 !important;
            padding: 24px !important;
        }
        .section-intro h2::before {
            content: "";
            display: inline-block;
            width: 10px;
            height: 10px;
            margin-right: 10px;
            border-radius: 50%;
            background: #1ed760;
            vertical-align: middle;
        }
        .metric-card {
            background: #181818 !important;
            padding: 22px !important;
        }
        .metric-card .label {
            text-transform: none !important;
            font-size: .9rem !important;
            font-weight: 700 !important;
        }
        .metric-card .value {
            font-size: 2.1rem !important;
        }
        .song-card {
            border-bottom: 1px solid rgba(255,255,255,.06) !important;
            border-radius: 0 !important;
            margin: 0 !important;
        }
        .song-card:hover {
            border-radius: 6px !important;
        }
        .song-card h3 {
            font-size: .98rem !important;
        }
        .song-card .meta {
            font-size: .86rem !important;
        }
        .album-mark {
            border-radius: 4px !important;
        }
        .creative-cover {
            border-radius: 4px !important;
        }
        .real-cover {
            width: 100% !important;
            height: 100% !important;
            object-fit: cover !important;
            display: block !important;
            border-radius: 4px !important;
            background: #282828 !important;
        }
        .cover-tag {
            display: none !important;
        }
        .pill {
            background: transparent !important;
            color: #1ed760 !important;
            padding: 0 !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
            height: 44px !important;
            min-height: 44px !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button:focus {
            outline: 2px solid #1ed760 !important;
            outline-offset: 2px !important;
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stDownloadButton"] > button {
            height: 44px !important;
            min-height: 44px !important;
            padding-left: 20px !important;
            padding-right: 20px !important;
        }
        div[data-testid="stTextInput"] label,
        div[data-testid="stTextArea"] label,
        div[data-testid="stSelectbox"] label,
        div[data-testid="stNumberInput"] label {
            color: #fff !important;
            font-weight: 800 !important;
        }
        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            box-shadow: 0 0 0 2px #1ed760 !important;
        }
        div[data-testid="stAlert"] {
            background: #181818 !important;
            border: 1px solid #2a2a2a !important;
            color: #fff !important;
        }
        [data-testid="stDataFrame"] {
            background: #181818 !important;
        }
        .startup-page {
            background: #000 !important;
        }
        .startup-card,
        .startup-popup {
            background: #121212 !important;
        }
        .startup-feature {
            background: #181818 !important;
            border: 0 !important;
        }
        .feature-icon {
            background: #1ed760 !important;
            color: #000 !important;
        }
        .playlist-player-title {
            color: #fff !important;
            font-weight: 900 !important;
        }
        .boosted-player {
            background: #181818;
            border-radius: 8px;
            padding: 12px;
            margin-top: 8px;
        }
        .boosted-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
            color: #b3b3b3;
            font-size: .86rem;
            font-weight: 700;
        }
        .boosted-row input {
            flex: 1;
            accent-color: #1ed760;
        }
        .boosted-row strong {
            color: #fff;
            min-width: 38px;
            text-align: right;
        }
        .login-card {
            background: #121212 !important;
            border: 1px solid #242424 !important;
        }
        .track-row {
            display: grid !important;
            grid-template-columns: 34px 52px minmax(260px, 1fr) minmax(160px, 280px) 62px !important;
            align-items: center !important;
            gap: 14px !important;
            width: 100% !important;
        }
        .track-index {
            color: #b3b3b3;
            font-size: 1rem;
            font-weight: 700;
            text-align: right;
            font-variant-numeric: tabular-nums;
        }
        .track-main {
            min-width: 0;
        }
        .track-main h3 {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .track-album,
        .track-duration {
            color: #b3b3b3;
            font-size: .95rem;
            font-weight: 700;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .track-duration {
            text-align: right;
            font-variant-numeric: tabular-nums;
        }
        .song-card:hover .track-index,
        .song-card:hover .track-album,
        .song-card:hover .track-duration {
            color: #fff;
        }
        .song-card + div[data-testid="stHorizontalBlock"] {
            margin-left: 100px;
            max-width: 560px;
            margin-bottom: 8px;
        }
        .song-card + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button,
        .song-card + div[data-testid="stHorizontalBlock"] div[data-testid="stDownloadButton"] > button {
            min-height: 34px !important;
            height: 34px !important;
            font-size: .82rem !important;
            padding-left: 14px !important;
            padding-right: 14px !important;
        }
        @media (max-width: 900px) {
            .hero {
                grid-template-columns: 1fr !important;
            }
            .track-row {
                grid-template-columns: 28px 52px minmax(0, 1fr) 54px !important;
            }
            .track-album {
                display: none !important;
            }
        }
        @media (max-width: 760px) {
            .main .block-container {
                border-radius: 0 !important;
                margin-top: 0 !important;
            }
            .hero {
                padding: 22px !important;
            }
            .metric-card .value {
                font-size: 1.6rem !important;
            }
            .track-row {
                grid-template-columns: 24px 48px minmax(0, 1fr) 48px !important;
                gap: 10px !important;
            }
            .track-index,
            .track-duration {
                font-size: .84rem !important;
            }
            .song-card + div[data-testid="stHorizontalBlock"] {
                margin-left: 0;
                max-width: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mobile_install_hint():
    st.markdown(
        f"""
        <div class="mobile-install">
            <strong>Permanent project link</strong>
            <span>On this computer, always open <b>{local_app_url()}</b> after starting EcoWavE.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def local_app_url(port=8501):
    return f"http://localhost:{port}"


@st.cache_data(ttl=3600, show_spinner=False)
def network_url(port=8501):
    ip_address = "localhost"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        ip_address = sock.getsockname()[0]
    except OSError:
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except OSError:
            ip_address = "localhost"
    finally:
        sock.close()
    return f"http://{ip_address}:{port}"


def app_splash_screen():
    if st.session_state.get("app_splash_seen"):
        return
    logo_html = logo_img_html("splash-logo")
    st.markdown(
        f"""
        <div class="spotify-splash" role="status" aria-label="Opening EcoWavE">
            <div class="splash-logo-wrap">
                {logo_html}
                <div class="splash-loader"><span></span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.app_splash_seen = True


def animated_welcome():
    mood_chips = "".join(f'<span class="mood-chip">{html.escape(mood)}</span>' for mood in MOODS[:6])
    logo_html = logo_img_html("hero-logo")
    st.markdown(
        f"""
        <section class="welcome-stage" aria-label="Animated welcome to EcoWavE">
            <div class="welcome-copy">
                <div class="brand-lockup">
                    {logo_html}
                    <div class="brand-copy">
                        <div class="brand-name">{APP_TITLE}</div>
                        <div class="brand-subtitle">Your mood. Your music. Instantly.</div>
                    </div>
                </div>
                <h1>Welcome to {APP_TITLE}</h1>
                <p>Start with how you feel, then let the recommender tune the room with playlists, online discoveries, favorites, and listening history.</p>
                <div class="welcome-moods">{mood_chips}</div>
            </div>
            <div class="welcome-player" aria-hidden="true">
                <div class="record-wrap">
                    <div class="record-label">EW</div>
                </div>
                <div class="welcome-trackline">Finding your first mood match</div>
                <div class="visualizer">
                    <span></span><span></span><span></span><span></span>
                    <span></span><span></span><span></span><span></span>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def startup_popup():
    if st.session_state.get("startup_popup_seen"):
        return True

    logo_html = logo_img_html("startup-logo")
    st.markdown(
        f"""
        <div class="startup-page">
            <div class="startup-card">
                <div class="startup-popup">
                    {logo_html}
                    <div class="startup-kicker">EcoWavE Studio</div>
                    <h2>Start your music mood journey</h2>
                    <p>Pick a mood, discover Punjabi tracks, save favorites, and let EcoWavE keep your listening history ready.</p>
                    <div class="startup-grid">
                        <div class="startup-feature"><span class="feature-icon">PL</span>Playlists<span>Create mixes and play songs in order.</span></div>
                        <div class="startup-feature"><span class="feature-icon">ON</span>Online Music<span>Search fresh tracks separately.</span></div>
                        <div class="startup-feature"><span class="feature-icon">FR</span>Free<span>Use EcoWavE without paid access.</span></div>
                        <div class="startup-feature"><span class="feature-icon">AD</span>Ad Free<span>Listen without ad breaks inside the app.</span></div>
                    </div>
                </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("startup_enter_form", clear_on_submit=False):
        entered = st.form_submit_button("→", use_container_width=True)
    st.markdown("</div></div>", unsafe_allow_html=True)
    if entered:
        st.session_state.startup_popup_seen = True
        st.rerun()
    return False


def login_success_animation(user):
    name = html.escape(user["name"])
    role = html.escape(user["role"].title())
    st.markdown(
        f"""
        <div class="login-burst" role="status" aria-live="polite">
            <div class="login-card">
                <div class="login-orbit">
                    <div class="login-note">EW</div>
                </div>
                <h2>Welcome back, {name}</h2>
                <p>{role} account unlocked. Your EcoWavE dashboard is tuning up now.</p>
                <div class="visualizer" aria-hidden="true">
                    <span></span><span></span><span></span><span></span>
                    <span></span><span></span><span></span><span></span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def password_hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def mysql_config():
    secret_cfg = {}
    try:
        secret_cfg = dict(st.secrets.get("mysql", {}))
    except Exception:
        secret_cfg = {}
    return {
        "host": os.getenv("MYSQL_HOST", secret_cfg.get("host", "localhost")),
        "port": int(os.getenv("MYSQL_PORT", secret_cfg.get("port", 3306))),
        "user": os.getenv("MYSQL_USER", secret_cfg.get("user", "root")),
        "password": os.getenv("MYSQL_PASSWORD", secret_cfg.get("password", "")),
        "database": os.getenv("MYSQL_DATABASE", secret_cfg.get("database", "mood_tunes")),
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
    }


def use_sqlite_backend():
    if os.getenv("MOOD_TUNES_SQLITE") == "1":
        return True
    cfg = mysql_config()
    explicit_mysql = any(
        os.getenv(name)
        for name in ("MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE")
    )
    if explicit_mysql:
        return False
    try:
        secret_cfg = dict(st.secrets.get("mysql", {}))
    except Exception:
        secret_cfg = {}
    host = str(cfg.get("host", "")).lower()
    password = str(cfg.get("password", ""))
    return host in ("", "localhost", "127.0.0.1") and not password and not secret_cfg


def sqlite_db_path():
    return os.path.join(BASE_DIR, "mood_tunes_streamlit.db")


def sqlite_connect():
    conn = sqlite3.connect(sqlite_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def server_config_without_db():
    cfg = mysql_config()
    cfg.pop("database", None)
    return cfg


def connect_db(create_database=True):
    if use_sqlite_backend():
        return sqlite_connect()
    cfg = mysql_config()
    try:
        return pymysql.connect(**cfg)
    except pymysql.err.OperationalError:
        if not create_database:
            raise
        server = pymysql.connect(**server_config_without_db())
        with server.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        server.close()
        return pymysql.connect(**cfg)


def sqlite_statement(sql):
    statement = sql.strip()
    duplicate_target = ""
    if "ON DUPLICATE KEY UPDATE" in statement:
        if "audio_stream_cache" in statement:
            duplicate_target = "source_hash"
        elif "users" in statement:
            duplicate_target = "email"
    replacements = [
        ("AUTO_INCREMENT", "AUTOINCREMENT"),
        ("MEDIUMTEXT", "TEXT"),
        ("BOOLEAN", "INTEGER"),
        ("TRUE", "1"),
        ("FALSE", "0"),
        ("NOW()", "CURRENT_TIMESTAMP"),
        ("INSERT IGNORE", "INSERT OR IGNORE"),
        ("%s", "?"),
    ]
    statement = re.sub(r"role\s+ENUM\('user',\s*'admin'\)", "role TEXT", statement)
    statement = re.sub(r"UNIQUE\s+KEY\s+\w+\s*\(([^)]+)\)", r"UNIQUE(\1)", statement, flags=re.IGNORECASE)
    statement = re.sub(r"\s+AFTER\s+\w+", "", statement, flags=re.IGNORECASE)
    statement = re.sub(r"ON UPDATE CURRENT_TIMESTAMP", "", statement, flags=re.IGNORECASE)
    if duplicate_target:
        statement = statement.replace("ON DUPLICATE KEY UPDATE", f"ON CONFLICT({duplicate_target}) DO UPDATE SET")
    statement = statement.replace("name=VALUES(name)", "name=excluded.name")
    statement = statement.replace("password_hash=VALUES(password_hash)", "password_hash=excluded.password_hash")
    statement = statement.replace("role=VALUES(role)", "role=excluded.role")
    statement = statement.replace("favorite_mood=VALUES(favorite_mood)", "favorite_mood=excluded.favorite_mood")
    statement = statement.replace("bio=VALUES(bio)", "bio=excluded.bio")
    statement = statement.replace("source_url=VALUES(source_url)", "source_url=excluded.source_url")
    statement = statement.replace("audio_url=VALUES(audio_url)", "audio_url=excluded.audio_url")
    statement = statement.replace("expires_at=VALUES(expires_at)", "expires_at=excluded.expires_at")
    for old, new in replacements:
        statement = statement.replace(old, new)
    statement = re.sub(r"\bid\s+INT\s+AUTOINCREMENT\s+PRIMARY\s+KEY\b", "id INTEGER PRIMARY KEY AUTOINCREMENT", statement, flags=re.IGNORECASE)
    return statement


def execute(sql, params=None, fetch=False, many=False):
    with connect_db() as conn:
        if isinstance(conn, sqlite3.Connection):
            statement = sqlite_statement(sql)
            cur = conn.cursor()
            if many:
                cur.executemany(statement, params or [])
            else:
                cur.execute(statement, params or ())
            if fetch:
                return [dict(row) for row in cur.fetchall()]
            conn.commit()
            return cur.lastrowid
        with conn.cursor() as cur:
            if many:
                cur.executemany(sql, params or [])
            else:
                cur.execute(sql, params or ())
            if fetch:
                return cur.fetchall()
            return cur.lastrowid


def init_db():
    statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            email VARCHAR(160) NOT NULL UNIQUE,
            password_hash VARCHAR(128) NOT NULL,
            role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
            favorite_mood VARCHAR(40) DEFAULT 'Happy',
            bio VARCHAR(255) DEFAULT '',
            profile_image MEDIUMTEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS songs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(180) NOT NULL,
            artist VARCHAR(140) NOT NULL,
            album VARCHAR(180) DEFAULT '',
            cover_url TEXT,
            mood VARCHAR(40) NOT NULL,
            genre VARCHAR(80) DEFAULT '',
            source_url TEXT NOT NULL,
            duration_seconds INT DEFAULT 180,
            energy INT DEFAULT 50,
            valence INT DEFAULT 50,
            added_by INT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE SET NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS saved_songs (
            user_id INT NOT NULL,
            song_id INT NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, song_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS playlists (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(120) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_user_playlist_name (user_id, name),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS playlist_songs (
            playlist_id INT NOT NULL,
            song_id INT NOT NULL,
            position INT NOT NULL DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (playlist_id, song_id),
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS listening_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            song_id INT NOT NULL,
            mood VARCHAR(40) NOT NULL,
            listened_seconds INT DEFAULT 0,
            listened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS login_tokens (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            token_hash VARCHAR(128) NOT NULL UNIQUE,
            expires_at DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS audio_stream_cache (
            source_hash VARCHAR(64) PRIMARY KEY,
            source_url TEXT NOT NULL,
            audio_url TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """,
    ]
    for statement in statements:
        execute(statement)
    ensure_user_profile_columns()
    ensure_song_album_column()
    ensure_song_cover_column()
    seed_data()


@st.cache_resource(show_spinner=False)
def initialize_app_once():
    init_db()
    return True


def ensure_user_profile_columns():
    if use_sqlite_backend():
        columns = {row["name"] for row in execute("PRAGMA table_info(users)", fetch=True)}
        if "profile_image" not in columns:
            execute("ALTER TABLE users ADD COLUMN profile_image TEXT")
        return
    columns = {
        row["Field"]
        for row in execute("SHOW COLUMNS FROM users", fetch=True)
    }
    if "profile_image" not in columns:
        execute("ALTER TABLE users ADD COLUMN profile_image MEDIUMTEXT")


def ensure_song_album_column():
    if use_sqlite_backend():
        columns = {row["name"] for row in execute("PRAGMA table_info(songs)", fetch=True)}
        if "album" not in columns:
            execute("ALTER TABLE songs ADD COLUMN album VARCHAR(180) DEFAULT ''")
        return
    columns = {
        row["Field"]
        for row in execute("SHOW COLUMNS FROM songs", fetch=True)
    }
    if "album" not in columns:
        execute("ALTER TABLE songs ADD COLUMN album VARCHAR(180) DEFAULT '' AFTER artist")


def ensure_song_cover_column():
    if use_sqlite_backend():
        columns = {row["name"] for row in execute("PRAGMA table_info(songs)", fetch=True)}
        if "cover_url" not in columns:
            execute("ALTER TABLE songs ADD COLUMN cover_url TEXT")
        return
    columns = {
        row["Field"]
        for row in execute("SHOW COLUMNS FROM songs", fetch=True)
    }
    if "cover_url" not in columns:
        execute("ALTER TABLE songs ADD COLUMN cover_url TEXT AFTER album")


def seed_data():
    seed_users = list(SEED_USERS)
    if show_public_demo_account():
        seed_users.append(PUBLIC_DEMO_USER)
    else:
        execute("DELETE FROM users WHERE email=%s AND role='user'", (PUBLIC_DEMO_USER[1],))

    for name, email, password, role, mood, bio in seed_users:
        execute(
            """
            INSERT INTO users (name, email, password_hash, role, favorite_mood, bio)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name=VALUES(name),
                password_hash=VALUES(password_hash),
                role=VALUES(role),
                favorite_mood=VALUES(favorite_mood),
                bio=VALUES(bio)
            """,
            (name, email, password_hash(password), role, mood, bio),
        )
    admin = execute("SELECT id FROM users WHERE role='admin' LIMIT 1", fetch=True)[0]["id"]
    for title, album in TRACK_ALBUMS.items():
        execute("UPDATE songs SET album=%s WHERE title=%s", (album, title))
    existing_sources = {
        row["source_url"]
        for row in execute("SELECT source_url FROM songs", fetch=True)
    }
    rows = [
        (title, artist, TRACK_ALBUMS.get(title, ""), mood, genre, source_url, duration, energy, valence, admin)
        for title, artist, mood, genre, source_url, duration, energy, valence in SEED_SONGS
        if source_url not in existing_sources
    ]
    if rows:
        execute(
            """
            INSERT INTO songs
                (title, artist, album, mood, genre, source_url, duration_seconds, energy, valence, added_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            rows,
            many=True,
        )


@st.cache_data(ttl=300, show_spinner=False)
def songs_df(active_only=True):
    where = "WHERE s.is_active = TRUE" if active_only else ""
    rows = execute(
        f"""
        SELECT s.*, u.name AS added_by_name
        FROM songs s
        LEFT JOIN users u ON u.id = s.added_by
        {where}
        ORDER BY s.created_at DESC
        """,
        fetch=True,
    )
    return pd.DataFrame(rows)


def clear_cache():
    songs_df.clear()
    for cache_name in ("user_playlists", "playlist_songs", "saved_song_ids", "saved_songs", "user_history"):
        cached_func = globals().get(cache_name)
        if cached_func and hasattr(cached_func, "clear"):
            cached_func.clear()


def clear_history_cache():
    if hasattr(user_history, "clear"):
        user_history.clear()


def get_user_by_email(email):
    rows = execute("SELECT * FROM users WHERE email=%s", (email.strip().lower(),), fetch=True)
    return rows[0] if rows else None


def get_user_by_id(user_id):
    rows = execute("SELECT * FROM users WHERE id=%s", (user_id,), fetch=True)
    return rows[0] if rows else None


def create_user(name, email, password):
    try:
        execute(
            """
            INSERT INTO users (name, email, password_hash, role, favorite_mood)
            VALUES (%s, %s, %s, 'user', 'Happy')
            """,
            (name.strip(), email.strip().lower(), password_hash(password)),
        )
        return True, "Account created. You can sign in now."
    except pymysql.err.IntegrityError:
        return False, "That email is already registered."


def token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def remember_user(user, cookies):
    token = token_secrets.token_urlsafe(48)
    expires_at = datetime.now() + timedelta(days=AUTH_COOKIE_DAYS)
    execute(
        """
        INSERT INTO login_tokens (user_id, token_hash, expires_at)
        VALUES (%s, %s, %s)
        """,
        (user["id"], token_hash(token), expires_at.strftime("%Y-%m-%d %H:%M:%S")),
    )
    cookies.set(
        AUTH_COOKIE_NAME,
        token,
        path="/",
        expires=expires_at,
        max_age=AUTH_COOKIE_DAYS * 24 * 60 * 60,
        same_site="lax",
    )


def restore_remembered_user(cookies):
    if st.session_state.get("user"):
        return
    token = cookies.get(AUTH_COOKIE_NAME)
    if not token:
        return
    execute("DELETE FROM login_tokens WHERE expires_at < NOW()")
    rows = execute(
        """
        SELECT u.*
        FROM login_tokens lt
        JOIN users u ON u.id = lt.user_id
        WHERE lt.token_hash=%s AND lt.expires_at >= NOW()
        LIMIT 1
        """,
        (token_hash(token),),
        fetch=True,
    )
    if rows:
        st.session_state.user = rows[0]
    else:
        cookies.remove(AUTH_COOKIE_NAME, path="/", same_site="lax")


def clear_remembered_user(cookies):
    token = cookies.get(AUTH_COOKIE_NAME)
    if token:
        execute("DELETE FROM login_tokens WHERE token_hash=%s", (token_hash(token),))
    cookies.remove(AUTH_COOKIE_NAME, path="/", same_site="lax")


def login_user(email, password, expected_role=None):
    user = get_user_by_email(email)
    if not user or user["password_hash"] != password_hash(password):
        return False, "Invalid email or password."
    if expected_role and user["role"] != expected_role:
        return False, f"This account is registered as {user['role']}. Use the correct login tab."
    st.session_state.user = user
    st.session_state.show_login_animation = True
    return True, "Login successful."


def update_session_user():
    user_id = st.session_state.user["id"]
    rows = execute("SELECT * FROM users WHERE id=%s", (user_id,), fetch=True)
    if rows:
        st.session_state.user = rows[0]


def uploaded_image_to_data_url(uploaded_file):
    if not uploaded_file:
        return None
    if uploaded_file.size > 2 * 1024 * 1024:
        raise ValueError("Profile picture must be under 2 MB.")
    mime_type = uploaded_file.type or "image/png"
    encoded = base64.b64encode(uploaded_file.getvalue()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def profile_image_html(user, size=84):
    image = user.get("profile_image")
    if image:
        return (
            f'<img class="profile-avatar-img" src="{image}" '
            f'alt="{html.escape(user["name"])} profile picture" '
            f'style="width:{size}px;height:{size}px;" />'
        )
    initials = "".join(part[:1] for part in str(user["name"]).split()[:2]).upper() or "EW"
    return f'<div class="profile-avatar-fallback" style="width:{size}px;height:{size}px;">{html.escape(initials)}</div>'


def add_song(title, artist, mood, genre, source_url, duration, energy, valence, added_by, album="", cover_url=""):
    song_id = execute(
        """
        INSERT INTO songs (title, artist, album, cover_url, mood, genre, source_url, duration_seconds, energy, valence, added_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (title, artist, album, cover_url, mood, genre, source_url, duration, energy, valence, added_by),
    )
    clear_cache()
    return song_id


def song_by_source(source_url):
    rows = execute("SELECT * FROM songs WHERE source_url=%s LIMIT 1", (source_url,), fetch=True)
    return rows[0] if rows else None


def youtube_thumbnail_url(source_url):
    if not source_url:
        return ""
    parsed = urlparse(str(source_url))
    host = parsed.netloc.lower()
    video_id = ""
    if "youtube.com" in host:
        video_id = parse_qs(parsed.query).get("v", [""])[0]
    elif "youtu.be" in host:
        video_id = parsed.path.strip("/").split("/")[0]
    if not video_id:
        return ""
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


@st.cache_data(ttl=86400, show_spinner=False)
def resolved_cover_url(source_url):
    source = str(source_url or "").strip()
    if not source:
        return ""
    direct_cover = youtube_thumbnail_url(source)
    if direct_cover:
        return direct_cover
    if not source.startswith("ytsearch"):
        return ""
    options = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "default_search": "ytsearch",
        "socket_timeout": 4,
    }
    try:
        with YoutubeDL(options) as ydl:
            data = ydl.extract_info(source, download=False)
    except Exception:
        return ""
    entries = data.get("entries") or []
    item = entries[0] if entries else data
    thumbnails = item.get("thumbnails") or []
    if thumbnails:
        return thumbnails[-1].get("url") or ""
    thumbnail = item.get("thumbnail") or ""
    if thumbnail:
        return thumbnail
    video_id = item.get("id") or ""
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else ""


def ensure_online_song(result, user_id, mood):
    existing = song_by_source(result["source_url"])
    cover_url = result.get("cover_url") or youtube_thumbnail_url(result.get("source_url", ""))
    if existing:
        updates = []
        params = []
        if not existing["is_active"]:
            updates.append("is_active=TRUE")
        if cover_url and not existing.get("cover_url"):
            updates.append("cover_url=%s")
            params.append(cover_url)
        if updates:
            params.append(existing["id"])
            execute(f"UPDATE songs SET {', '.join(updates)} WHERE id=%s", params)
            clear_cache()
        return existing["id"]
    return add_song(
        result["title"],
        result["artist"],
        mood,
        "Online",
        result["source_url"],
        result["duration_seconds"],
        result["energy"],
        result["valence"],
        user_id,
        cover_url=cover_url,
    )


def remember_song_cover(source_url, cover_url):
    if not source_url or not cover_url:
        return
    try:
        execute(
            "UPDATE songs SET cover_url=%s WHERE source_url=%s AND (cover_url IS NULL OR cover_url='')",
            (cover_url, source_url),
        )
    except Exception:
        pass


def remove_song(song_id):
    execute("UPDATE songs SET is_active=FALSE WHERE id=%s", (song_id,))
    clear_cache()


def save_song(user_id, song_id):
    execute("INSERT IGNORE INTO saved_songs (user_id, song_id) VALUES (%s, %s)", (user_id, song_id))
    clear_cache()


def unsave_song(user_id, song_id):
    execute("DELETE FROM saved_songs WHERE user_id=%s AND song_id=%s", (user_id, song_id))
    clear_cache()


@st.cache_data(ttl=60, show_spinner=False)
def user_playlists(user_id):
    return execute(
        """
        SELECT p.*, COUNT(ps.song_id) AS song_count
        FROM playlists p
        LEFT JOIN playlist_songs ps ON ps.playlist_id = p.id
        WHERE p.user_id=%s
        GROUP BY p.id
        ORDER BY p.created_at DESC
        """,
        (user_id,),
        fetch=True,
    )


def create_playlist(user_id, name):
    cleaned = name.strip()
    if not cleaned:
        return False, "Playlist name is required."
    try:
        execute("INSERT INTO playlists (user_id, name) VALUES (%s, %s)", (user_id, cleaned))
        clear_cache()
        return True, "Playlist created."
    except pymysql.err.IntegrityError:
        return False, "You already have a playlist with that name."


def delete_playlist(user_id, playlist_id):
    execute("DELETE FROM playlists WHERE id=%s AND user_id=%s", (playlist_id, user_id))
    clear_cache()


def playlist_song_ids(playlist_id):
    rows = execute("SELECT song_id FROM playlist_songs WHERE playlist_id=%s", (playlist_id,), fetch=True)
    return {row["song_id"] for row in rows}


def add_song_to_playlist(user_id, playlist_id, song_id):
    rows = execute("SELECT id FROM playlists WHERE id=%s AND user_id=%s", (playlist_id, user_id), fetch=True)
    if not rows:
        return False, "Playlist not found."
    position_rows = execute(
        "SELECT COALESCE(MAX(position), 0) + 1 AS next_position FROM playlist_songs WHERE playlist_id=%s",
        (playlist_id,),
        fetch=True,
    )
    next_position = position_rows[0]["next_position"]
    execute(
        """
        INSERT IGNORE INTO playlist_songs (playlist_id, song_id, position)
        VALUES (%s, %s, %s)
        """,
        (playlist_id, song_id, next_position),
    )
    clear_cache()
    return True, "Added to playlist."


def remove_song_from_playlist(user_id, playlist_id, song_id):
    rows = execute("SELECT id FROM playlists WHERE id=%s AND user_id=%s", (playlist_id, user_id), fetch=True)
    if rows:
        execute("DELETE FROM playlist_songs WHERE playlist_id=%s AND song_id=%s", (playlist_id, song_id))
        clear_cache()


@st.cache_data(ttl=60, show_spinner=False)
def playlist_songs(user_id, playlist_id):
    rows = execute(
        """
        SELECT s.*, ps.position
        FROM playlists p
        JOIN playlist_songs ps ON ps.playlist_id = p.id
        JOIN songs s ON s.id = ps.song_id
        WHERE p.user_id=%s AND p.id=%s AND s.is_active=TRUE
        ORDER BY ps.position, ps.added_at
        """,
        (user_id, playlist_id),
        fetch=True,
    )
    return pd.DataFrame(rows)


def render_add_to_playlist_button(user, key_base, song_id_factory, button_slot=None):
    playlists = user_playlists(user["id"])
    button_slot = button_slot or st
    if not playlists:
        button_slot.button("Add to Playlist", key=f"add_playlist_disabled_{key_base}", disabled=True)
        return
    playlist_options = {f"{item['name']} ({item['song_count']})": item["id"] for item in playlists}
    picker_key = f"show_playlist_picker_{key_base}"
    if button_slot.button("Add to Playlist", key=f"add_playlist_{key_base}"):
        if len(playlists) == 1:
            playlist_id = int(playlists[0]["id"])
            song_id = song_id_factory()
            ok, message = add_song_to_playlist(user["id"], playlist_id, int(song_id))
            st.success(message) if ok else st.error(message)
            st.rerun()
        st.session_state[picker_key] = True
    if st.session_state.get(picker_key):
        selected_playlist = button_slot.selectbox(
            "Choose playlist",
            list(playlist_options.keys()),
            key=f"playlist_select_{key_base}",
        )
        c1, c2 = button_slot.columns([1, 1])
        if c1.button("Confirm Add", key=f"confirm_playlist_{key_base}"):
            song_id = song_id_factory()
            ok, message = add_song_to_playlist(user["id"], playlist_options[selected_playlist], int(song_id))
            st.session_state[picker_key] = False
            st.success(message) if ok else st.error(message)
            st.rerun()
        if c2.button("Cancel", key=f"cancel_playlist_{key_base}"):
            st.session_state[picker_key] = False
            st.rerun()


def log_listen(user_id, song_id, mood, seconds):
    execute(
        """
        INSERT INTO listening_history (user_id, song_id, mood, listened_seconds)
        VALUES (%s, %s, %s, %s)
        """,
        (user_id, song_id, mood, seconds),
    )
    clear_history_cache()


def set_current_player(player_key):
    st.session_state.current_player_key = player_key


def queue_track(title, artist, source_url, duration_seconds=180):
    return {
        "title": str(title),
        "artist": str(artist),
        "url": str(source_url),
        "duration_seconds": int(duration_seconds or 180),
    }


def queue_from_rows(rows):
    tracks = []
    for _, row in rows.iterrows():
        tracks.append(
            queue_track(
                row.get("title", "Untitled"),
                row.get("artist", "Unknown Artist"),
                row.get("source_url", ""),
                row.get("duration_seconds", 180),
            )
        )
    return tracks


def set_play_queue(tracks, start_index=0):
    cleaned = [track for track in tracks if track.get("url")]
    if not cleaned:
        st.session_state.pop("play_queue", None)
        st.session_state.pop("play_queue_start", None)
        return
    st.session_state.play_queue = cleaned
    st.session_state.play_queue_start = max(0, min(int(start_index), len(cleaned) - 1))


def is_current_player(player_key):
    return st.session_state.get("current_player_key") == player_key


def song_icon_label(player_key):
    return "▶ ♪" if is_current_player(player_key) else "♪"


def render_now_playing(title, artist):
    st.markdown(
        f"""
        <div class="now-playing">
            Now playing
            <span>{html.escape(str(title))} - {html.escape(str(artist))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def boosted_audio_player(url, key_base, boost=1.0, autoplay=True):
    safe_url = html.escape(str(url), quote=True)
    safe_id = re.sub(r"[^A-Za-z0-9_-]+", "_", str(key_base))[:80]
    autoplay_attr = "autoplay" if autoplay else ""
    components.html(
        f"""
        <div class="boosted-player">
            <audio id="audio_{safe_id}" controls {autoplay_attr} src="{safe_url}" style="width:100%;"></audio>
            <div class="boosted-row">
                <span>Volume</span>
                <input id="gain_{safe_id}" type="range" min="0" max="1" step="0.05" value="{boost}" />
                <strong id="gain_label_{safe_id}">{int(boost * 100)}%</strong>
            </div>
        </div>
        <script>
        (() => {{
            const audio = document.getElementById("audio_{safe_id}");
            const slider = document.getElementById("gain_{safe_id}");
            const label = document.getElementById("gain_label_{safe_id}");
            audio.volume = 1.0;
            slider.addEventListener("input", () => {{
                audio.volume = Number(slider.value);
                label.textContent = Math.round(audio.volume * 100) + "%";
            }});
        }})();
        </script>
        """,
        height=116,
    )


def is_audio_url(url):
    return urlparse(url).path.lower().endswith((".mp3", ".wav", ".ogg", ".m4a"))


def is_online_audio_source(url):
    source = str(url).lower()
    parsed = urlparse(source)
    return source.startswith("ytsearch") or "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc


def audio_filename(title, url):
    ext = os.path.splitext(urlparse(url).path)[1].lower() or ".mp3"
    if ext not in {".mp3", ".wav", ".ogg", ".m4a"}:
        ext = ".mp3"
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(title)).strip("_") or "mood_tunes_song"
    return f"{cleaned}{ext}"


def audio_mime_type(url):
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    return {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
    }.get(ext, "audio/mpeg")


@st.cache_data(ttl=3600, show_spinner=False)
def download_audio_bytes(url):
    request = urllib.request.Request(url, headers={"User-Agent": "EcoWavE/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def render_download_audio_control(title, url, key_base, button_slot=None):
    button_slot = button_slot or st
    if not is_audio_url(str(url)):
        return
    state_key = f"download_data_{key_base}"
    if state_key in st.session_state:
        button_slot.download_button(
            "Save Offline",
            data=st.session_state[state_key],
            file_name=audio_filename(title, str(url)),
            mime=audio_mime_type(str(url)),
            key=f"download_audio_{key_base}",
        )
        return
    if button_slot.button("Download", key=f"prepare_download_{key_base}"):
        with st.spinner("Preparing offline file..."):
            try:
                st.session_state[state_key] = download_audio_bytes(str(url))
                st.rerun()
            except Exception as exc:
                st.error(f"Download unavailable: {exc}")


def render_playlist_player(tracks, playlist_name):
    audio_tracks = []
    skipped_tracks = []
    online_tracks = []
    playlist_signature = hashlib.sha1(
        "|".join(str(row["id"]) for _, row in tracks.iterrows()).encode("utf-8")
    ).hexdigest()[:12]
    prepared_key = f"prepared_playlist_audio_{playlist_signature}"
    for _, row in tracks.iterrows():
        source_url = str(row["source_url"])
        track = {
            "title": str(row["title"]),
            "artist": str(row["artist"]),
            "url": source_url,
        }
        if is_audio_url(source_url):
            audio_tracks.append(track)
        elif is_online_audio_source(source_url):
            online_tracks.append(track)
        else:
            skipped_tracks.append(str(row["title"]))

    audio_tracks.extend(st.session_state.get(prepared_key, []))
    if online_tracks and prepared_key not in st.session_state:
        st.caption(f"{len(online_tracks)} online playlist song needs preparation before autoplay.")
        if st.button("Prepare Online Songs", key=f"prepare_online_playlist_{playlist_signature}"):
            prepared_tracks = []
            with st.spinner("Preparing online playlist songs..."):
                for track in online_tracks:
                    try:
                        audio_url = online_audio_stream_url(track["url"])
                    except Exception:
                        audio_url = None
                    if audio_url:
                        prepared_tracks.append({**track, "url": audio_url})
                    else:
                        skipped_tracks.append(track["title"])
            st.session_state[prepared_key] = prepared_tracks
            st.rerun()
    if not audio_tracks:
        st.info("No playlist songs are ready for automatic playback yet.")
        return
    if skipped_tracks:
        st.caption(f"{len(skipped_tracks)} playlist song could not be prepared for autoplay.")
    payload = json.dumps(audio_tracks)
    safe_name = html.escape(playlist_name)
    components.html(
        f"""
        <div class="playlist-player">
            <div class="playlist-player-title">Playlist Player</div>
            <div id="playlist-now">Ready: {html.escape(audio_tracks[0]["title"])} - {html.escape(audio_tracks[0]["artist"])}</div>
            <audio id="playlist-audio" controls style="width:100%; margin-top:12px;"></audio>
            <div style="display:flex; align-items:center; gap:10px; margin-top:10px; color:#b3b3b3; font-size:13px;">
                <span>Volume</span>
                <input id="playlist-gain" type="range" min="0" max="1" step="0.05" value="1" style="flex:1;">
                <strong id="playlist-gain-label" style="color:#fff;">100%</strong>
            </div>
            <div style="display:flex; gap:8px; margin-top:12px;">
                <button id="playlist-start" type="button">Start Playlist</button>
                <button id="playlist-prev" type="button">Previous</button>
                <button id="playlist-next" type="button">Next</button>
            </div>
            <div id="playlist-count" style="margin-top:10px; color:#d6c8bd; font-size:13px;"></div>
        </div>
        <script>
        const tracks = {payload};
        let index = 0;
        let errorSkips = 0;
        const audio = document.getElementById("playlist-audio");
        const gainSlider = document.getElementById("playlist-gain");
        const gainLabel = document.getElementById("playlist-gain-label");
        const now = document.getElementById("playlist-now");
        const count = document.getElementById("playlist-count");
        audio.volume = 1.0;
        gainSlider.addEventListener("input", () => {{
            audio.volume = Number(gainSlider.value);
            gainLabel.textContent = Math.round(audio.volume * 100) + "%";
        }});
        count.textContent = "{safe_name} - " + tracks.length + " tracks ready";
        function loadTrack(nextIndex, shouldPlay = true) {{
            index = (nextIndex + tracks.length) % tracks.length;
            audio.src = tracks[index].url;
            now.textContent = tracks[index].title + " - " + tracks[index].artist;
            count.textContent = "{safe_name} - Track " + (index + 1) + " of " + tracks.length;
            if (shouldPlay) {{
                audio.play().catch(() => {{}});
            }}
        }}
        document.getElementById("playlist-start").onclick = () => loadTrack(index, true);
        document.getElementById("playlist-next").onclick = () => loadTrack(index + 1);
        document.getElementById("playlist-prev").onclick = () => loadTrack(index - 1);
        audio.addEventListener("playing", () => {{ errorSkips = 0; }});
        audio.addEventListener("error", () => {{
            errorSkips += 1;
            if (errorSkips < tracks.length) {{
                loadTrack(index + 1);
            }} else {{
                count.textContent = "Could not play the prepared playlist audio.";
            }}
        }});
        audio.addEventListener("ended", () => loadTrack(index + 1));
        loadTrack(0, false);
        </script>
        """,
        height=190,
    )


@st.cache_data(ttl=1800, show_spinner=False)
def online_audio_stream_url(url):
    memory_key = f"audio_stream_{hashlib.sha256(str(url).encode('utf-8')).hexdigest()}"
    if memory_key in st.session_state:
        return st.session_state[memory_key]
    source_hash = hashlib.sha256(str(url).encode("utf-8")).hexdigest()
    cached = execute(
        """
        SELECT audio_url
        FROM audio_stream_cache
        WHERE source_hash=%s AND expires_at > NOW()
        LIMIT 1
        """,
        (source_hash,),
        fetch=True,
    )
    if cached:
        st.session_state[memory_key] = cached[0]["audio_url"]
        return cached[0]["audio_url"]
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "noplaylist": True,
        "socket_timeout": 8,
        "retries": 1,
        "fragment_retries": 1,
        "extractor_retries": 1,
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("entries"):
        info = next((item for item in info["entries"] if item), info)
    if info.get("url"):
        audio_url = info["url"]
        st.session_state[memory_key] = audio_url
        cache_audio_stream_url(source_hash, url, audio_url)
        return audio_url
    audio_formats = [
        item
        for item in info.get("formats", [])
        if item.get("url") and (item.get("acodec") or "none") != "none"
    ]
    if not audio_formats:
        return None
    audio_formats.sort(key=lambda item: item.get("abr") or item.get("tbr") or 0, reverse=True)
    audio_url = audio_formats[0]["url"]
    st.session_state[memory_key] = audio_url
    cache_audio_stream_url(source_hash, url, audio_url)
    return audio_url


def cache_audio_stream_url(source_hash, source_url, audio_url):
    expires_at = datetime.now() + timedelta(hours=3)
    execute(
        """
        INSERT INTO audio_stream_cache (source_hash, source_url, audio_url, expires_at)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            source_url=VALUES(source_url),
            audio_url=VALUES(audio_url),
            expires_at=VALUES(expires_at)
        """,
        (source_hash, source_url, audio_url, expires_at.strftime("%Y-%m-%d %H:%M:%S")),
    )


@st.cache_data(ttl=60, show_spinner=False)
def user_history(user_id):
    rows = execute(
        """
        SELECT h.*, s.title, s.artist, s.album, s.cover_url, s.genre, s.source_url, s.duration_seconds, s.energy, s.valence, s.is_active
        FROM listening_history h
        JOIN songs s ON s.id = h.song_id
        WHERE h.user_id=%s
        ORDER BY h.listened_at DESC
        """,
        (user_id,),
        fetch=True,
    )
    return pd.DataFrame(rows)


@st.cache_data(ttl=60, show_spinner=False)
def saved_song_ids(user_id):
    rows = execute("SELECT song_id FROM saved_songs WHERE user_id=%s", (user_id,), fetch=True)
    return {row["song_id"] for row in rows}


@st.cache_data(ttl=60, show_spinner=False)
def saved_songs(user_id):
    rows = execute(
        """
        SELECT s.*
        FROM saved_songs ss
        JOIN songs s ON s.id = ss.song_id
        WHERE ss.user_id=%s AND s.is_active=TRUE
        ORDER BY ss.saved_at DESC
        """,
        (user_id,),
        fetch=True,
    )
    return pd.DataFrame(rows)


def all_history():
    rows = execute(
        """
        SELECT h.*, u.name AS user_name, s.title, s.artist
        FROM listening_history h
        JOIN users u ON u.id = h.user_id
        JOIN songs s ON s.id = h.song_id
        ORDER BY h.listened_at DESC
        """,
        fetch=True,
    )
    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def recommend_songs(df, selected_mood, search_text="", favorite_mood="Happy", top_n=None):
    if df.empty:
        return df
    work = df.copy()
    search_text = search_text.strip()
    query = f"{selected_mood} {favorite_mood} {search_text}".strip()
    corpus = (
        work["title"].fillna("")
        + " "
        + work["artist"].fillna("")
        + " "
        + work["mood"].fillna("")
        + " "
        + work["genre"].fillna("")
    )
    scores = tfidf_scores(corpus.tolist(), query)
    work["ml_score"] = scores
    work["mood_match"] = (work["mood"] == selected_mood).astype(int)
    ranked = work.sort_values(["mood_match", "ml_score", "energy"], ascending=False)
    if top_n:
        return ranked.head(top_n)
    return ranked


def tokenize(text):
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in STOP_WORDS]


@st.cache_data(ttl=300, show_spinner=False)
def tfidf_scores(documents, query):
    tokenized_docs = [tokenize(document) for document in documents]
    query_tokens = tokenize(query)
    if not query_tokens:
        return [0.0] * len(documents)

    doc_count = len(tokenized_docs)
    document_frequency = Counter()
    for tokens in tokenized_docs:
        document_frequency.update(set(tokens))

    def vector(tokens):
        counts = Counter(tokens)
        total = sum(counts.values()) or 1
        return {
            token: (count / total) * (math.log((1 + doc_count) / (1 + document_frequency[token])) + 1)
            for token, count in counts.items()
        }

    query_vector = vector(query_tokens)
    query_norm = math.sqrt(sum(value * value for value in query_vector.values()))
    if query_norm == 0:
        return [0.0] * len(documents)

    scores = []
    for tokens in tokenized_docs:
        doc_vector = vector(tokens)
        doc_norm = math.sqrt(sum(value * value for value in doc_vector.values()))
        if doc_norm == 0:
            scores.append(0.0)
            continue
        dot_product = sum(query_vector.get(token, 0.0) * doc_vector.get(token, 0.0) for token in query_vector)
        scores.append(dot_product / (query_norm * doc_norm))
    return scores


@st.cache_data(ttl=900, show_spinner=False)
def online_music_search(search_text, limit=5):
    search_text = search_text.strip()
    if not search_text:
        return []
    options = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "default_search": "ytsearch",
    }
    with YoutubeDL(options) as ydl:
        data = ydl.extract_info(f"ytsearch{limit}:{search_text} song", download=False)
    results = []
    for item in data.get("entries", []) or []:
        video_id = item.get("id")
        if not video_id:
            continue
        url = item.get("url") or f"https://www.youtube.com/watch?v={video_id}"
        if not url.startswith("http"):
            url = f"https://www.youtube.com/watch?v={video_id}"
        thumbnails = item.get("thumbnails") or []
        thumbnail = item.get("thumbnail") or ""
        if thumbnails:
            thumbnail = thumbnails[-1].get("url") or thumbnail
        if not thumbnail:
            thumbnail = youtube_thumbnail_url(url)
        duration = int(item.get("duration") or 180)
        results.append(
            {
                "id": video_id,
                "title": item.get("title") or "Untitled track",
                "artist": item.get("uploader") or item.get("channel") or "YouTube",
                "source_url": url,
                "cover_url": thumbnail,
                "duration_seconds": duration,
                "energy": 60,
                "valence": 60,
            }
        )
    return results


def render_online_results(search_text, user, mood, area):
    if not search_text.strip():
        return
    st.subheader("Online Music Results")
    with st.spinner("Searching songs inside the app..."):
        try:
            results = online_music_search(search_text)
        except Exception as exc:
            st.error("Online music search failed. Check your internet connection and try again.")
            st.caption(str(exc))
            return
    if not results:
        st.info("No online songs found for this search.")
        return
    online_queue = [
        queue_track(result["title"], result["artist"], result["source_url"], result.get("duration_seconds", 180))
        for result in results
    ]
    for position, result in enumerate(results, start=1):
        key_base = f"{area}_{user['id']}_{result['id']}"
        player_key = f"online_{area}_{result['id']}"
        duration = format_duration(result.get("duration_seconds", 180))
        st.markdown(
            f"""
            <div class="song-card">
                <div class="track-row">
                    <div class="track-index">{position}</div>
                    <div class="album-mark">{song_logo_html(result["source_url"], result["title"], result["artist"], mood, result.get("cover_url", ""))}</div>
                    <div class="track-main">
                        <h3>{html.escape(str(result['title']))}</h3>
                        <div class="meta">
                            <span>{html.escape(str(result['artist']))}</span>
                            <span>YouTube result</span>
                            <span class="pill">{html.escape(str(mood))}</span>
                        </div>
                    </div>
                    <div class="track-album">Online Music</div>
                    <div class="track-duration">{duration}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        action_cols = st.columns([9, 1])
        play_label = song_icon_label(player_key)
        if action_cols[0].button(play_label, key=f"play_online_{key_base}", use_container_width=True):
            song_id = ensure_online_song(result, user["id"], mood)
            set_current_player(player_key)
            set_play_queue(online_queue, position - 1)
            log_listen(user["id"], song_id, mood, result["duration_seconds"])
            st.success("Played and added to your mood history.")
            st.rerun()
        menu = action_cols[1].popover("...", use_container_width=True)
        if menu.button("Save", key=f"save_online_{key_base}", use_container_width=True):
            song_id = ensure_online_song(result, user["id"], mood)
            save_song(user["id"], song_id)
            st.success("Saved to your library.")
            st.rerun()
        render_add_to_playlist_button(
            user,
            f"online_{key_base}",
            lambda result=result, user=user, mood=mood: ensure_online_song(result, user["id"], mood),
            menu,
        )
        render_download_audio_control(result["title"], result["source_url"], f"online_{key_base}", menu)
        if is_current_player(player_key):
            render_now_playing(result["title"], result["artist"])
            source_view(result["source_url"])


def source_view(url):
    queue = st.session_state.get("play_queue") or []
    if queue:
        for index, track in enumerate(queue):
            if str(track.get("url")) == str(url):
                render_auto_queue_player(queue, st.session_state.get("play_queue_start", index))
                return

    parsed = urlparse(url)
    media_path = parsed.path.lower()
    if media_path.endswith((".mp3", ".wav", ".ogg", ".m4a")):
        st.audio(url, autoplay=True)
    elif is_online_audio_source(url):
        with st.spinner("Starting audio..."):
            try:
                audio_url = online_audio_stream_url(url)
            except Exception as exc:
                st.error("Could not start online audio automatically.")
                st.caption(str(exc))
                st.link_button("Open music source", url)
                return
        if audio_url:
            st.audio(audio_url, autoplay=True)
            st.caption("Playback restored. Set browser/device volume high for the loudest output.")
        else:
            st.error("Could not find a playable audio stream for this song.")
            st.link_button("Open music source", url)
    else:
        st.link_button("Open music source", url)


def playable_url(source_url):
    source_url = str(source_url)
    if is_audio_url(source_url):
        return source_url
    if is_online_audio_source(source_url):
        return online_audio_stream_url(source_url)
    return ""


def render_auto_queue_player(queue, start_index=0):
    playable_tracks = []
    skipped = []
    with st.spinner("Preparing queue..."):
        for track in queue[:30]:
            try:
                audio_url = playable_url(track.get("url", ""))
            except Exception:
                audio_url = ""
            if audio_url:
                playable_tracks.append(
                    {
                        "title": track.get("title", "Untitled"),
                        "artist": track.get("artist", "Unknown Artist"),
                        "url": audio_url,
                    }
                )
            else:
                skipped.append(track.get("title", "Unknown song"))

    if not playable_tracks:
        st.error("Could not prepare this queue for playback.")
        return

    start_index = max(0, min(int(start_index or 0), len(playable_tracks) - 1))
    payload = json.dumps(playable_tracks)
    player_id = hashlib.sha1(
        "|".join(track["url"] for track in playable_tracks).encode("utf-8")
    ).hexdigest()[:12]
    components.html(
        f"""
        <div class="playlist-player queue-player">
            <div class="playlist-player-title">Queue Player</div>
            <div id="queue-now-{player_id}">Ready</div>
            <audio id="queue-audio-{player_id}" controls autoplay style="width:100%; margin-top:12px;"></audio>
            <div style="display:flex; align-items:center; gap:10px; margin-top:10px; color:#b3b3b3; font-size:13px;">
                <span>Volume</span>
                <input id="queue-gain-{player_id}" type="range" min="0" max="1" step="0.05" value="1" style="flex:1;">
                <strong id="queue-gain-label-{player_id}" style="color:#fff;">100%</strong>
            </div>
            <div style="display:flex; gap:8px; margin-top:12px;">
                <button id="queue-prev-{player_id}" type="button">Previous</button>
                <button id="queue-next-{player_id}" type="button">Next</button>
            </div>
            <div id="queue-count-{player_id}" style="margin-top:10px; color:#b3b3b3; font-size:13px;"></div>
        </div>
        <script>
        (() => {{
            const tracks = {payload};
            let index = {start_index};
            let errorSkips = 0;
            const audio = document.getElementById("queue-audio-{player_id}");
            const gainSlider = document.getElementById("queue-gain-{player_id}");
            const gainLabel = document.getElementById("queue-gain-label-{player_id}");
            const now = document.getElementById("queue-now-{player_id}");
            const count = document.getElementById("queue-count-{player_id}");
            audio.volume = 1.0;
            gainSlider.addEventListener("input", () => {{
                audio.volume = Number(gainSlider.value);
                gainLabel.textContent = Math.round(audio.volume * 100) + "%";
            }});
            function loadTrack(nextIndex, shouldPlay = true) {{
                index = (nextIndex + tracks.length) % tracks.length;
                audio.src = tracks[index].url;
                now.textContent = tracks[index].title + " - " + tracks[index].artist;
                count.textContent = "Track " + (index + 1) + " of " + tracks.length;
                if (shouldPlay) {{
                    audio.play().catch(() => {{}});
                }}
            }}
            document.getElementById("queue-next-{player_id}").onclick = () => loadTrack(index + 1);
            document.getElementById("queue-prev-{player_id}").onclick = () => loadTrack(index - 1);
            audio.addEventListener("playing", () => {{ errorSkips = 0; }});
            audio.addEventListener("ended", () => loadTrack(index + 1));
            audio.addEventListener("error", () => {{
                errorSkips += 1;
                if (errorSkips < tracks.length) {{
                    loadTrack(index + 1);
                }} else {{
                    count.textContent = "Could not play the prepared queue.";
                }}
            }});
            loadTrack(index, true);
        }})();
        </script>
        """,
        height=190,
    )
    if skipped:
        st.caption(f"{len(skipped)} song(s) could not be prepared for this queue.")


def format_duration(seconds):
    try:
        total = max(0, int(seconds or 0))
    except (TypeError, ValueError):
        total = 0
    if total <= 0:
        total = 180
    return f"{total // 60}:{total % 60:02d}"


def song_logo_html(source_url, title="", artist="", mood="", cover_url=""):
    cover = cover_url or resolved_cover_url(source_url)
    if cover and not cover_url:
        remember_song_cover(source_url, cover)
    if cover:
        safe_cover = html.escape(str(cover), quote=True)
        safe_title = html.escape(str(title or "Song artwork"), quote=True)
        return f'<img class="album-art real-cover" src="{safe_cover}" alt="{safe_title} cover art" loading="lazy" />'

    palette = [
        ("#29f0c0", "#ffd166", "#ff4d6d"),
        ("#5aa9e6", "#29f0c0", "#ffd166"),
        ("#ff4d6d", "#ffd166", "#7bdff2"),
        ("#b8f7d4", "#5aa9e6", "#ef6f9f"),
        ("#f8c14a", "#ff6b6b", "#2dd4bf"),
    ]
    seed = sum(ord(ch) for ch in f"{artist}{title}{mood}") or 1
    c1, c2, c3 = palette[seed % len(palette)]
    words = str(artist or title or "EcoWavE").split()
    initials = "".join(word[:1] for word in words[:2]).upper() or "EW"
    source_tag = "ON" if is_online_audio_source(source_url) else "EW"
    return f"""
        <div class="album-art creative-cover" style="--cover-a:{c1};--cover-b:{c2};--cover-c:{c3};">
            <div class="cover-ring"></div>
            <div class="cover-initials">{html.escape(initials)}</div>
            <div class="cover-tag">{source_tag}</div>
        </div>
    """


def hero(user):
    user_name = html.escape(user["name"])
    logo_html = logo_img_html("hero-logo")
    st.markdown(
        f"""
        <div class="hero">
            <div>
                <div class="brand-lockup">
                    {logo_html}
                    <div class="brand-copy">
                        <div class="brand-name">{APP_TITLE}</div>
                        <div class="brand-subtitle">Mood aware music console</div>
                    </div>
                </div>
                <h1>{APP_TITLE}</h1>
                <p>Welcome, {user_name}. Search any track, play online results, save favorites, and let the recommendation model shape the next queue.</p>
            </div>
            <div class="hero-deck">
                <div class="deck-title">Live mood signal</div>
                <div class="visualizer">
                    <span></span><span></span><span></span><span></span>
                    <span></span><span></span><span></span><span></span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_row(user):
    history = user_history(user["id"])
    saved = saved_songs(user["id"])
    total_minutes = 0 if history.empty else int(history["listened_seconds"].sum() / 60)
    top_mood = "No plays yet" if history.empty else history.groupby("mood")["listened_seconds"].sum().idxmax()
    c1, c2, c3 = st.columns(3)
    for col, label, value in [
        (c1, "Listening minutes", total_minutes),
        (c2, "Saved songs", len(saved)),
        (c3, "Top mood", top_mood),
    ]:
        col.markdown(
            f'<div class="metric-card"><div class="label">{label}</div><div class="value">{value}</div></div>',
            unsafe_allow_html=True,
        )


def render_song_card(row, user, allow_remove=False, area="library", position=1, queue_tracks=None, saved_ids=None):
    if saved_ids is None:
        saved_ids = saved_song_ids(user["id"])
    key_base = f"{area}_{user['id']}_{int(row['id'])}"
    player_key = f"local_{area}_{int(row['id'])}"
    title = html.escape(str(row["title"]))
    artist = html.escape(str(row["artist"]))
    album = html.escape(str(row.get("album") or "Single"))
    genre = html.escape(str(row["genre"]))
    mood = html.escape(str(row["mood"]))
    duration = format_duration(row.get("duration_seconds", 180))
    with st.container():
        st.markdown(
            f"""
            <div class="song-card">
                <div class="track-row">
                    <div class="track-index">{position}</div>
                    <div class="album-mark">{song_logo_html(row["source_url"], row["title"], row["artist"], row["mood"], row.get("cover_url", ""))}</div>
                    <div class="track-main">
                        <h3>{title}</h3>
                        <div class="meta">
                            <span>{artist}</span>
                            <span>{genre}</span>
                            <span class="pill">{mood}</span>
                        </div>
                    </div>
                    <div class="track-album">{album}</div>
                    <div class="track-duration">{duration}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        minutes = max(1, int(row.get("duration_seconds", 180) / 60))
        song_id = int(row["id"])
        action_cols = st.columns([9, 1])
        play_label = song_icon_label(player_key)
        if action_cols[0].button(play_label, key=f"play_{key_base}", use_container_width=True):
            set_current_player(player_key)
            set_play_queue(queue_tracks or [queue_track(row["title"], row["artist"], row["source_url"], row.get("duration_seconds", 180))], position - 1)
            log_listen(user["id"], song_id, row["mood"], int(row.get("duration_seconds", 180)))
            st.success(f"Added {minutes} minutes to {row['mood']} history.")
            st.rerun()
        menu = action_cols[1].popover("...", use_container_width=True)
        if song_id in saved_ids:
            if menu.button("Unsave", key=f"unsave_{key_base}", use_container_width=True):
                unsave_song(user["id"], song_id)
                st.rerun()
        else:
            if menu.button("Save", key=f"save_{key_base}", use_container_width=True):
                save_song(user["id"], song_id)
                st.rerun()
        if allow_remove:
            if menu.button("Remove", key=f"remove_{key_base}", use_container_width=True):
                remove_song(song_id)
                st.warning("Song removed from active library.")
                st.rerun()
        render_add_to_playlist_button(user, key_base, lambda song_id=song_id: song_id, menu)
        render_download_audio_control(row["title"], row["source_url"], key_base, menu)
        if is_current_player(player_key):
            render_now_playing(row["title"], row["artist"])
            source_view(row["source_url"])


def render_song_list(rows, user, area, empty_message="No songs found.", initial_limit=12, allow_remove=False):
    if rows.empty:
        st.info(empty_message)
        return
    limit_key = f"{area}_visible_limit"
    if limit_key not in st.session_state:
        st.session_state[limit_key] = initial_limit
    visible_count = min(int(st.session_state[limit_key]), len(rows))
    st.caption(f"Showing {visible_count} of {len(rows)} songs")
    visible_rows = rows.head(visible_count)
    queue_tracks = queue_from_rows(visible_rows)
    saved_ids = saved_song_ids(user["id"])
    for position, (_, row) in enumerate(visible_rows.iterrows(), start=1):
        render_song_card(
            row,
            user,
            allow_remove=allow_remove,
            area=area,
            position=position,
            queue_tracks=queue_tracks,
            saved_ids=saved_ids,
        )
    if visible_count < len(rows):
        if st.button("Show More Songs", key=f"{area}_show_more", use_container_width=True):
            st.session_state[limit_key] = visible_count + initial_limit
            st.rerun()


def add_music_form(user, title="Add Music"):
    with st.form(f"music_form_{title.replace(' ', '_')}"):
        st.subheader(title)
        c1, c2 = st.columns(2)
        song_title = c1.text_input("Song title")
        artist = c2.text_input("Artist")
        album = c1.text_input("Album", placeholder="Album or single name")
        mood = c1.selectbox("Mood", MOODS)
        genre = c2.text_input("Genre", value="Pop")
        source_url = st.text_input("Music source URL", placeholder="Direct mp3, YouTube, Spotify, SoundCloud, etc.")
        c3, c4, c5 = st.columns(3)
        duration = c3.number_input("Duration seconds", min_value=20, max_value=3600, value=180)
        energy = c4.slider("Energy", 0, 100, 55)
        valence = c5.slider("Positive feeling", 0, 100, 65)
        submitted = st.form_submit_button("Add to library")
        if submitted:
            if not song_title or not artist or not source_url:
                st.error("Song title, artist, and source URL are required.")
            else:
                add_song(song_title, artist, mood, genre, source_url, int(duration), energy, valence, user["id"], album=album)
                st.success("Music added successfully.")
                st.rerun()


def history_section(user):
    st.markdown(
        """
        <h2><span class="history-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2.2">
            <path d="M3 12a9 9 0 1 0 3-6.7"/>
            <path d="M3 4v6h6"/>
            <path d="M12 7v5l4 2"/>
        </svg>
        </span>Mood History</h2>
        """,
        unsafe_allow_html=True,
    )
    history = user_history(user["id"])
    if history.empty:
        st.info("Play a song to build your mood history chart.")
        return
    mood_summary = (
        history.groupby("mood", as_index=False)["listened_seconds"].sum().assign(
            minutes=lambda x: (x["listened_seconds"] / 60).round(1)
        )
    )
    fig = px.bar(
        mood_summary,
        x="mood",
        y="minutes",
        color="mood",
        title="Time listened by mood",
        color_discrete_sequence=["#18a999", "#f45d48", "#d45087", "#4c78a8", "#f6c85f", "#72b7b2", "#9d755d"],
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,.55)", title_font_size=20)
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Play From History")
    visible_history = history.head(10)
    history_queue = queue_from_rows(visible_history)
    for position, (_, row) in enumerate(visible_history.iterrows(), start=1):
        player_key = f"history_{user['id']}_{int(row['id'])}_{int(row['song_id'])}"
        duration = format_duration(row.get("duration_seconds", 180))
        st.markdown(
            f"""
            <div class="song-card history-card">
                <div class="track-row">
                    <div class="track-index">{position}</div>
                    <div class="album-mark">{song_logo_html(row["source_url"], row["title"], row["artist"], row["mood"], row.get("cover_url", ""))}</div>
                    <div class="track-main">
                        <h3>{html.escape(str(row['title']))}</h3>
                        <div class="meta">
                            <span>{html.escape(str(row['artist']))}</span>
                            <span>Listened {html.escape(str(row['listened_at']))}</span>
                            <span class="pill">{html.escape(str(row['mood']))}</span>
                        </div>
                    </div>
                    <div class="track-album">{html.escape(str(row.get('album') or 'Single'))}</div>
                    <div class="track-duration">{duration}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        action_cols = st.columns([9, 1])
        play_label = song_icon_label(player_key)
        if action_cols[0].button(play_label, key=f"play_history_{int(row['id'])}_{int(row['song_id'])}", use_container_width=True):
            set_current_player(player_key)
            set_play_queue(history_queue, position - 1)
            log_listen(user["id"], int(row["song_id"]), row["mood"], int(row.get("duration_seconds", 180)))
            st.rerun()
        menu = action_cols[1].popover("...", use_container_width=True)
        if menu.button("Save", key=f"save_history_{int(row['id'])}_{int(row['song_id'])}", use_container_width=True):
            save_song(user["id"], int(row["song_id"]))
            st.success("Saved to your library.")
            st.rerun()
        render_add_to_playlist_button(
            user,
            f"history_{int(row['id'])}_{int(row['song_id'])}",
            lambda row=row: int(row["song_id"]),
            menu,
        )
        render_download_audio_control(row["title"], row["source_url"], f"history_{int(row['id'])}_{int(row['song_id'])}", menu)
        c2.caption(f"{row['artist']} - {row.get('album') or 'Single'}")
        if is_current_player(player_key):
            render_now_playing(row["title"], row["artist"])
            source_view(row["source_url"])


def profile_section(user):
    st.markdown('<div class="profile-panel">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="profile-head">
            {profile_image_html(user, 96)}
            <div>
                <h2>{html.escape(user["name"])}</h2>
                <p>{html.escape(user["role"].title())} account · Favorite mood: {html.escape(user.get("favorite_mood") or "Happy")}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("profile_form"):
        name = st.text_input("Name", value=user["name"])
        favorite_mood = st.selectbox("Favorite mood", MOODS, index=MOODS.index(user.get("favorite_mood") or "Happy"))
        bio = st.text_area("Bio", value=user.get("bio") or "", max_chars=255)
        profile_file = st.file_uploader("Profile picture", type=["png", "jpg", "jpeg", "webp"])
        remove_picture = st.checkbox("Remove current profile picture", value=False)
        submitted = st.form_submit_button("Update profile")
        if submitted:
            profile_image = user.get("profile_image")
            if remove_picture:
                profile_image = None
            elif profile_file:
                try:
                    profile_image = uploaded_image_to_data_url(profile_file)
                except ValueError as exc:
                    st.error(str(exc))
                    st.stop()
            execute(
                "UPDATE users SET name=%s, favorite_mood=%s, bio=%s, profile_image=%s WHERE id=%s",
                (name, favorite_mood, bio, profile_image, user["id"]),
            )
            update_session_user()
            st.success("Profile updated.")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def playlists_section(user):
    st.markdown(
        """
        <div class="section-intro">
            <h2>My Playlists</h2>
            <p>Create your own playlists, add songs from song cards, and play direct-audio tracks one after another automatically.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("create_playlist_form"):
        playlist_name = st.text_input("New playlist name", placeholder="Gym mix, late night drive, happy Punjabi...")
        submitted = st.form_submit_button("Create Playlist")
        if submitted:
            ok, message = create_playlist(user["id"], playlist_name)
            st.success(message) if ok else st.error(message)
            if ok:
                st.rerun()

    playlists = user_playlists(user["id"])
    if not playlists:
        st.info("Create a playlist first, then use Add to playlist on any song card.")
        return

    playlist_labels = {f"{item['name']} ({item['song_count']} songs)": item for item in playlists}
    selected_label = st.selectbox("Open playlist", list(playlist_labels.keys()), key="open_playlist_select")
    selected = playlist_labels[selected_label]
    playlist_id = int(selected["id"])
    playlist_name = selected["name"]
    tracks = playlist_songs(user["id"], playlist_id)

    c1, c2 = st.columns([3, 1])
    c1.subheader(playlist_name)
    if c2.button("Delete Playlist", key=f"delete_playlist_{playlist_id}"):
        delete_playlist(user["id"], playlist_id)
        st.warning("Playlist deleted.")
        st.rerun()

    if tracks.empty:
        st.info("This playlist is empty. Add songs from EcoWavE Music, All Songs, or Saved.")
        return

    render_playlist_player(tracks, playlist_name)
    st.caption(f"{len(tracks)} songs in this playlist")
    playlist_queue = queue_from_rows(tracks)
    for position, (_, row) in enumerate(tracks.iterrows(), start=1):
        duration = format_duration(row.get("duration_seconds", 180))
        st.markdown(
            f"""
            <div class="song-card">
                <div class="track-row">
                    <div class="track-index">{position}</div>
                    <div class="album-mark">{song_logo_html(row["source_url"], row["title"], row["artist"], row["mood"], row.get("cover_url", ""))}</div>
                    <div class="track-main">
                        <h3>{html.escape(str(row['title']))}</h3>
                        <div class="meta">
                            <span>{html.escape(str(row['artist']))}</span>
                            <span>{html.escape(str(row['genre']))}</span>
                            <span class="pill">{html.escape(str(row['mood']))}</span>
                        </div>
                    </div>
                    <div class="track-album">{html.escape(str(row.get('album') or 'Single'))}</div>
                    <div class="track-duration">{duration}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        player_key = f"playlist_{playlist_id}_{int(row['id'])}"
        action_cols = st.columns([9, 1])
        play_label = song_icon_label(player_key)
        if action_cols[0].button(play_label, key=f"playlist_play_{playlist_id}_{int(row['id'])}", use_container_width=True):
            set_current_player(player_key)
            set_play_queue(playlist_queue, position - 1)
            log_listen(user["id"], int(row["id"]), row["mood"], int(row.get("duration_seconds", 180)))
            st.rerun()
        menu = action_cols[1].popover("...", use_container_width=True)
        if menu.button("Remove From Playlist", key=f"playlist_remove_{playlist_id}_{int(row['id'])}", use_container_width=True):
            remove_song_from_playlist(user["id"], playlist_id, int(row["id"]))
            st.rerun()
        if menu.button("Save", key=f"playlist_save_{playlist_id}_{int(row['id'])}", use_container_width=True):
            save_song(user["id"], int(row["id"]))
            st.success("Saved to your library.")
            st.rerun()
        render_download_audio_control(row["title"], row["source_url"], f"playlist_{playlist_id}_{int(row['id'])}", menu)
        if is_current_player(player_key):
            render_now_playing(row["title"], row["artist"])
            source_view(row["source_url"])


def artists_albums_section(user):
    library = songs_df()
    st.markdown(
        """
        <div class="section-intro">
            <h2>Artists & Albums</h2>
            <p>Browse Punjabi artists, albums, and songs from your EcoWavE library.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if library.empty:
        st.info("No artists or albums are available yet.")
        return

    artist_names = sorted(set(library["artist"].fillna("").tolist()) | set(ARTIST_ALBUMS.keys()))
    selected_artist = st.selectbox("Artist", artist_names, key="artist_album_artist")
    artist_songs = library[library["artist"] == selected_artist].copy()
    known_albums = ARTIST_ALBUMS.get(selected_artist, [])
    library_albums = sorted(album for album in artist_songs.get("album", pd.Series(dtype=str)).fillna("").unique() if album)
    album_names = ["All Albums"] + sorted(set(known_albums) | set(library_albums))
    selected_album = st.selectbox("Album", album_names, key="artist_album_album")

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="label">Artist</div><div class="value">{html.escape(selected_artist)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="label">Albums</div><div class="value">{max(0, len(album_names) - 1)}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="label">Songs</div><div class="value">{len(artist_songs)}</div></div>', unsafe_allow_html=True)

    if selected_album != "All Albums":
        artist_songs = artist_songs[artist_songs["album"].fillna("") == selected_album]

    if artist_songs.empty:
        st.info("This album is listed for the artist, but no songs from it are in the library yet.")
        return

    grouped = artist_songs.groupby(artist_songs["album"].fillna("Single"), sort=True)
    for album_name, rows in grouped:
        st.subheader(album_name or "Single")
        render_song_list(rows, user, f"artist_album_{selected_artist}_{album_name}", "No songs in this album.")


def section_nav(state_key, sections, label="Section"):
    if state_key not in st.session_state or st.session_state[state_key] not in sections:
        st.session_state[state_key] = sections[0]
    current_index = sections.index(st.session_state[state_key])
    back_col, choose_col, next_col = st.columns([1, 5, 1])
    if back_col.button("← Back", key=f"{state_key}_back", disabled=current_index == 0, use_container_width=True):
        st.session_state[state_key] = sections[current_index - 1]
        st.rerun()
    if next_col.button(
        "Next →",
        key=f"{state_key}_next",
        disabled=current_index == len(sections) - 1,
        use_container_width=True,
    ):
        st.session_state[state_key] = sections[current_index + 1]
        st.rerun()
    icons = {
        "Search": "⌕",
        "All Songs": "♪",
        "Saved": "★",
        "Playlists": "▦",
        "History": "↺",
        "Add Music": "+",
        "Profile": "◉",
        "EcoWavE Music": "♫",
        "Online Music": "⌁",
        "Library": "▤",
        "Analytics": "▥",
    }
    with choose_col:
        nav_cols = st.columns(len(sections))
        for index, section in enumerate(sections):
            icon = icons.get(section, "•")
            active = section == st.session_state[state_key]
            button_label = f"■ {section}" if active else f"{icon} {section}"
            if nav_cols[index].button(button_label, key=f"{state_key}_{section}", use_container_width=True):
                st.session_state[state_key] = section
                st.rerun()
    return st.session_state[state_key]


def section_nav2(state_key, sections, label="Section"):
    if state_key not in st.session_state or st.session_state[state_key] not in sections:
        st.session_state[state_key] = sections[0]
    current_index = sections.index(st.session_state[state_key])
    back_col, choose_col, next_col = st.columns([1, 5, 1])
    if back_col.button("< Back", key=f"{state_key}_back_v2", disabled=current_index == 0, use_container_width=True):
        st.session_state[state_key] = sections[current_index - 1]
        st.rerun()
    if next_col.button(
        "Next >",
        key=f"{state_key}_next_v2",
        disabled=current_index == len(sections) - 1,
        use_container_width=True,
    ):
        st.session_state[state_key] = sections[current_index + 1]
        st.rerun()
    with choose_col:
        nav_cols = st.columns(len(sections))
        for index, section in enumerate(sections):
            active = section == st.session_state[state_key]
            button_label = section
            if nav_cols[index].button(button_label, key=f"{state_key}_v2_{section}", use_container_width=True):
                st.session_state[state_key] = section
                st.rerun()
    return st.session_state[state_key]


def user_interface(user):
    hero(user)
    st.write("")
    metric_row(user)
    st.write("")
    page = section_nav2(
        "user_page",
        ["Search", "All Songs", "Saved", "Playlists", "Artists & Albums", "History", "Add Music", "Profile"],
        "User section",
    )
    st.write("")
    if page == "Search":
        search_page = section_nav2("search_page", ["EcoWavE Music", "Online Music"], "Search section")
        if search_page == "EcoWavE Music":
            st.markdown(
                """
                <div class="section-intro">
                    <h2>EcoWavE Music</h2>
                    <p>Recommendations from your EcoWavE library, ranked by mood, favorites, and search intent.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns([1, 2])
            mood = c1.selectbox("Current mood", MOODS, index=MOODS.index(user.get("favorite_mood") or "Happy"))
            mood_search = c2.text_input(
                "Search mood library",
                placeholder="romantic song, sad piano, workout beats",
                key="mood_music_search",
            )
            mood_library = songs_df()
            if not mood_library.empty:
                mood_library = mood_library[mood_library["mood"].fillna("").str.lower() == mood.lower()]
            recs = recommend_songs(mood_library, mood, mood_search, mood, top_n=20)
            if recs.empty:
                st.info(f"No {mood} songs found in the library.")
            else:
                st.caption(f"Showing only {mood} songs")
                render_song_list(recs, user, f"discover_mood_{mood.lower()}", f"No {mood} songs found in the library.")
        else:
            st.markdown(
                """
                <div class="section-intro online">
                    <h2>Online Music</h2>
                    <p>Search online tracks separately, then play or save discoveries into your EcoWavE history.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns([1, 2])
            online_mood = c1.selectbox(
                "Mood for online results",
                MOODS,
                index=MOODS.index(user.get("favorite_mood") or "Happy"),
                key="online_music_mood",
            )
            online_search = c2.text_input(
                "Search online music",
                placeholder="Arijit romantic, lo-fi focus, upbeat pop",
                key="online_music_search",
            )
            render_online_results(online_search, user, online_mood, "discover_online")
    elif page == "All Songs":
        library = songs_df()
        all_search = st.text_input("Search full library", placeholder="Type song name, artist, mood, or genre")
        if all_search:
            needle = all_search.strip().lower()
            mask = (
                library["title"].fillna("").str.lower().str.contains(needle, regex=False)
                | library["artist"].fillna("").str.lower().str.contains(needle, regex=False)
                | library["album"].fillna("").str.lower().str.contains(needle, regex=False)
                | library["mood"].fillna("").str.lower().str.contains(needle, regex=False)
                | library["genre"].fillna("").str.lower().str.contains(needle, regex=False)
            )
            library = library[mask]
        st.caption(f"{len(library)} songs available")
        if library.empty:
            st.info("No matching songs found in the local library.")
        else:
            render_song_list(library, user, "all_songs", "No matching songs found in the local library.")
    elif page == "Saved":
        saved = saved_songs(user["id"])
        if saved.empty:
            st.info("Saved music will appear here.")
        else:
            render_song_list(saved, user, "saved", "Saved music will appear here.")
    elif page == "Playlists":
        playlists_section(user)
    elif page == "Artists & Albums":
        artists_albums_section(user)
    elif page == "History":
        history_section(user)
    elif page == "Add Music":
        add_music_form(user, "Add Your Music")
        st.caption("Your added music becomes part of the shared active library.")
    elif page == "Profile":
        profile_section(user)


def admin_interface(user):
    hero(user)
    st.write("")
    songs = songs_df(active_only=False)
    history = all_history()
    active_count = int(songs["is_active"].sum()) if not songs.empty else 0
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="label">Total songs</div><div class="value">{len(songs)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="label">Active songs</div><div class="value">{active_count}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="label">Total plays</div><div class="value">{len(history)}</div></div>', unsafe_allow_html=True)
    st.write("")
    page = section_nav2("admin_page", ["Library", "Add Music", "Analytics", "Profile"], "Admin section")
    st.write("")
    if page == "Library":
        st.subheader("Music Library")
        if songs.empty:
            st.info("No songs yet.")
        else:
            st.dataframe(
                songs[["id", "title", "artist", "album", "mood", "genre", "source_url", "is_active", "added_by_name"]],
                use_container_width=True,
            )
            active = songs[songs["is_active"] == 1]
            render_song_list(active, user, "admin_library", "No active songs yet.", allow_remove=True)
    elif page == "Add Music":
        add_music_form(user, "Admin Add Music")
    elif page == "Analytics":
        st.subheader("Listening Analytics")
        if history.empty:
            st.info("Analytics appear after users play songs.")
        else:
            mood_summary = (
                history.groupby("mood", as_index=False)["listened_seconds"].sum().assign(
                    minutes=lambda x: (x["listened_seconds"] / 60).round(1)
                )
            )
            fig = px.pie(mood_summary, values="minutes", names="mood", hole=.45, title="Platform listening by mood")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(history[["listened_at", "user_name", "title", "mood", "listened_seconds"]], use_container_width=True)
    elif page == "Profile":
        profile_section(user)


def auth_screen(cookies):
    show_admin = show_private_admin_login()
    tab_names = ["User Login"]
    if show_admin:
        tab_names.append("Admin Login")
    tab_names.append("Create Account")
    tabs = dict(zip(tab_names, st.tabs(tab_names)))

    with tabs["User Login"]:
        st.subheader("User Login")
        with st.form("user_login_form"):
            email = st.text_input("User email", value="", placeholder="you@example.com")
            password = st.text_input("User password", value="", type="password")
            remember = st.checkbox("Keep me logged in", value=True, key="remember_user_login")
            submitted = st.form_submit_button("Login")
            if submitted:
                ok, message = login_user(email, password, expected_role="user")
                if ok:
                    if remember:
                        remember_user(st.session_state.user, cookies)
                    st.rerun()
                st.error(message)

    if show_admin:
        with tabs["Admin Login"]:
            st.subheader("Admin Login")
            with st.form("admin_login_form"):
                email = st.text_input("Admin email", value="", placeholder="admin@example.com")
                password = st.text_input("Admin password", value="", type="password")
                remember = st.checkbox("Keep me logged in", value=True, key="remember_admin_login")
                submitted = st.form_submit_button("Login as Admin")
                if submitted:
                    ok, message = login_user(email, password, expected_role="admin")
                    if ok:
                        if remember:
                            remember_user(st.session_state.user, cookies)
                        st.rerun()
                    st.error(message)

    with tabs["Create Account"]:
        st.subheader("Create account")
        with st.form("signup_form"):
            name = st.text_input("Full name")
            new_email = st.text_input("New email")
            new_password = st.text_input("New password", type="password")
            submitted = st.form_submit_button("Sign up")
            if submitted:
                if len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif not name or not new_email:
                    st.error("Name and email are required.")
                else:
                    ok, message = create_user(name, new_email, new_password)
                    st.success(message) if ok else st.error(message)


def sidebar(user, cookies):
    if os.path.exists(LOGO_PATH):
        st.sidebar.image(LOGO_PATH, width=190)
    st.sidebar.title(APP_TITLE)
    st.sidebar.caption("Mood based music system")
    if user:
        st.sidebar.markdown(
            f'<div class="profile-head">{profile_image_html(user, 56)}<div><strong>{html.escape(user["name"])}</strong><p>{html.escape(user["role"].title())}</p></div></div>',
            unsafe_allow_html=True,
        )
        st.sidebar.write(f"Signed in as {user['name']}")
        st.sidebar.write(f"Role: {user['role'].title()}")
        if st.sidebar.button("Logout"):
            clear_remembered_user(cookies)
            st.session_state.pop("user", None)
            st.rerun()
    st.sidebar.divider()
    st.sidebar.write("Permanent project link")
    st.sidebar.caption(local_app_url())
    st.sidebar.caption(f"Phone on same Wi-Fi: {network_url()}")
    st.sidebar.divider()
    st.sidebar.write("MySQL database")
    cfg = mysql_config()
    st.sidebar.caption(f"{cfg['user']}@{cfg['host']}:{cfg['port']} / {cfg['database']}")


def main():
    inject_styles()
    app_splash_screen()
    cookies = CookieController()
    try:
        initialize_app_once()
    except Exception as exc:
        st.error("Could not connect to MySQL. Update `.streamlit/secrets.toml` or start your MySQL server.")
        st.code(str(exc))
        st.stop()
    restore_remembered_user(cookies)
    user = st.session_state.get("user")
    sidebar(user, cookies)
    if not startup_popup():
        st.stop()
    if not user:
        auth_screen(cookies)
        return
    if st.session_state.pop("show_login_animation", False):
        login_success_animation(user)
    if user["role"] == "admin":
        admin_interface(user)
    else:
        user_interface(user)


if __name__ == "__main__":
    _ = main()
