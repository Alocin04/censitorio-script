# ---------------------------------- LIBRARY --------------------------------- #
import os
import json
import time
from math import ceil

import logging
logging.basicConfig(filename='censitorio.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

from spotify_class import SpotifyClient
from utility import create_counter_dict

# ------------------------------- CONSTANTS ---------------------------------- #
""" With the filter 'next, items.track.uri, items.track.name' the returned structure is:
{
    'items': [
        {
            'track': {
                'name': "Name of song", 
                'uri': 'spotify:track:6vn8dvUpDC4YeaAh3BI25r'
            }
        }
    ], 
    'next': 'https://api.spotify.com/v1/playlists/4sAt49W9paJp0PJMWElkFs/tracks?offset=100&limit=100&additional_types=track&fields=next,%20items.track.uri,%20items.track.name'
}
"""
FILTER = "next, items.track.uri, items.track.name" # Filter's a costant because we don't need anything else but the name (for logging) and the id

start_time = time.time() # To calculate execution time

# ------------------------------ AUTHENTICATION ------------------------------ #
logging.info("Starting authentication process...")
scope = "playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public" # Scope for reading and modifying private playlists
spotify_client = SpotifyClient(scope)
spotify_client.auth()
# print(spotify_client)
logging.info("Ended authentication process")


# ------------------------------- PLAYLISTS ---------------------------------- #
logging.info("Starting playlists' ids extraction...")
with open('playlists.json') as file:
    PLAYLISTS = json.load(file) # JSON with all the data structure related to playlists
logging.info("Ended playlists' ids extraction")
logging.debug(f"Playlists' ids: {PLAYLISTS}")
    

# ------------------------------- CREATE BACKUP ------------------------------ #
logging.info("Starting backup process...")
""" 
    This section creates a monthly backup for each playlist in the "monthly_backup_playlists" structure.
    It's used if there is a problem in the code and you want to restore the playlists to the previous state.
    It can also add the songs in a general backup playlist, to track all the songs that have ever been added to a certain playlist
    This section CAN BE COMMENTED OUT if you don't want to create a monthly backup or a general backup.
"""
monthly_backup_playlists = PLAYLISTS["monthly_backup_playlists"] # dictionary with all the backup playlists for the songs of the current month
logging.debug(f"Monthly backup playlists: {monthly_backup_playlists}")
if len(monthly_backup_playlists) > 0:
    for key, ids in monthly_backup_playlists.items():
        logging.info(f"Starting backup for {key} playlist...")
        playlist_id = ids["playlist_id"]
        # Get the tracks from the playlist
        """ With the filter 'next, items.track.uri, items.track.name' the returned structure is:
        [
            {
                'track': {
                    'name': "Name of song", 
                    'uri': 'spotify:track:6vn8dvUpDC4YeaAh3BI25r'
                }
            }
        ]
        """
        playlist_songs = spotify_client.get_songs_from_playlist(playlist_id, FILTER)
        logging.debug(f"Playlist songs: {playlist_songs}")
        playlist_uris = spotify_client.get_uris_from_songs(playlist_songs) # Get a list with all the playlist's songs' uris
        # logging.debug(f"Playlist uris: {playlist_uris}")
        # spotify_client.remove_local_songs_from_playlist(playlist_uris, playlist_id) 
        
        # Creation of the monthly backup playlist
        if "backup_id" in ids:
            backup_id = ids["backup_id"]
            logging.debug(f"Backup id: {backup_id}")
            backup_songs = spotify_client.get_songs_from_playlist(backup_id, FILTER)
            logging.debug(f"Backup songs: {backup_songs}")
            backup_uris = spotify_client.get_uris_from_songs(backup_songs) # Get a list with all the playlist's songs' uris
            # logging.debug(f"Backup uris: {backup_uris}")
            
            #* Deletion of the songs in the backup
            # The backup is monthly, so it "restart" the playlist everytime and then add the current months songs
            # So the backup will always be the exact copy of the current playlist
            # spotify_client.delete_songs_from_playlist(backup_uris, backup_id)
            #* Addition of the songs in the backup
            # spotify_client.add_songs_to_playlist(playlist_uris, backup_id)
        
        # Creation of the general backup playlist
        if "general_backup_id" in ids:
            general_backup_id = ids["general_backup_id"]
            logging.debug(f"General backup id: {general_backup_id}")
            general_backup_songs = spotify_client.get_songs_from_playlist(general_backup_id, FILTER)
            logging.debug(f"General backup songs: {general_backup_songs}")
            general_backup_uris = spotify_client.get_uris_from_songs(general_backup_songs) # Get a list with all the playlist's songs' uris
            # logging.debug(f"General backup uris: {general_backup_uris}")
            
            #* Filtering songs that are already in the general backup
            new_songs = []
            for uri in playlist_uris:
                if not uri in general_backup_uris and not uri in new_songs:
                    new_songs.append(uri)
            # spotify_client.add_songs_to_playlist(new_songs, general_backup_id)
logging.info("Ended backup process")


# ------------------------------ UPDATE PLAYLIST ----------------------------- #
logging.info("Starting playlist creation process...")
""" 
    This section gets the songs in the waiting room playlist and creates a dict, where keys are the songs' uri and the value is a counter.
    It's used to know how many people likes the song. With "likes the song" we mean that the song is present in the personal playlist of the user. 
    Because we need to know how many people like the song, then we will get the songs from the personal playlists of the users.
    The dict is then used to update the official playlist:
    removing the songs that have not reached the minimum number of likes and adding the ones that have reached the minimum number of likes.
"""
#* Creation of waiting room's structure and variables, used for the whole elaboration
waiting_room_id = PLAYLISTS["waiting_room_id"]
waiting_room_songs = spotify_client.get_songs_from_playlist(waiting_room_id, FILTER)
# logging.debug(f"Waiting room's songs: {waiting_room_songs}")
waiting_room_uris = spotify_client.get_uris_from_songs(waiting_room_songs)
# logging.debug(f"Waiting room's uris: {waiting_room_uris}")
waiting_room_dict = spotify_client.create_songs_dict(waiting_room_songs) # Used for more readable logging
logging.debug(f"Waiting room's dict: {waiting_room_dict}")

# spotify_client.remove_local_songs_from_playlist(waiting_room_uris, waiting_room_id) # Deletion of local songs (they can't be added)
songs_likes = create_counter_dict(waiting_room_uris) # Dict where it will be stored the number of likes for each song

""" 
    The structure inizialized in the code below will be used to create a JSON with which person voted each songs.
    It's a optional feature, used only if you are curious about what your friends voted or liked. It CAN BE COMMENTED OUT. 
    With this code you will also have to comment other section. They will be marked with a comment saying #!MONTHLY STATISTICS
"""
#!MONTHLY STATISTICS
monthly_statistics = {
    "songs": {},
    "songs_added": {
        "number": 0,
        "songs": {}
    },
    "songs_removed_from_universal": {
        "number": 0,
        "songs": {}
    },
    "songs_removed_from_waiting_room": {
        "number": 0,
        "songs": {}
    }
}
for uri in waiting_room_uris:
    if uri in monthly_statistics:
        continue
    song_data = waiting_room_dict[uri]
    monthly_statistics["songs"][uri] = {
        "name": song_data["name"],
        "counter": 0,
        "votes": [],
    }
# print(len(monthly_statistics))
# print(len(waiting_room_dict))
# print(len(waiting_room_uris))

#* Counting likes for each song
personal_playlists_ids = PLAYLISTS["personal_playlists_ids"]
users_playlists = {} # Used to avoid the same API request more than once per execution in further elaboration ("CLEANING PERSONAL PLAYLIST" section)
for user, id_playlist in personal_playlists_ids.items():
    logging.info(f"Extracting user {user}'s playlist: {id_playlist}")
    
    user_playlist_songs = spotify_client.get_songs_from_playlist(id_playlist, FILTER)
    logging.debug(f"User playlist's songs: {user_playlist_songs}")
    user_playlist_uris = set(spotify_client.get_uris_from_songs(user_playlist_songs)) # It cast the list into a set to remove the duplicates

    if (len(user_playlist_uris)<10):
        logging.warning(f"{user}'s playlist is empty or almost empty, so it won't count")
        continue
    
    users_playlists[user] = user_playlist_uris
    for uri in user_playlist_uris:
        # User could add songs, which are not present in waiting room, to their personal playlist. This if is needed to filter them
        if (uri in songs_likes):
            songs_likes[uri] += 1
            
            #!MONTHLY STATISTICS
            monthly_statistics["songs"][uri]["counter"] += 1
            if not (user in monthly_statistics["songs"][uri]["votes"]):
                monthly_statistics["songs"][uri]["votes"].append(user)
logging.debug(f"Songs' likes: {songs_likes}")

#* Calculating minimum number of likes that a song need to be added to the universal playlist
"""  
    I didn't find a simple algorithm that calculates the required like using the number of users
    that will be used with both small number and huge number.
    Then I thought: "This project is aimed for friends groups, who will be use this with more than 15-20 people?"
    So I choose to do a simple if, but if you found a better way let me know   
"""
required_like = 0
playlists_number = len(users_playlists)
logging.info(f"Number of valid playlists: {playlists_number}")
# This if can be changed based on you friends group
if playlists_number <= 3:
    required_like = playlists_number
elif playlists_number >= 4 and playlists_number <= 6:
    required_like = 3
elif playlists_number >= 7 and playlists_number <= 8:
    required_like = 4
elif playlists_number >= 9 and playlists_number <= 11:
    required_like = 5
elif playlists_number >= 12 and playlists_number <= 15:
    required_like = 6
elif playlists_number >= 16 and playlists_number <= 20:
    required_like = 7
logging.info(f"Required like to be added to the official playlist: {required_like}")
    
#* Extraction of the universal playlist songs    
universal_playlist_id = PLAYLISTS["universal_playlist_id"]
universal_playlist_songs = spotify_client.get_songs_from_playlist(universal_playlist_id, FILTER)
logging.debug(f"Universal playlist's songs: {universal_playlist_songs}")
universal_playlist_uris = spotify_client.get_uris_from_songs(universal_playlist_songs)
# logging.debug(f"Universal playlist's uris: {waiting_room_uris}")

#* Updating the universal playlist with new songs that have received enough likes 
winner_songs = []
for uri, likes in songs_likes.items():
    if likes>=required_like and not (uri in universal_playlist_uris) and not (uri in winner_songs):
        logging.info(f"Winner song: {waiting_room_dict[uri]['name']} ({uri}), added by {likes} people")
        winner_songs.append(uri)
        
        #!MONTHLY STATISTICS
        song_data = monthly_statistics["songs"][uri]
        monthly_statistics["songs_added"]["songs"][uri] = song_data
        
# spotify_client.add_songs_to_playlist(winner_songs.copy(), universal_playlist_id) # It use a copy because winner_songs could be used again later

#* Removing from the universal playlist the songs that have not received enough likes 
""" 
    Because anyone can remove a song from waiting room, even after it's added to the universal playlist,
    the program checks if the uris in universal_playlist_uris are in waiting room, 
    if yes checks the likes, otherwise it removes the songs.
    If you want to remove only the songs that haven't enough likes, use the second method.
"""
loser_songs  = []
#METHOD 1: keeps only winner songs
for uri in universal_playlist_uris:
    if not (uri in waiting_room_uris):
        logging.warning(f"Song not present in waiting room: {uri}, removed from universal playlist")
        loser_songs.append(uri)
        
        monthly_statistics["songs_removed_from_universal"]["songs"][uri] = {} #!MONTHLY STATISTICS
        
        continue
    likes = songs_likes[uri] # it doesn't check if it's in songs_likes because it has the same uris as waiting_room_uris 
    if likes<required_like and not (uri in loser_songs):
        name = waiting_room_dict[uri]["name"]
        logging.info(f"Universal loser song: {name} ({uri}), added by {likes} people")
        loser_songs.append(uri)
        
        #!MONTHLY STATISTICS
        song_data = monthly_statistics["songs"][uri]
        monthly_statistics["songs_removed_from_universal"]["songs"][uri] = song_data
        
#METHOD 2: removes only loser songs
# for uri, likes in songs_likes.items():
#     if likes<required_like and uri in universal_playlist_uris and not (uri in loser_songs):
#         logging.info(f"Loser song: {waiting_room_dict[uri]["name"]} ({uri}), added by {likes} people")
#         loser_songs.append(uri)

#         #!MONTHLY STATISTICS
#         song_data = monthly_statistics["songs"][uri]
#         monthly_statistics["songs_removed_from_universal"]["songs"][uri] = song_data

# spotify_client.delete_songs_from_playlist(loser_songs.copy(), universal_playlist_id) # It use a copy because loser_songs could be used again later

monthly_statistics["songs_removed_from_universal"]["number"] = len(loser_songs) #!MONTHLY STATISTICS


# --------------------------- CLEANING WAITING ROOM -------------------------- #
# Removes the songs that haven
logging.info(f"Cleaning waiting room...")
loser_songs.clear()
for uri, likes in songs_likes.items():
    if likes<required_like  and not (uri in loser_songs):
        logging.info(f"Waiting room loser song: {waiting_room_dict[uri]['name']} ({uri}), added by {likes} people")
        loser_songs.append(uri)
        
        #!MONTHLY STATISTICS
        song_data = monthly_statistics["songs"][uri]
        monthly_statistics["songs_removed_from_waiting_room"]["songs"][uri] = song_data
# spotify_client.delete_songs_from_playlist(loser_songs.copy(), waiting_room_id) # It use a copy because loser_songs could be used again later

monthly_statistics["songs_removed_from_waiting_room"]["number"] = len(loser_songs) #!MONTHLY STATISTICS


# ------------------------ CLEANING PERSONAL PLAYLISTS ----------------------- #
"""
    Because users can add any songs to their personal playlist, 
    the program removes any playlist's song that isn't in winner_songs. 
    Using this it clean the playlist, removing the loser songs and the one that aren't in waiting room.
    If you want, you can remove only the loser songs using the second method and commentating the first.
"""
#METHOD 1: keeps only winner songs
for user, uris in users_playlists.items():
    logging.info(f"Cleaning {user}'s playlist...")
    
    #!MONTHLY STATISTICS
    monthly_statistics["songs_removed_from_"+user] = {
        "number": 0,
        "songs": {}
    }
    
    loser_songs.clear()
    for uri in uris:
        if not (uri in waiting_room_uris):
            logging.warning(f"Song not present in waiting room: {uri}, removed from personal playlist")
            loser_songs.append(uri)
            
            monthly_statistics["songs_removed_from_"+user]["songs"][uri] = {} #!MONTHLY STATISTICS
            
            continue
        likes = songs_likes[uri] # it doesn't check if it's in songs_likes because it has the same uris as waiting_room_uris 
        if likes<required_like and not (uri in loser_songs):
            name = waiting_room_dict[uri]["name"] # it doesn't check if it's in waiting_room_dict because it has the same uris as waiting_room_uris
            logging.debug(f"User loser song: {name} ({uri}), added by {likes} people")
            loser_songs.append(uri)
            
            #!MONTHLY STATISTICS
            song_data = monthly_statistics["songs"][uri]
            monthly_statistics["songs_removed_from_"+user]["songs"][uri] = song_data
    # spotify_client.delete_songs_from_playlist(loser_songs.copy(), personal_playlists_ids[user])
    
    monthly_statistics["songs_removed_from_"+user]["number"] = len(loser_songs) #!MONTHLY STATISTICS
    
#METHOD 2: removes only loser songs
# for user, playlist_id in personal_playlists_ids.items():
#     logging.info(f"Cleaning {user}'s playlist...")
#     spotify_client.delete_songs_from_playlist(loser_songs.copy(), playlist_id)



# --------------------------- MONTHLY STATISTICS --------------------------- #    
with open("monthly_statistics.json", "w") as f:
    json.dump(monthly_statistics, f)
    
print(f"--- TIME OF EXECUTION {time.time() - start_time}---")
    