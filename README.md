# 🎵 Censitorio musicale (Torio's musical census) 🎵

## Overview
**Automate your group's monthly music discovery.** This project handles the collective selection of the best tracks from a shared Spotify playlist. No more debating which songs deserve to stay - let the data decide!

### How it Works
1.  **Discover:** Throughout the month, group members add their latest finds to a **shared playlist**.
2.  **Vote:** If you like a song, simply add it to your **personal playlists**. That’s your vote!
3.  **Tally:** Once a month, the script counts how many members saved each song (unique votes only).
4.  **Promote:** Tracks that reach a **majority consensus** are automatically moved to a "Hall of Fame" playlist, preserving the group's top hits forever.

### Features
- **Spotify API Integration**: The project uses the Spotify API to authenticate and extract playlist data, providing a seamless and efficient way to manage playlists.
- **Monthly Backup**: The project can create a monthly backup of all the playlists, if the users need it.  
- **Statistics**: Each execution of the code creates a .json with all the songs which are added or removed from each playlists.
- **Playlist Data Extraction**: The project extracts specific fields from the Spotify API, providing users with detailed information about their playlists.
- **Logging**: The project includes logging functionality. You can set 2 option: INFO gives you only the surface information, DEBUG gives you detailed information for all processes.

### Tech Stack
* **Python**: The project is built using Python, a popular and versatile programming language.
* **Spotify API**: The project uses the Spotify API to interact with Spotify playlists and extract data.

## Usage

### Installation
1. Clone the repository using `git clone`.
2. Create a virtual environment (venv) and enter it with `source ./bin/activate` for Linux or `./bin/activate` for Windows.
3. Install the required dependencies using `pip install -r requirements.txt`.
4. Create a .env file, following the env template, and add your Spotify API credentials.
5. Create a playlists.json file, following the playlists template. Add the ids of the spotify playlists.

### Run the code
1. Run the project using `python censitorio.py` if you don't want the statistics, `python censitorio_monthly_stats.py` if you want them.
2. Wait for the execution (around 1 minute on a decent pc).
3. Look te result on your Spotify!

## ⚠️ Important Notes

* **Cleanup:** every time the script runs, songs that *didn't* make the cut are automatically removed from both the shared and personal playlists.
* **No Local Files:** Only songs available on the Spotify streaming catalog are supported. Local files will be ignored.
* **Permissions:** The authenticated Spotify account must have full `read/write` access to all involved playlists to smoothly execute the code.