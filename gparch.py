import io
import json
import os
import pickle
import sqlite3
from multiprocessing.pool import ThreadPool
from time import time

import piexif
import piexif.helper
import requests
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from PIL import Image
from tqdm import tqdm

"""
Archiver for Google Photos
By: Nick Dawson | nick@ndawson.me
"""

"""
    Archiver For Google Photos
    - A tool to maintain an archive/mirror of your Google Photos library for backup purposes.
    Copyright (C) 2021  Nicholas Dawson

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

VERSION = "2.0.0"

# Define Scopes for Application
SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",  # Read Only Photos Library API
]

# Define constants
DATABASE_NAME = "database.sqlite3"


def safe_mkdir(path):
    """
    Creates directory only if it doesn't exist already to prevent errors
    """
    if not os.path.exists(path):
        os.mkdir(path)


def auto_mkdir(path, instance=0):
    """
    Recursively creates directory and appends a number -> (#) to the end
    if that directory already exists
    """
    if instance:
        new_path = path + " (" + str(instance) + ")"
    else:
        new_path = path

    if not os.path.exists(new_path):
        os.mkdir(new_path)
        return os.path.abspath(new_path)
    else:
        return auto_mkdir(path, instance + 1)


def auto_filename(path, instance=0):
    """
    Recursively finds an available name for a new file and
    appends a number -> (#) to the end if that file already exists
    """
    if instance:
        extension_index = path.rfind(".")
        new_path = (
            path[:extension_index] + " (" + str(instance) + ")" + path[extension_index:]
        )
    else:
        new_path = path

    if not os.path.exists(new_path):
        return new_path
    else:
        return auto_filename(path, instance + 1)


def save_json(variable, path):
    json.dump(variable, open(path, "w"))


def load_json(path):
    # If file exists load the json as a dict
    if os.path.isfile(path):
        return json.load(open(path, "r"))
    # If file doesn't exist return None
    else:
        return None


def load_database(path, init_dict):
    # Create and/or Load the databases
    db = load_json(path)
    if db is None:
        db = init_dict
    save_json(db, path)
    return db


class PhotosAccount(object):
    def __init__(self, credentials_path, directory, thread_count):
        # Define directory instance variables
        self.base_dir = directory
        self.lib_dir = self.base_dir + "/Library"
        self.albums_dir = self.base_dir + "/Albums"
        self.shared_albums_dir = self.base_dir + "/Shared Albums"
        self.favorites_dir = self.base_dir + "/Favorites"

        # Define/initialize other instance variables
        self.thread_count = thread_count
        self.credentials = credentials_path
        self.service = None  # is None because it will be defined later by calling "get_google_api_service"
        self.timer = time()
        self.downloads = 0

        # Define/Init Database
        self.db_path = self.base_dir + "/" + DATABASE_NAME
        self.con = self.init_db()
        self.cur = self.con.cursor()

        # Create the directories (if not already there)
        safe_mkdir(self.base_dir)
        safe_mkdir(self.lib_dir)
        safe_mkdir(self.albums_dir)
        safe_mkdir(self.shared_albums_dir)
        safe_mkdir(self.favorites_dir)

    def get_google_api_service(self):
        # The file photos_token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        credentials = None
        token_path = self.base_dir + "/photoslibrary_token.pickle"

        if os.path.exists(token_path):
            with open(token_path, "rb") as token:
                credentials = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                if not os.path.exists(self.credentials):
                    raise FileNotFoundError(self.credentials + " is not found.")

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials, SCOPES
                )
                credentials = flow.run_local_server()
            # Save the credentials for the next run
            with open(token_path, "wb") as token:
                pickle.dump(credentials, token)

        self.service = build(
            "photoslibrary", "v1", credentials=credentials, static_discovery=False
        )

    def init_db(self):
        if not os.path.exists(self.db_path):
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            # Create Media Table - Used to store basic information about each media item
            cur.execute(
                """CREATE TABLE media (uuid text, path text, album_uuid text)"""
            )
            # Create Albums Table - Used to store information about each album
            cur.execute(
                """CREATE TABLE albums (uuid text, path text, title text, is_shared integer)"""
            )
            con.commit()  # Save changes
            return con
        else:
            return sqlite3.connect(self.db_path)

    def get_session_stats(self):
        return time() - self.timer, self.downloads

    def download_media_item(self, entry):
        try:
            url, path, description = entry
            if not os.path.isfile(path):
                r = requests.get(url)
                if r.status_code == 200:
                    if description:
                        img = Image.open(io.BytesIO(r.content))
                        exif_dict = piexif.load(img.info["exif"])
                        exif_dict["Exif"][
                            piexif.ExifIFD.UserComment
                        ] = piexif.helper.UserComment.dump(
                            description, encoding="unicode"
                        )

                        # This is a known bug with piexif (https://github.com/hMatoba/Piexif/issues/95)
                        if 41729 in exif_dict["Exif"]:
                            exif_dict["Exif"][41729] = bytes(exif_dict["Exif"][41729])

                        exif_bytes = piexif.dump(exif_dict)
                        img.save(path, exif=exif_bytes)
                    else:
                        open(path, "wb").write(r.content)
                    self.downloads += 1
                    return True

            else:
                return False
        except Exception as e:
            print("ERROR: media item could not be downloaded because:", e)
            return False

    def download(self, entries, desc, thread_count):
        result = ThreadPool(thread_count).imap_unordered(
            self.download_media_item, entries
        )
        for _ in tqdm(result, unit=" media items", total=len(entries), desc=desc):
            pass

    def select_media_item(self, uuid):
        return self.cur.execute(
            """SELECT * FROM media WHERE uuid=?""", (uuid,)
        ).fetchone()

    def insert_media_item(self, uuid, path, album_uuid):
        self.cur.execute(
            """INSERT INTO media VALUES (?, ?, ?)""", (uuid, path, album_uuid)
        )
        self.con.commit()

    def select_album(self, uuid):
        return self.cur.execute(
            """SELECT * FROM albums WHERE uuid=?""", (uuid,)
        ).fetchone()

    def insert_album(self, uuid, path, title, is_shared=False):
        self.cur.execute(
            """INSERT INTO albums VALUES (?, ?, ?, ?)""", (uuid, path, title, is_shared)
        )
        self.con.commit()

    def process_media_items(self, media_items, save_directory, album_uuid=None):
        media = []
        for item in media_items:
            # Path where the media item will be saved to
            item_path = None

            # Select the media item from the database
            # -> if it exists then insert a new media item and set the item_path to the newly set path
            # -> if it already exists then just pull the item_path from the existing db entry
            item_db_entry = self.select_media_item(item["id"])
            if not item_db_entry:
                item_path = auto_filename(f'{save_directory}/{item["filename"]}')
                self.insert_media_item(
                    item["id"],
                    item_path,
                    album_uuid,
                )
            else:
                item_path = item_db_entry[1]

            # Set description to none if not there so a key error won't occur below
            #   This keeps the code simpler when dealing with descriptions
            if "description" not in item:
                item["description"] = None

            # Process Media
            # - Image
            if "image" in item["mimeType"]:
                media.append(
                    (
                        item["baseUrl"] + "=d",
                        item_path,
                        item["description"],
                    )
                )
            # - Video
            elif "video" in item["mimeType"]:
                media.append(
                    (
                        item["baseUrl"] + "=dv",
                        item_path,
                        item["description"],
                    )
                )

        return media

    def download_library(self):
        items = self.process_media_items(self.list_media_items(), self.lib_dir)
        self.download(items, "Downloading Library", self.thread_count)

    def download_favorites(self):
        items = self.process_media_items(self.search_favorites(), self.favorites_dir)
        self.download(items, "Downloading Favorites", self.thread_count)

    def download_all_albums(self):
        for album in self.list_albums():
            self.download_single_album(album)

    def download_all_shared_albums(self):
        for album in self.list_shared_albums():
            self.download_single_album(album, True)

    def download_single_album(self, album, shared=False):
        # Return if the album has no mediaItems to download
        # Unsure of how this occurs, but there are album entries that exist
        #   where there I don't have permission, weird bug...
        if "mediaItemsCount" not in album:
            return

        # Next check to see if the album has a title, if it doesn't give it default name
        if "title" not in album:
            album["title"] = "Unnamed Album"

        # Make request
        album_items = []

        request_body = {
            "albumId": album["id"],
            "pageSize": 100,  # Max is 100
            "pageToken": "",
        }

        request = (
            self.service.mediaItems().search(body=request_body).execute()
        )  # 100 is max
        while True:
            album_items += request["mediaItems"]
            if "nextPageToken" in request:
                request_body["pageToken"] = request["nextPageToken"]
                request = self.service.mediaItems().search(body=request_body).execute()
            else:
                break

        # Directory where the album exists
        album_path = None

        # Select the album item from the database
        # -> if it exists then insert a new album entry and set the album_path to the newly set path
        # -> if it already exists then just pull the album_path from the existing db entry
        album_db_entry = self.select_album(album["id"])
        if album_db_entry:
            album_path = album_db_entry[1]
        elif not shared:
            album_path = auto_mkdir(self.albums_dir + "/" + album["title"])
            self.insert_album(album["id"], album_path, album["title"], shared)
        else:
            album_path = auto_mkdir(self.shared_albums_dir + "/" + album["title"])
            self.insert_album(album["id"], album_path, album["title"], shared)

        processed_items = self.process_media_items(album_items, album_path, album["id"])

        self.download(
            processed_items,
            f"Downloading {'Shared ' if shared else ''}Album: \"{album['title']}\"",
            self.thread_count,
        )

    def list_media_items(self):
        media_items_list = []
        request = self.service.mediaItems().list(pageSize=100).execute()  # Max is 50
        while True:
            media_items_list += request["mediaItems"]
            if "nextPageToken" in request:
                next_page = request["nextPageToken"]
                request = (
                    self.service.mediaItems()
                    .list(pageSize=100, pageToken=next_page)
                    .execute()
                )
            else:
                break
        return media_items_list

    def list_albums(self):
        album_list = []
        request = self.service.albums().list(pageSize=50).execute()  # Max is 50
        while True:
            album_list += request["albums"]
            if "nextPageToken" in request:
                next_page = request["nextPageToken"]
                request = (
                    self.service.albums()
                    .list(pageSize=50, pageToken=next_page)
                    .execute()
                )
            else:
                break
        return album_list

    def list_shared_albums(self):
        shared_album_list = []
        request = self.service.sharedAlbums().list(pageSize=50).execute()  # Max is 50
        while True:
            shared_album_list += request["sharedAlbums"]
            if "nextPageToken" in request:
                next_page = request["nextPageToken"]
                request = (
                    self.service.sharedAlbums()
                    .list(pageSize=50, pageToken=next_page)
                    .execute()
                )
            else:
                break
        return shared_album_list

    def search_favorites(self):
        # Form request body using media_types_list above
        request_body = {
            "filters": {"featureFilter": {"includedFeatures": ["FAVORITES"]}},
            "pageSize": 100,  # Max is 100
            "pageToken": "",
        }

        # Make request
        favorites_list = []
        request = self.service.mediaItems().search(body=request_body).execute()
        while True:
            favorites_list += request["mediaItems"]
            if "nextPageToken" in request:
                request_body["pageToken"] = request["nextPageToken"]
                request = self.service.mediaItems().search(body=request_body).execute()
            else:
                break
        return favorites_list
