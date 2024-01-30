import spotipy
from spotipy.oauth2 import SpotifyOAuth

import os
from dotenv import load_dotenv, find_dotenv
print(__file__)
load_dotenv(find_dotenv())

from flask import Flask, request, url_for, session, redirect
import time
import filter_song

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

print(__name__)
app = Flask(__name__)
app.config["SESSION_COOCKIE_NAME"] = "pipi"
app.secret_key = "gay"
TOKEN_INFO = "token_info"

@app.route("/")
def login():
    auth_url = spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    session.clear()
    code = request.args.get("code")
    token_info = spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for("create_playlist", external = True))

@app.route("/create_playlist")
def create_playlist():
    try:
        token_info = get_token()
    except:
        print("User are not logged in")
        return redirect("/")
    
    torio = "3gQEmyPWOxbSnNJzeqVSi5"
    playlists = {
                 "Rezza Capa": "1DkkgB2T4qShCdzknEC8Iv",
                 "Nicola": "4Z3UtePQqtlMcJxkcHS5BP",
                 "Colletti": "2kcVxGZrI2dgG3lentrQEK",
                 "Di Maria": "26VIRC6eT0tjBTFloShpi1",
                }
    
    spotify = spotipy.Spotify(auth=token_info["access_token"])
    
    # spotify.playlist_remove_all_occurrences_of_items(playlists["Rezza Capa"], [cazziFreestyle], snapshot_id=None)
    playlist = spotify.playlist_items(playlists["Rezza Capa"], fields="next, items.track.uri, items.track.name") 
    
    playlist2 = spotify.next(playlist)
    
    return playlist2
    

def spotify_oauth():
    return SpotifyOAuth(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        redirect_uri = url_for("callback", _external=True),
        scope = "playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public"
    )
    
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for("login", external = False))
        
    now = int(time.time())
    
    is_expired = token_info["expires_at"] - now < 60
    if(is_expired): 
        refreshed_oauth = spotify_oauth()
        token_info = refreshed_oauth.refresh_access_token(token_info["refresh_token"])
    return token_info
        
app.run(port=8000, debug=True)