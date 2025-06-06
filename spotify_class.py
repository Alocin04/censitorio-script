from dotenv import load_dotenv, find_dotenv # library for reading file .env
load_dotenv(find_dotenv())

import spotipy # Spotify API
from spotipy.oauth2 import SpotifyOAuth

import os
import logging

class SpotifyClient:
    """ SpotifyClient class to interact with the Spotify API using the spotipy library.
    This class handles authentication and provides methods to interact with Spotify playlists.
    """
    
    def __init__(self, scope: str):
        self._client_id = os.getenv("CLIENT_ID")
        self._client_secret = os.getenv("CLIENT_SECRET")
        self._redirect_uri = os.getenv("REDIRECT_URI")
        self._scope = scope
        self._spotipy = None

    def auth(self) -> None:
        """ Authenticate with Spotify API (spotipy library) using credentials from .env file """
        auth_manager = SpotifyOAuth(
            client_id = self._client_id,
            client_secret = self._client_secret,
            redirect_uri = self._redirect_uri,
            scope = self._scope
        )

        self._spotipy = spotipy.Spotify(auth_manager=auth_manager)
        
    def get_songs_from_playlist(self, id_playlist: str, filter: str = "") -> list:
        """Extracts all the songs from a playlist, the returned structure depends on the filter used

        Args:
            id_playlist (str): id of the spotify playlist
            filter (str): the filter used to extract only certain fields

        Returns:
            playlist (list): the formatted list containing the songs' data
        """
        if (filter != ""):
            songs = self._spotipy.playlist_items(id_playlist, fields=filter)
        else:
            songs = self._spotipy.playlist_items(id_playlist)
        
        playlist = []
        iterations = 0
        while True:
            items = songs["items"]
            iterations += 1
            logging.debug(f"Iteration n°{iterations}")
            
            playlist.extend(items)
            
            # Structure used to extract the next page of songs (max 100 items per page)
            next = {"next": songs["next"]}
            logging.debug("Next: " + str(next))
            if(next["next"] == None):
                logging.info("No more pages")
                break
            else:
                logging.info("Another page found")
                songs = None
                songs = self._spotipy.next(next)
        
        return playlist
    
    def get_uris_from_songs(self, songs: list) -> list:
        """Extracts the uris from the songs' list

        Args:
            songs (list): list of dictionaries containing the songs' data
            Each dictionary has the following structure:
            [
                {
                    'track': {
                        'name': "Name of song", 
                        'uri': 'spotify:track:6vn8dvUpDC4YeaAh3BI25r',
                        ...: ...,
                    }
                }
            ]

        Returns:
            uris (list): list of uris
        """
        uris = []
        for song in songs:
            if not "track" in song:
                logging.warning(f"Song not valid: {song}")
                continue
            if song["track"] == None:
                logging.warning(f"Song not valid: {song}")
                continue
            track = song["track"]
            if not "uri" in track:
                logging.warning(f"Song not valid: {track}")
                continue
            if track["uri"] == None:
                logging.warning(f"Song not valid: {track}")
                continue
            uris.append(track["uri"])
        
        return uris
    
    def create_songs_dict(self, songs: list) -> dict:
        """Extracts the songs' data from the returned structure of the Spotify API
        and creates a dict with the format "uri: {name: name, artist: artist, ...}"

        Args:
            songs (list): list of dictionaries containing the songs' data
            Each dictionary has the following structure:
            [
                {
                    'track': {
                        'name': "Name of song", 
                        'uri': 'spotify:track:6vn8dvUpDC4YeaAh3BI25r',
                        ...: ...,
                    }
                }
            ]

        Returns:
            songs_dict (dict): dict of songs
        """
        songs_dict = {}
        for song in songs:
            
            if not "track" in song:
                continue
            if song["track"] == None:
                continue
            track = song["track"]
            songs_dict[track["uri"]] = track
            songs_dict[track["uri"]].pop("uri")
        
        return songs_dict
    
    def add_songs_to_playlist(self, songs: list, playlist_id: str) -> None:
        """Add songs from a playlist

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
            self._spotipy.playlist_add_items(playlist_id, add_list)
    
    def delete_songs_from_playlist(self, songs: list, playlist_id: str) -> None:
        """Delete songs from a playlist

        Args:
            songs: the list that contains the songs' uri
            playlist_id: playlist's id
        """
        logging.info(f"Number of songs which will be removed: {len(songs)}")
        SPLIT = 100 # Number removed per loop
        while (len(songs)!=0):
            remove_list = songs[:SPLIT]
            del songs[:SPLIT]
            # print(remove_list)
            self._spotipy.playlist_remove_all_occurrences_of_items(playlist_id, remove_list)
    
    def remove_local_songs_from_playlist(self, songs: list, playlist_id: str) -> list:
        """Remove local songs from the playlist and from the list of songs

        Args:
            songs: the list that contains the songs' uri

        Returns:
            local_songs: the list of local songs
        """
        local_songs = []
        for song in songs:
            # EX of uri: 
            if (song.split(":")[1] == "local"):
                local_songs.append(song)
                songs.remove(song)
        
        self.delete_songs_from_playlist(local_songs, playlist_id)
        logging.info(f"Number of local songs removed: {len(local_songs)}")
        logging.debug(f"Local songs: {local_songs}")        
        
        return local_songs
