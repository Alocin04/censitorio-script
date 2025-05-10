# ---------------------------------- LIBRARY --------------------------------- #
import os
import json

import logging
logging.basicConfig(filename='censitorio.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

from spotify_class import SpotifyClient

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
        logging.debug(f"Playlist uris: {playlist_uris}")
        
        # Creation of the monthly backup playlist
        if "backup_id" in ids:
            backup_id = ids["backup_id"]
            logging.debug(f"Backup id: {backup_id}")
            backup_songs = spotify_client.get_songs_from_playlist(backup_id, FILTER)
            logging.debug(f"Backup songs: {backup_songs}")
            backup_uris = spotify_client.get_uris_from_songs(backup_songs) # Get a list with all the playlist's songs' uris
            logging.debug(f"Backup uris: {backup_uris}")
            
            #* Deletion of the songs in the backup
            # The backup is monthly, so it "restart" the playlist everytime and then add the current months songs
            # So the backup will always be the exact copy of the current playlist
            spotify_client.delete_songs_from_playlist(backup_uris, backup_id)
            #* Addition of the songs in the backup
            spotify_client.add_songs_to_playlist(playlist_uris, backup_id)
        
        # Creation of the general backup playlist
        if "general_backup_id" in ids:
            general_backup_id = ids["general_backup_id"]
            logging.debug(f"General backup id: {general_backup_id}")
            general_backup_songs = spotify_client.get_songs_from_playlist(general_backup_id, FILTER)
            logging.debug(f"General backup songs: {general_backup_songs}")
            general_backup_uris = spotify_client.get_uris_from_songs(general_backup_songs) # Get a list with all the playlist's songs' uris
            logging.debug(f"General backup uris: {general_backup_uris}")
            
            #* Filtering songs which are already in the general backup
            new_songs = []
            for uri in playlist_uris:
                if not uri in general_backup_uris and not uri in new_songs:
                    new_songs.append(uri)
            spotify_client.add_songs_to_playlist(new_songs, general_backup_id)
logging.info("Ended backup process")


# ID_WAITING_ROOM = PLAYLISTS["ID_WAITING_ROOM"]
#   "ID_PLAYLIST"
#   "ID_SONGS_BACKUP"
#   "ID_TEST"
#   "IDS_PLAYLISTS"
# results = spotify_client.playlist_tracks(ID_WAITING_ROOM)
# print(results)