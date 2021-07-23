"""
CLI Interface
Archiver for Google Photos
By: Nick Dawson | nick@ndawson.me
"""

import argparse
from os import getcwd

from colorama import Fore, init

from gparch import VERSION, PhotosAccount

if __name__ == "__main__":
    init()  # Init colorama

    CWD = getcwd()
    DEFAULT_THREADS = 8

    parser = argparse.ArgumentParser(
        description="If no directory arg is provided the program will default to the current working directory. "
        "If no credentials are provided the program will search for 'credentials.json' in the directory. "
        "If no download options are provided, the program will download everything. "
        "The program automatically skips downloading existing files so running the program with any"
        " download option after downloading items already will update everything without re-downloading or"
        " deleting existing media. It will only ensure everything is downloaded from Google Photos."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=CWD,
        help="directory where your photo library is saved",
    )
    parser.add_argument(
        "-c",
        "--credentials",
        help="path to Google Cloud OAuth2 Credentials (default: {CURRENT_DIR}/credentials.json)",
        type=str,
    )
    parser.add_argument(
        "-t",
        "--threads",
        help="amount of threads to use when downloading media items (default: 8)",
        default=DEFAULT_THREADS,
        type=int,
    )

    parser.add_argument(
        "-a",
        "--albums",
        help="download all albums YOU have created",
        action="store_true",
    )

    parser.add_argument(
        "-s",
        "--shared",
        help="download all shared albums (with you/from you)",
        action="store_true",
    )

    parser.add_argument(
        "-f",
        "--favorites",
        help="download all media from your library that is marked as favorite",
        action="store_true",
    )

    args = parser.parse_args()

    # Welcome Message
    print(Fore.BLUE + "================================")
    print(Fore.RED + "Archiver for Google Photos (CLI)")
    print(Fore.YELLOW + " - By: Nick Dawson")
    print(Fore.YELLOW + " - GitHub @NicholasDawson")
    print(Fore.YELLOW + " - https://ndawson.me")
    print(
        Fore.RED + "\nReport all issues on GitHub:"
        "\nhttps://github.com/NicholasDawson/ArchiverForGooglePhotos/issues"
    )
    print(Fore.RED + "Version -> " + VERSION)
    print(Fore.BLUE + "================================")

    if args.credentials is None:
        args.credentials = args.directory + "/credentials.json"

    # Init PhotosAccount object
    account = PhotosAccount(args.credentials, args.directory, args.threads)

    account.get_google_api_service()

    # ==============
    # ARG PROCESSING
    # - downloaded in order of importance
    # - (fav) -> (albums) -> (shared) -> (library)
    # - this is because media is only downloaded and stored in one location
    #   so we want it to be in the most specific place possible
    # ==============

    # Handler for downloading everything default option (when no download options are specified)
    download_everything = False
    if not args.favorites and not args.shared and not args.albums:
        args.favorites = True
        args.shared = True
        args.albums = True
        download_everything = True

    # Download everything
    try:
        if args.favorites:
            print(Fore.YELLOW + "Reading Favorites List From Server..." + Fore.BLUE)
            account.download_favorites()
            print(Fore.GREEN + "✔ Finished Downloading Favorites.")

        if args.albums:
            print(Fore.YELLOW + "Reading Albums List From Server..." + Fore.BLUE)
            account.download_all_albums()
            print(Fore.GREEN + "✔ Finished Downloading Albums.")

        if args.shared:
            print(Fore.YELLOW + "Reading Shared Albums List From Server..." + Fore.BLUE)
            account.download_all_shared_albums()
            print(Fore.GREEN + "✔ Finished Downloading Shared Albums.")

        if download_everything:
            print(Fore.YELLOW + "Reading Entire Library From Server..." + Fore.BLUE)
            account.download_library()
            print(Fore.GREEN + "✔ Finished Downloading Everything.")

    # Finish up and close program
    finally:
        # Close db connection
        account.con.close()

        # Print session stats
        seconds, downloads = account.get_session_stats()
        print(Fore.RED + "\n=============")
        print("SESSION STATS")
        print("=============")
        print(Fore.BLUE + f"Seconds: {Fore.YELLOW}{seconds:.{2}f}s")
        print(Fore.BLUE + f"Downloads: {Fore.YELLOW}{downloads} items")
