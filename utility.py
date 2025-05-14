import requests
import re
import unicodedata
import logging

from datetime import datetime, timedelta, timezone
import time
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------- #
#                                     DATE                                     #
# ---------------------------------------------------------------------------- #
# def get_offset(date, timezone):
#     date_time=dateutil.parser.parse(date)
#     print(f"Date: {date_time}")
#     timestamp=time.mktime(date_time.timetuple())
#     print(f"Timestamp: {timestamp}")
#     date_str = datetime.fromtimestamp(timestamp, tz=timezone.).strftime('%FT%XZ')
#     print(f"Datetime: {date_str}")
    
#     return date_str
# get_offset("2024-10-10", "Europe/Rome")

def get_utc_date(date):
    timestamp=time.mktime(date.timetuple())
    # print(f"Timestamp: {timestamp}")
    date_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    # print(f"Datetime: {date_utc}")
    
    return date_utc

def get_timezone_date(date, timezone):
    # date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
    # print(f"Date: {date}")
    # date_timezone = date.astimezone(ZoneInfo(timezone))
    # date_timezone = date.replace(ZoneInfo(timezone))
    # date_timezone = ZoneInfo(timezone).fromutc(date)
    date_timezone = date + ZoneInfo(timezone).utcoffset(date)
    # print(ZoneInfo(timezone).fromutc())
    # print(f"Date with Offset: {date_timezone.strftime('%Y-%m-%dT%H:%M:%S')}")
    
    return date_timezone
# print(get_timezone_date("2025-01-10T23:00:00", "Europe/Rome"))
# print(get_timezone_date("2025-01-17T22:59:00", "Europe/Rome"))
# --------------------------------- FINE DATE -------------------------------- #


# ---------------------------------------------------------------------------- #
#                                     DICT                                     #
# ---------------------------------------------------------------------------- #
def create_counter_dict(keys: list) -> dict:
    """Adds keys and 0 as value to a dict

    Args:
        keys: the structure that contains the keys of the returned dict

    Returns:
        counters_dict: the dict with the format "uris: 0" (key: value)
    """
    counters_dict = {}
    for key in keys:
        logging.debug("Item of the playlist: " + str(key))
        
            
    logging.info(f"Playlist's lenght: {len(counters_dict)}")
    logging.info(f"Playlist's songs: {counters_dict}")
    
    return counters_dict
# --------------------------------- FINE DICT -------------------------------- #


# ---------------------------------------------------------------------------- #
#                                 GENERAL UTIL                                 #
# ---------------------------------------------------------------------------- #
def get_data(url, headers):
    response=requests.get(url, headers=headers)
    return response

def send_data(url, headers, data):
    # request = Request('https://private-anon-7cbb88c2ee-megaphoneapi.apiary-mock.com/networks/network_id/podcasts', data=values, headers=headers)
    # response_body = urlopen(request).read()
    # print(response_body)
    response=requests.post(url, headers=headers, json=data)
    return response

def put_data(url, headers, data):
    # request = Request('https://private-anon-7cbb88c2ee-megaphoneapi.apiary-mock.com/networks/network_id/podcasts', data=values, headers=headers)
    # response_body = urlopen(request).read()
    # print(response_body)
    response=requests.put(url, headers=headers, json=data)
    return response

def handle_status(status):
    if(status==200):
        #logging.info('200 OK')
        print("OK! 200")
        return True
    if(status==201):
        #logging.info('200 OK')
        print("OK! 201")
        return True
    if(status==202):
        #logging.info('200 OK')
        print("OK! 202")
        return True
    if(status==203):
        #logging.info('200 OK')
        print("OK! 203")
        return True
    if(status==400):
        #logging.error('400 Bad Request')
        print("Error 400!")
        return False
    if(status==401):
        #logging.error('401 Unauthorized')
        print("Error 401!")
        return False
    if(status==404):
        #logging.error('404 Not Found')
        print("Error 404!")
        return False
    if(status==500):
        #logging.error('500 Internal Server Error')
        print("Error 500!")
        return False

def is_null(var):
    if(not var):
        if(var == 0):
            return False
        else:
            return True
    else:
        return False
    
def format_vanity(vanity):
    # vanity = vanity.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    # vanity = vanity.replace(/\'/g, "-");
    # vanity = vanity.replace(/\s/g, '-');
    # vanity = vanity.replace(/[^a-zA-Z0-9\- ]/g, "");
    # return vanity;
    vanity = re.sub('[\u0300-\u036f]', "", unicodedata.normalize("NFD", vanity.lower()))
    # print(vanity)
    vanity = re.sub('\'', "-", vanity)
    # print(vanity)
    vanity = re.sub("\s", '-', vanity)
    # print(vanity)
    vanity = re.sub("[^a-zA-Z0-9\-_ ]", "", vanity)
    # print(vanity)
    return vanity
# ----------------------------- FINE GENERAL UTIL ---------------------------- #