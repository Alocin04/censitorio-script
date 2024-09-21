import logging

ID_WAITING_ROOM = "4sAt49W9paJp0PJMWElkFs"
ID_PLAYLIST = "4YRJXy4XrbPvsYl1Gcn03E"
ID_BACKUP = "60HoslluDzVSfTpKghxbmC"
IDS_PLAYLISTS = {
            #  "Rezza Capa": "1DkkgB2T4qShCdzknEC8Iv",
                "Adel": "5Q5tbNVFad5cxSLrqP4cJq",
                "Alessia": "08vu4v41HpAtFDYK2ukSEI",
                "Arianna": "56s8469bgh0CT5J0gzQKij",
                "Colletti": "2kcVxGZrI2dgG3lentrQEK",
                "Dedo": "606h9qHIgjXpu6YisRKA26",
                "Di Maria": "26VIRC6eT0tjBTFloShpi1",
                "Nicola": "1XiiJ7SI3JkI0scBqWeRas",
            }
FILTER = "next, items.track.uri, items.track.name"
MIN_LIKE = 4

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