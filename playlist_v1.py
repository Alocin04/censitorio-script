import logging

ID_WAITING_ROOM = "4sAt49W9paJp0PJMWElkFs"
ID_PLAYLIST = "4YRJXy4XrbPvsYl1Gcn03E"
ID_BACKUP = "60HoslluDzVSfTpKghxbmC"
ID_TEST = "4HmCfWawMNq1Bnvawgy8pB"
IDS_BACKUP = {
    "ID_BACKUP_WAITING_ROOM": "5IkPMTHii0yy8PxkHaFGbB",
    "ID_BACKUP_MOMENTO_TORIO": "5u4SlTRwaLnaxmiYwnmMQm",
    "ID_BACKUP_MIA_PLAYLIST": "56BxJ9OeY9iQgLrPxYvPnM",
}
IDS_PLAYLISTS = {
                # "Adel": "5Q5tbNVFad5cxSLrqP4cJq",
                # "Alessia": "08vu4v41HpAtFDYK2ukSEI",
                "Arianna": "56s8469bgh0CT5J0gzQKij",
                "Colletti": "2kcVxGZrI2dgG3lentrQEK",
                # "Dedo": "606h9qHIgjXpu6YisRKA26",
                "Di Maria": "26VIRC6eT0tjBTFloShpi1",
                "Lorenzo": "0D1Jr4uzXF3oppoyLUh9ra",
                "Nicola": "1XiiJ7SI3JkI0scBqWeRas",
                # "De Cicco": "1gzFTpBQbufYfQHQ6y8zat",
                "Ruben": "3KFRer87wkYWGGffqInGE7",
                "Daria": "5byikUaf4QYFW4Au5EKqSR",
                "Tiziana": "6Cf2lyJs9G3nzSNxlp2T9p",
                # "Test": "0a2oErpqWJPsWbwwUek5ED"
                
            }
FILTER = "next, items.track.uri, items.track.name"
MIN_LIKE = 4

def soft_reset(spotify, ids):
    # for name, id in IDS_BACKUP.items():
    for name, id in IDS_BACKUP.items():
    # for name, id in IDS_PLAYLISTS.items():
        playlist = get_songs_from_playlist(spotify, id, FILTER)
        uris = get_songs_list(playlist)
        delete_songs_from_playlist(spotify, uris, id)
        logging.info(f"All items in {name}'s playlist has been removed")
        
def hard_reset(spotify):
    # soft_reset(spotify)
    
    # playlist = get_songs_from_playlist(spotify, ID_WAITING_ROOM, FILTER)
    # uris = get_songs_list(playlist)
    # delete_songs_from_playlist(spotify, uris, ID_WAITING_ROOM)
    # logging.info(f"All items in Waiting Room's playlist has been removed")
    
    # playlist = get_songs_from_playlist(spotify, ID_PLAYLIST, FILTER)
    # uris = get_songs_list(playlist)
    # delete_songs_from_playlist(spotify, uris, ID_PLAYLIST)
    # logging.info(f"All items in Momento Torio's playlist has been removed")
    
    # playlist = get_songs_from_playlist(spotify, ID_BACKUP, FILTER)
    # uris = get_songs_list(playlist)
    # delete_songs_from_playlist(spotify, uris, ID_BACKUP)
    # logging.info(f"All items in Backup's playlist has been removed")
    
    playlist = get_songs_from_playlist(spotify, ID_TEST, FILTER)
    uris = get_songs_list(playlist)
    delete_songs_from_playlist(spotify, uris, ID_TEST)
    logging.info(f"All items in Test's playlist has been removed")
    
def remove_duplicate(spotify):
    playlist = get_songs_from_playlist(spotify, ID_TEST, FILTER)
    songs_list = {}
    i = 0
    for song in playlist:
        logging.debug("Item of the playlist: " + str(song))
        if (song["track"]==None):
            continue
        if (song["track"]["uri"]==None):
            continue
        uri = song["track"]["uri"]
        name = song["track"]["name"]
        
        is_local = (uri.split(":")[1] == "local")
        # logging.debug(f"{name} is local? {is_local}")
        if(not is_local):
            logging.debug(f"{name} is not local")
            songs_list[name] = i
        else:
            logging.warning(f"{name}'s local")
        
        i += 1
    item = [{"uri":"spotify:track:7iaqij2YBDjDV6ZAW0VRfc", "positions":[1]}]
    spotify.playlist_remove_specific_occurrences_of_items(ID_TEST, item)
    logging.info(f"Playlist's lenght: {len(songs_list)}")
    logging.info(f"Playlist's songs: {songs_list}")
    return songs_list

def get_songs_from_playlist(spotify, id_playlist, filter):
    # Estrazione delle canzoni nella playlist
    songs = spotify.playlist_items(id_playlist, fields=filter) # Inserisco il filtro per ottenere solo i campi che mi servono
    
    playlist = [] # Playlist da restituire
    iterations = 0
    while True:
        items = songs["items"]
        iterations += 1
        logging.debug(f"Iteration n°{iterations}")
        
        playlist.extend(items)
        
        # Struttura necessaria per ottenere le successive 100 canzoni
        next = {"next": songs["next"]}
        logging.debug("Next: " + str(next))
        if(next["next"] == None):
            logging.info("No more pages")
            break
        else:
            logging.info("Another page found")
            songs = None
            songs = spotify.next(next)
    
    return playlist

