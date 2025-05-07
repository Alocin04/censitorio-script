# ---------------------------------------------------------------------------- #
#                                    LIBRARY                                   #
# ---------------------------------------------------------------------------- #
import os
from dotenv import load_dotenv, find_dotenv # library for reading file .env
load_dotenv(find_dotenv())

import spotipy # Spotify API
from spotipy.oauth2 import SpotifyOAuth

from flask import Flask, request, url_for, session, redirect # Flask, needed for diplaying the Spotify's login pop-up

# local file
from playlist import get_counters_dict, get_songs_list, get_songs_from_playlist
from playlist import delete_songs_from_playlist, add_songs_to_playlist
from playlist import hard_reset, soft_reset, remove_duplicate
from playlist import ID_PLAYLIST, ID_WAITING_ROOM, ID_BACKUP, IDS_PLAYLISTS, FILTER, MIN_LIKE

from math import ceil
import time
import logging
logging.basicConfig(filename='filter_spotify.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# ---------------------------------------------------------------------------- #
#                                   SETTINGS                                   #
# ---------------------------------------------------------------------------- #
# Setting for spotify API
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Setting for Flask and session
PORT = 8000
app = Flask(__name__)
app.config["SESSION_COOCKIE_NAME"] = "pipi"
app.secret_key = "gay"
TOKEN_INFO = "token_info"

# ---------------------------------------------------------------------------- #
#                                     ROUTE                                    #
# ---------------------------------------------------------------------------- #
#* The internal page "callback" redirects us to this url after it extracts the access token
@app.route("/create_playlist")
def create_playlist():
    """Creation of the Torio playlist
        It extracts all the songs from the playlist waiting room. 
        Then check how many instance of each songs there are in each personal playlist.
        If the number of song's instance is higher than the minimun likes, the song will be added in the universal playlist of our group.  

        Returns:
            torio_playlist: the official torio playlist
    """
    logging.info("Start main")
    
    start_time = time.time()
    #* Checking if logged in spotify
    try:
        token_info = get_token()
        logging.debug("Token info in create_playlist: " + str(token_info)) 
    except Exception as e:
        print("User are not logged in")
        logging.error("Error, user are not probably logged in: " + str(e))
        return redirect("/")
    
    spotify = spotipy.Spotify(auth=token_info["access_token"]) #* Inizializing the spotify client
    
    # ---------------------------------- SCRIPTS --------------------------------- #
    #* Hard Reset: rimozione di tutte le canzoni da tutte le playlist
    # response = ["Finito hard reset"]
    # hard_reset(spotify)
    # return response
    
    #* Soft Reset: rimozione di tutte le canzoni da playlist backup
    # IDS_BACKUP = {
    #     "ID_BACKUP_WAITING_ROOM": "5IkPMTHii0yy8PxkHaFGbB",
    #     "ID_BACKUP_MOMENTO_TORIO": "5u4SlTRwaLnaxmiYwnmMQm",
    #     "ID_BACKUP_MIA_PLAYLIST": "56BxJ9OeY9iQgLrPxYvPnM",
    # }
    # response = ["Finito soft reset"]
    # soft_reset(spotify, IDS_BACKUP)
    # return response
    
    #TODO Da finire: https://github.com/JMPerez/spotify-dedup/blob/master/dedup/deduplicator.ts
    #* Rimozione di tutti i doppioni dalle playlist
    # response = remove_duplicate(spotify)
    # return response
    # ------------------------------- FINE SCRIPTS ------------------------------- #
    
    
    
    # ------------------------------- CALCOLO LIKES ------------------------------ #
    waiting_room = get_songs_from_playlist(spotify, ID_WAITING_ROOM, FILTER) #* Estrazione della playlist waiting room
    songs_likes = get_counters_dict(waiting_room) #* Formattazione del dict per il conteggio dei like
    
    #* Estrazione e formattazione delle playlist personali dei membri
    users_songs = {} # Dict dove le chiavi sono i nomi dei proprietari della playlist e i valori sono le liste di canzoni nella playlist
    for user, id_playlist in IDS_PLAYLISTS.items():
        logging.info(f"Extracting user {user}'s playlist: {id_playlist}")
        
        user_playlist_not_formatted = get_songs_from_playlist(spotify, id_playlist, FILTER) #* Estrazione della playlist personale
        user_playlist = list(set(get_songs_list(user_playlist_not_formatted))) #* Ottenimento della lista delle canzoni, il set rimuove i duplicati

        if (len(user_playlist)<10):
            logging.warning(f"{user}'s playlist is empty or almost empty, so it won't count")
            continue
        users_songs[user] = user_playlist
        logging.debug(f"All {user}'s songs: {users_songs[user]}")
        
        #* Aumento il counter delle canzoni per ogni istanza (non stessa playlist) presente nelle playlist personali
        for song in user_playlist:
            if(song in songs_likes):
                songs_likes[song] += 1
             
    logging.info(f"Songs' like: {songs_likes}")
    
    #* Decido il numero di like (valore counter) necessari per essere aggiunti alla playlist ufficiale
    # Viene deciso in base a quanti membri hanno la playlist personale
    required_like = 0
    logging.debug(f"Number of playlist: {len(users_songs)}")
    logging.debug(f"Minimun number of like: {MIN_LIKE}")
    if(len(users_songs)<=MIN_LIKE): 
        # Se il numero delle playlist è minore od uguale al numero minimo di playlist (4)
        required_like = len(users_songs)
    else:
        # Se il numero delle playlist è maggiore del numero minimo di playlist (4)
        # divido il numero delle playlist per 3 e arrotondo per eccesso
        required_like = ceil(len(users_songs)/3)
        logging.debug(f"Required liked calculated by ceil: {required_like}")
        
        # Se l'operazione precedente è minore del numero minimo di playlist (4)
        if(required_like<MIN_LIKE):
            required_like = MIN_LIKE
    logging.info(f"Required like to be added to the official playlist: {required_like}")
    # ---------------------------- FINE CALCOLO LIKES ---------------------------- #
    
    
    
    # --------------------------- UPDATE MOMENTO TORIO --------------------------- #
    #* Salvo le canzoni che hanno superato od egualiato i like minimi
    winner_songs = []
    for uri, like in songs_likes.items():
        if like>=required_like:
            logging.debug(f"Winner song: {uri}, aggiunta da {like} persone")
            winner_songs.append(uri)
    torio_playlist = get_songs_from_playlist(spotify, ID_PLAYLIST, FILTER) #* Estrazione della playlist momento torio
    momento_torio = get_songs_list(torio_playlist) #* Ottenimento della lista delle canzoni
    
    #* Ottenimento delle canzoni di momento torio che non hanno passato il voto
    songs_2_remove = []
    for uri in momento_torio:
        if uri not in winner_songs and uri not in songs_2_remove:
            logging.debug(f"{uri} not in winner songs: needs to be removed")
            songs_2_remove.append(uri)
    delete_songs_from_playlist(spotify, songs_2_remove.copy(), ID_PLAYLIST) #* Rimozione canzoni che non hanno raggiuto i like minimi
            
    #* Ottenimento delle canzoni di momento torio che hanno passato il voto e non sono già presenti
    songs_2_add = []
    for uri in winner_songs:
        if uri not in momento_torio and uri not in songs_2_add:
            logging.debug(f"{uri} not in momento torio: needs to be added")
            songs_2_add.append(uri)
    add_songs_to_playlist(spotify, songs_2_add.copy(), ID_PLAYLIST) #* Aggiunta delle canzoni che hanno raggiuto i like minimi
    # ------------------------- FINE UPDATE MOMENTO TORIO ------------------------ #
    
    
    
    # ------------------------------- UPDATE BACKUP ------------------------------ #
    #* Ottengo le canzoni nella playlist di backup
    # Questo perché successivamente si deve controllare se le canzoni in waiting room sono già presenti nel backup 
    backup_playlist = get_songs_from_playlist(spotify, ID_BACKUP, FILTER) #* Estrazione della playlist
    backup_songs = get_songs_list(backup_playlist) #* Ottenimento della lista delle canzoni
    
    #* Aggiungo al backup le canzoni che non sono già presenti
    songs_2_add.clear()
    waiting_room_uris = list(songs_likes.keys()) # Ottenimento degli uri della waiting room
    for uri in waiting_room_uris:
        if uri not in backup_songs and uri not in songs_2_add:
            # spotify.playlist_add_items(ID_BACKUP, [uri])
            songs_2_add.append(uri)
    add_songs_to_playlist(spotify, songs_2_add.copy(), ID_BACKUP)
    # ---------------------------- FINE UPDATE BACKUP ---------------------------- #
    
    
    
    # ------------------------- UPDATE PLAYLIST PERSONALI ------------------------ #
    for user, songs in users_songs.items():
        logging.info(f"Updating {user}'s playlist")
        #* Ottenimento delle canzoni che non hanno passato il voto
        songs_2_remove.clear()
        for uri in songs:
            if uri not in winner_songs and uri not in songs_2_remove:
                logging.debug(f"{uri} not in winner songs: needs to be removed")
                songs_2_remove.append(uri)
        delete_songs_from_playlist(spotify, songs_2_remove.copy(), IDS_PLAYLISTS[user]) #* Rimozione canzoni che non hanno raggiuto i like minimi
    # ---------------------- FINE UPDATE PLAYLIST PERSONALI ---------------------- #

    
        
    # ---------------------------- UPDATE WAITING ROOM --------------------------- #
    #* Tolgo da waiting room le canzoni che non sono vincenti
    songs_2_remove.clear()
    for uri in waiting_room_uris:
        if uri not in winner_songs and uri not in songs_2_remove:
            logging.debug(f"{uri} not in winner songs: needs to be removed")
            songs_2_remove.append(uri)
    delete_songs_from_playlist(spotify, songs_2_remove.copy(), ID_WAITING_ROOM) #* Rimozione canzoni che non hanno raggiuto i like minimi
    # ------------------------- FINE UPDATE WAITING ROOM ------------------------- #
    
    print(f"--- TIME OF EXECUTION {time.time() - start_time}---")
    return [len(winner_songs), winner_songs]

""" def create_playlist():
    ""Creation of the Torio playlist
        It extracts all the songs from the playlist waiting room. 
        Then check how many instance of each songs there are in each personal playlist.
        If the number of song's instance is higher than the minimun likes, the song will be added in the universal playlist of our group.  

        Returns:
            torio_playlist: the official torio playlist
    ""
    logging.info("Start main")
    
    start_time = time.time()
    #* Checking if logged in spotify
    try:
        token_info = get_token()
        logging.debug("Token info in create_playlist: " + str(token_info)) 
    except Exception as e:
        print("User are not logged in")
        logging.error("Error, user are not probably logged in: " + str(e))
        return redirect("/")
    
    #* Inizializing the spotify client
    spotify = spotipy.Spotify(auth=token_info["access_token"]) 
    
    # ------------------------------- RECUPERO SONG ------------------------------ #
    # waiting_room = spotify.playlist_items(ID_PLAYLIST, fields=FILTER) # Inserisco il filtro per ottenere solo i campi che mi servono
    # torio_songs = []
    # while True:
    #     items = waiting_room["items"]
        
    #     # Struttura di spotify scomoda perché annidata.
    #     # Creo un dict dove le chiavi sono le uri delle canzoni mentre i valori sono dei contatori inizializzati a zero
    #     for item in items:
    #         logging.debug("Item of the playlist: " + str(item))
    #         if (item["track"]==None):
    #             continue
    #         if (item["track"]["uri"]==None):
    #             continue
            
    #         uri = item["track"]["uri"]
    #         is_local = uri.split(":")[1] == "local"
    #         logging.debug("Is local? " + str(is_local))
    #         if(not is_local and uri not in torio_songs):
    #             torio_songs.append(uri)
    #     # Struttura necessaria per ottenere le successive 100 canzoni
    #     next = {"next": waiting_room["next"]}
    #     logging.debug("Next: " + str(next))
    #     if(next["next"] == None):
    #         logging.info("No more pages")
    #         break
    #     else:
    #         logging.info("Another page found")
    #         waiting_room = None
    #         waiting_room = spotify.next(next)
        
    # logging.debug(torio_songs)
    # N_SPLIT = 100 # Numero di canzoni rimosse a ciclo      
    # delete_copy = torio_songs.copy()
    # while (len(delete_copy)!=0):
    #     remove_list = delete_copy[:N_SPLIT]
    #     del delete_copy[:N_SPLIT]
    #     spotify.playlist_remove_all_occurrences_of_items(ID_PLAYLIST, remove_list)
    
    # logging.debug(torio_songs)
    # winners_copy = torio_songs.copy()
    # while (len(winners_copy)!=0):
    #     logging.debug(len(winners_copy))
    #     winners = winners_copy[:N_SPLIT]
    #     del winners_copy[:N_SPLIT]
    #     # spotify.playlist_add_items(ID_WAITING_ROOM, winners)
    #     logging.debug(winners)
    #     spotify.playlist_add_items(ID_PLAYLIST, winners)
        
    # return torio_songs   
    # ------------------------------- FINE RECUPERO SONG ------------------------------ #
    
    #* Extraction of waiting room's songs
    torio_songs = {}
    waiting_room = spotify.playlist_items(ID_WAITING_ROOM, fields=FILTER) # Inserisco il filtro per ottenere solo i campi che mi servono
    
    #* Formatting of waiting room's songs
    while True:
        items = waiting_room["items"]
        
        # Struttura di spotify scomoda perché annidata.
        # Creo un dict dove le chiavi sono le uri delle canzoni mentre i valori sono dei contatori inizializzati a zero
        torio_songs = add_uris_to_dict(torio_songs, items)
        
        # Struttura necessaria per ottenere le successive 100 canzoni
        next = {"next": waiting_room["next"]}
        logging.debug("Next: " + str(next))
        if(next["next"] == None):
            logging.info("No more pages")
            break
        else:
            logging.info("Another page found")
            waiting_room = None
            waiting_room = spotify.next(next)
    logging.info(f"Lunghezza playlist: {len(torio_songs)}")
    logging.debug(f"Torio songs: {torio_songs}")
            
    #* Extraction of torio's member's playlists
    user_songs = {} # Dict dove le chiavi sono i nomi dei proprietari della playlist e i valori sono le liste di canzoni nella playlist
    for user, id_playlist in IDS_PLAYLISTS.items():
        logging.info(f"Extracting user {user} playlist: {id_playlist}" )
        playlist = None
        playlist = spotify.playlist_items(id_playlist, fields=FILTER)
        
        while True:
            items = playlist["items"]
            
            # Nel caso non ci sia lo inizializzo altrimenti da errore
            if user not in user_songs:
                user_songs[user] = []   
            user_songs[user] = add_uris_to_list(user_songs[user], items)
                    
            # Struttura necessaria per ottenere le successive 100 canzoni
            next = {"next": playlist["next"]}
            logging.debug("Next: " + str(next))
            if(next["next"] == None):
                logging.info("No more pages")
                break
            else:
                logging.info("Another page found")
                playlist = None
                playlist = spotify.next(next)
        logging.debug(f"All {user} songs: {user_songs[user]}")
        
        #* Controllo dei mi piace nelle varie playlist
        for song in user_songs[user]:
            if(song in torio_songs):
                # Aumento il counter nel caso la canzone sia presente in una delle playlist dei membri di torio
                torio_songs[song] += 1
        
    #* Decido il numero di like necessari per essere aggiunti alla playlist ufficiali
    # Viene deciso in base a quanti membri hanno mandato la playlist
    required_like = 0
    if(len(IDS_PLAYLISTS)<=MIN_LIKE): 
        # Se il numero delle playlist è minore od uguale del numero minimo di playlist (4)
        required_like = len(IDS_PLAYLISTS)
    else:
        # Se il numero delle playlist è maggiore del numero minimo di playlist (4)
        # divido il numero delle playlist per 3 e arrotondo per eccesso
        required_like = ceil(len(IDS_PLAYLISTS)/3)
        
        # Se l'operazione precedente è minore del numero minimo di playlist (4)
        if(required_like<MIN_LIKE):
            required_like = MIN_LIKE
    logging.info(f"Required like to be added to the official playlist: {required_like}")
    
    #* Salvo le canzoni che hanno superato i like minimi
    winner_songs = []
    for uri, like in torio_songs.items():
        if like>=required_like:
            logging.debug(f"Winner song: {uri}, aggiuta da {like} persone")
            winner_songs.append(uri)
    
    #* Rimuovo le canzoni vincitrici dagli oggetti corrispondenti alle playlist dei membri
    # Questo perché successivamente questi dict verranno usati per rimuore le canzoni che non hanno raggiunti i requisiti
    # Facendo così vengono lasciate solo le canzoni vincitrici nelle playlist dei membri
    for winner_song in winner_songs:
        for user, songs in user_songs.items():
            # Se non ha la canzone passa al ciclo successivo
            if winner_song not in songs:
                continue
            
            # Altrimenti rimuovi la canzone
            user_songs[user].remove(winner_song)
        
    #* Rimuovo le canzoni che non hanno raggiunti i requisiti dalle playlist dei membri
    N_SPLIT = 100 # Numero di canzoni rimosse a ciclo      
    for user, playlist in IDS_PLAYLISTS.items():
    # for user, playlist in {"Nicola": ID_PLAYLIST}.items():
        user_song = user_songs[user] # Canzoni della playlist dello user
        logging.debug(f"Numero canzoni nella playlist di {user}: {len(user_song)}")
        while (len(user_song)!=0):
            remove_list = user_song[:N_SPLIT]
            del user_song[:N_SPLIT]
            spotify.playlist_remove_all_occurrences_of_items(playlist, remove_list)
    
    #* Ottengo le canzoni nella playlist di backup
    # Questo perché successivamente si deve controllare se le canzoni in waiting room sono già presenti nel backup 
    playlist = None
    playlist = spotify.playlist_items(ID_BACKUP, fields=FILTER)
    backup_songs = []
    while True:
        items = playlist["items"]
        
        backup_songs = add_uris_to_list(backup_songs, items)
                
        next = {"next": playlist["next"]}
        logging.debug("Next: " + str(next))
        if(next["next"] == None):
            logging.info("No more pages")
            break
        else:
            logging.info("Another page found")
            playlist = None
            playlist = spotify.next(next)
    
    #* Aggiungo al backup le canzoni che non sono già presenti
    torio_uris = list(torio_songs.keys())
    for torio_uri in torio_uris:
        if torio_uri not in backup_songs:
            spotify.playlist_add_items(ID_BACKUP, [torio_uri]) 
            
    #* Rimuovo tutte le canzoni da waiting room
    while (len(torio_uris)!=0):
        remove_list = torio_uris[:N_SPLIT]
        del torio_uris[:N_SPLIT]
        spotify.playlist_remove_all_occurrences_of_items(ID_WAITING_ROOM, remove_list)
        
    #* Aggiungo le canzoni vincitrici a waiting room
    winners_copy = winner_songs.copy()
    while (len(winners_copy)!=0):
        print(len(winners_copy))
        winners = winners_copy[:100]
        del winners_copy[:100]
        spotify.playlist_add_items(ID_WAITING_ROOM, winners)
        spotify.playlist_add_items(ID_PLAYLIST, winners)
    
    #TODO MEttere che la rimozione delle canzoni non è totale ma solo delle interessate. allo stesso modo dell'inserimento.
    
    #* Ottengo le canzoni nella playlist di backup
    # Questo perché successivamente si deve controllare se le canzoni in waiting room sono già presenti nel backup 
    playlist = None
    playlist = spotify.playlist_items(ID_BACKUP, fields=FILTER)
    backup_songs = []
    while True:
        items = playlist["items"]
        
        backup_songs = add_uris_to_list(backup_songs, items)
                
        next = {"next": playlist["next"]}
        logging.debug("Next: " + str(next))
        if(next["next"] == None):
            logging.info("No more pages")
            break
        else:
            logging.info("Another page found")
            playlist = None
            playlist = spotify.next(next)
    
    #* Aggiungo al backup le canzoni che non sono già presenti
    torio_uris = list(torio_songs.keys())
    for torio_uri in torio_uris:
        if torio_uri not in backup_songs:
            spotify.playlist_add_items(ID_BACKUP, [torio_uri]) 
            
    print(f"--- TIME OF EXECUTION {time.time() - start_time}---")
    return winner_songs
    # return len(winner_songs) """
    
#* Home route
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


#* The external page then redirect us to this page after you complete the login
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

#* spotify_oauth
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
    
    
#* get_token
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
   
     
# ANCHOR -Flask app run   
print(f"localhost:{PORT}")
app.run(port=PORT, debug=True)