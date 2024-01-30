# Import dotenv
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Import Spotify API
import spotipy
from spotipy.oauth2 import SpotifyOAuth
# Setting for spotify API
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Import Flask
from flask import Flask, request, url_for, session, redirect
# Setting for Flask
app = Flask(__name__)
app.config["SESSION_COOCKIE_NAME"] = "pipi"
app.secret_key = "gay"
TOKEN_INFO = "token_info"

# Import other library
import time
import logging
logging.basicConfig(filename='filter_spotify.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


# ANCHOR - Home route
@app.route("/")
def login():
    """Inizialize the authentication for spotify API

    Returns:
        redirect(auth_url): Redirect to an external page for the spotify's login
    """
    logging.info("Start login")
    auth_url = spotify_oauth().get_authorize_url()
    logging.debug("Link to spotify login page: " + str(auth_url))
    return redirect(auth_url) 


# ANCHOR - The external page then redirect us to this page after you complete the login
@app.route("/callback")
def callback():
    """Extraction of the access token, which was given by the login

    Returns:
        redirect(url_for("create_playlist", external = True)): Redirect to an internal page which will execute the main task of this code
    """
    logging.info("Start callback")
    session.clear()
    
    code = request.args.get("code")
    logging.debug("Code received from login page: " + str(code))
    
    token_info = spotify_oauth().get_access_token(code)
    logging.debug("Token info in callback: " + str(token_info))
    
    session[TOKEN_INFO] = token_info
    return redirect(url_for("create_playlist", external = True))


# ANCHOR - The internal page "callback" redirect us to this page after it extracts the access token
@app.route("/create_playlist")
def create_playlist():
    """Creation of the Torio playlist

    Returns:
        torio_playlist: the official torio playlist
    """
    logging.info("Start main")
    try:
        token_info = get_token()
        logging.debug("Token info in create_playlist: " + str(token_info)) 
    except Exception as e:
        print("User are not logged in")
        logging.error("Error, user are not probably logged in: " + str(e))
        return redirect("/")
    
    ID_TORIO = "3gQEmyPWOxbSnNJzeqVSi5"
    users_playlists = {
                #  "Rezza Capa": "1DkkgB2T4qShCdzknEC8Iv",
                 "Nicola": "1XiiJ7SI3JkI0scBqWeRas",
                 "Colletti": "2kcVxGZrI2dgG3lentrQEK",
                 "Di Maria": "26VIRC6eT0tjBTFloShpi1",
                }
    FILTER = "next, items.track.uri, items.track.name"
    
    spotify = spotipy.Spotify(auth=token_info["access_token"])
    
    torio_songs = {}
    playlist = spotify.playlist_items(ID_TORIO, fields=FILTER) 
    
    #Extraction of Torio general songs
    while True:
        items = playlist["items"]
        
        torio_songs = add_uris_to_dict(torio_songs, items)
                
        next = {"next": playlist["next"]}
        logging.debug("Next: " + str(next))
        if(next["next"] == None):
            logging.info("No more pages")
            break
        else:
            logging.info("Another page found")
            playlist = None
            playlist = spotify.next(next)
    logging.debug("All torio songs: " + str(torio_songs))
            
    # Extraction of torio's member's playlists
    for user, id_playlist in users_playlists.items():
        logging.info("Extracting user " + str(user) + " playlist: " + str(id_playlist))
        user_songs = []
        playlist = None
        playlist = spotify.playlist_items(id_playlist, fields=FILTER)
        
        while True:
            items = playlist["items"]
            
            user_songs = add_uris_to_list(user_songs, items)
                    
            next = {"next": playlist["next"]}
            logging.debug("Next: " + str(next))
            if(next["next"] == None):
                logging.info("No more pages")
                break
            else:
                logging.info("Another page found")
                playlist = None
                playlist = spotify.next(next)
        logging.debug("All " + str(user) + " songs: " + str(user_songs))
        
        for song in user_songs:
            if(song in torio_songs):
                torio_songs[song] += 1
            
        # NOTE - manca filtraggio in base ai contatori
    return torio_songs
    
    
# ANCHOR - spotify_oauth
def spotify_oauth():
    """Create an object to allow us to login into spotify and use the logged session to save the access token

    Returns:
        SpotifyOAuth(...): An object of the library "spotipy", composed by 
                           the client id;
                           the "password" (client secret);
                           the redirect uri, which is where the external authorize url will redirect us after the login;
                           the scope, which is the action we can perform with the logged spotify account 
    """
    return SpotifyOAuth(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        redirect_uri = url_for("callback", _external=True),
        scope = "playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public"
    )
    
    
# ANCHOR - get_token
def get_token():
    """Extraction of the token from the session, 
       if there isn't or it is expired it will redirect to the login page,
       

    Returns:
        token_info: the access token
    """
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        logging.warning("User is not logged in Spotify")
        redirect(url_for("login", external = False))
        
    now = int(time.time())
    
    is_expired = token_info["expires_at"] - now < 60
    if(is_expired): 
        logging.warning("The token is expired")
        refreshed_oauth = spotify_oauth()
        token_info = refreshed_oauth.refresh_access_token(token_info["refresh_token"])
        logging.info("The token was refreshed")
        
    return token_info


# ANCHOR - add_uris_to_dict
def add_uris_to_dict(dict, items):
    """Adds uris as key and 0 as value to a dict

    Args:
        dict (dict): the dict that will receive the uris
        items (list): the list of uris

    Returns:
        dict: the dict with the newly added "uris: 0" (key: value)
    """
    for item in items:
        logging.debug("Item of the playlist: " + str(item))
        uri = item["track"]["uri"]
        is_local = uri.split(":")[1] == "local"
        logging.debug("Is local? " + str(is_local))
        if(not is_local):
            dict[uri] = 0
    
    return dict


# ANCHOR - add_uris_to_list
def add_uris_to_list(list, items):
    """Adds uris to a list

    Args:
        list (list): the list that will receive the uris
        items (_type_): the list of uris

    Returns:
        list: the list with the newly added uris
    """
    for item in items:
        logging.debug("Item of the playlist: " + str(item))
        uri = item["track"]["uri"]
        is_local = uri.split(":")[1] == "local"
        logging.debug("Is local? " + str(is_local))
        if(not is_local):
            list.append(uri)
    
    return list
   
   
# ANCHOR -Flask app run     
app.run(port=8000, debug=True)