def get_counters_dict(songs):
    """Adds uris as key and 0 as value to a dict

    Args:
        songs: the structure that contains the songs' uri

    Returns:
        counters_dict: the dict with the format "uris: 0" (key: value)
    """
    counters_dict = {}
    for song in songs:
        logging.debug("Item of the playlist: " + str(song))
        if (song["track"]==None):
            continue
        if (song["track"]["uri"]==None):
            continue
        uri = song["track"]["uri"]
        name = song["track"]["name"]
        
        is_local = (uri.split(":")[1] == "local")
        # logging.debug(f"{name} is local? {is_local}")
        # Non serve controllare per i duplicati perché non è possibile avere 2 chiavi uguali
        if(not is_local):
            logging.debug(f"{name} is not local")
            counters_dict[uri] = 0
        else:
            logging.warning(f"{name}'s local")
            
    logging.info(f"Playlist's lenght: {len(counters_dict)}")
    logging.info(f"Playlist's songs: {counters_dict}")
    
    return counters_dict

def get_songs_list(songs):
    """Adds uris to a list

    Args:
        songs: the structure that contains the songs' uri

    Returns:
        songs_list: the list containing the songs'uri
    """
    songs_list = []
    for song in songs:
        logging.debug("Item of the playlist: " + str(song))
        if (song["track"]==None):
            continue
        if (song["track"]["uri"]==None):
            continue
        uri = song["track"]["uri"]
        name = song["track"]["name"]
        
        is_local = (uri.split(":")[1] == "local")
        # logging.debug(f"{name} is local? {is_local}")
        if(not is_local):
            # Controllo per duplicati
            if uri not in songs_list:
                logging.debug(f"{name} is not local")
                songs_list.append(uri)
            else:
                logging.warning(f"{name}'s duplicated")
        else:
            logging.warning(f"{name}'s local")
            
    logging.info(f"Playlist's lenght: {len(songs_list)}")
    logging.info(f"Playlist's songs: {songs_list}")
    
    return songs_list

def delete_songs_from_playlist(spotify, songs, playlist):
    """Delete songs from playlist

    Args:
        songs: the list that contains the songs' uri
        playlist: playlist's id
    """
    logging.info(f"Numero canzoni da rimuovere: {len(songs)}")
    SPLIT = 100 # Numero di canzoni rimosse a ciclo 
    while (len(songs)!=0):
        remove_list = songs[:SPLIT]
        del songs[:SPLIT]
        # print(remove_list)
        spotify.playlist_remove_all_occurrences_of_items(playlist, remove_list)
        
def add_songs_to_playlist(spotify, songs, playlist):
    """Add songs from playlist

    Args:
        songs: the list that contains the songs' uri
        playlist: playlist's id
    """
    logging.info(f"Numero canzoni da aggiungere: {len(songs)}")
    SPLIT = 100 # Numero di canzoni rimosse a ciclo 
    while (len(songs)!=0):
        add_list = songs[:SPLIT]
        del songs[:SPLIT]
        # print(add_list)
        spotify.playlist_add_items(playlist, add_list)

#* add_uris_to_dict
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
        if (item["track"]==None):
            continue
        if (item["track"]["uri"]==None):
            continue
        
        uri = item["track"]["uri"]
        is_local = uri.split(":")[1] == "local"
        logging.debug("Is local? " + str(is_local))
        if(not is_local):
            dict[uri] = 0
    
    return dict


#* add_uris_to_list
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
        if (item["track"]==None):
            continue
        if (item["track"]["uri"]==None):
            continue
        
        uri = item["track"]["uri"]
        is_local = uri.split(":")[1] == "local"
        logging.debug("Is local? " + str(is_local))
        if(not is_local and uri not in list):
            list.append(uri)
    
    return list


    # ------------------------------- RIMOZIONE DOPPIONI ------------------------------ #
    """ waiting_room = spotify.playlist_items(ID_PLAYLIST, fields=FILTER) # Inserisco il filtro per ottenere solo i campi che mi servono
    torio_songs = []
    while True:
        items = waiting_room["items"]
        
        # Struttura di spotify scomoda perché annidata.
        # Creo un dict dove le chiavi sono le uri delle canzoni mentre i valori sono dei contatori inizializzati a zero
        for item in items:
            logging.debug("Item of the playlist: " + str(item))
            if (item["track"]==None):
                continue
            if (item["track"]["uri"]==None):
                continue
            
            uri = item["track"]["uri"]
            is_local = uri.split(":")[1] == "local"
            logging.debug("Is local? " + str(is_local))
            if(not is_local and uri not in torio_songs):
                torio_songs.append(uri)
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
        
    logging.debug(torio_songs)
    N_SPLIT = 100 # Numero di canzoni rimosse a ciclo      
    delete_copy = torio_songs.copy()
    while (len(delete_copy)!=0):
        remove_list = delete_copy[:N_SPLIT]
        del delete_copy[:N_SPLIT]
        spotify.playlist_remove_all_occurrences_of_items(ID_PLAYLIST, remove_list)
    
    logging.debug(torio_songs)
    winners_copy = torio_songs.copy()
    while (len(winners_copy)!=0):
        logging.debug(len(winners_copy))
        winners = winners_copy[:N_SPLIT]
        del winners_copy[:N_SPLIT]
        # spotify.playlist_add_items(ID_WAITING_ROOM, winners)
        logging.debug(winners)
        spotify.playlist_add_items(ID_PLAYLIST, winners)
        
    return torio_songs    """
    # ------------------------------- FINE RIMOZIONE DOPPIONI ------------------------------ #