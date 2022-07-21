# Google Photos Archiver
[![build-exe](https://github.com/NicholasDawson/ArchiverForGooglePhotos/actions/workflows/build-exe.yml/badge.svg)](https://github.com/NicholasDawson/ArchiverForGooglePhotos/actions/workflows/build-exe.yml)

# Instructions:
1. Download the script (exe or python script listed below)
2. Follow the [instructions](INSTRUCTIONS.md)
3. Reference the command guide below to learn the different commands available to you.

If you need assistance or want to report an issue fill out an [Issue Report](https://github.com/NicholasDawson/ArchiverForGooglePhotos/issues) or email me `github (at) ndawson.me`

# [Downloads](https://github.com/NicholasDawson/ArchiverForGooglePhotos/releases)
> If you are unfamiliar with python or computers in general I recommend you download an executable as it will not require any special installation.

## Python Script
If you are familiar with python, just download the [source code](https://github.com/NicholasDawson/ArchiverForGooglePhotos/releases)

Install [pipenv](https://pipenv-fork.readthedocs.io/en/latest/install.html)
`pip install pipenv`

Install dependencies using pipenv
`pipenv install`

# Commands
> This guide assumes you have downloaded Google API Credentials and have them saved in some location on your computer, if you have no idea what this is please follow the [instructions](INSTRUCTIONS.md)

## Usage:
```
usage: gparch_cli.py [-h] [-c CREDENTIALS] [-t THREADS] [-a] [-s] [-f] [directory]

- If no directory arg is provided the program will default to the current working directory.
- If no credentials are provided the program will search for 'credentials.json' in the directory.
- If no download options are provided, the program will download everything.
- The program automatically skips downloading existing files so running the program with any download option after downloading items already will update everything without re-downloading or deleting existing media. It will only ensure everything is downloaded from Google Photos.

positional arguments:
  directory             directory where your photo library is saved

optional arguments:
  -h, --help            show this help message and exit
  -c CREDENTIALS, --credentials CREDENTIALS
                        path to Google Cloud OAuth2 Credentials (default: {CURRENT_DIR}/credentials.json)
  -t THREADS, --threads THREADS
                        amount of threads to use when downloading media items (default: 8)
  -d, --debug           enables debugging mode
  -a, --albums          download all albums YOU have created
  -s, --shared          download all shared albums (with you/from you)
  -f, --favorites       download all media from your library that is marked as favorite
```

## Important Note:
In the following examples I will be using `gparch_cli` to run the program for readability. I am listing below all the different ways you may have to run the program to get it to work on your system.

### Executable (in the same directory or in PATH)
Command Prompt: `gparch_cli`
PowerShell: `./gparch_cli`

### Python Script (in the same directory or in PATH)
Windows: `py gparch_cli.py`
Linux/Mac: `python3 gpararch_cli.py`


## Examples
Get Help
`gparch_cli --help`

Download everything from your library in the current directory with the credentials file in the current directory named `credentials.json`
`gparch_cli`

Download everything from your library to a specific directory
`gparch_cli example_directory/google_photos_folder`

Download everything from your library to a specific directory and specify where your credentials file is
`gparch_cli example_directory/google_photos_folder -c example_directory/creds.json`

Download just your albums
`gparch_cli -a`

Download just your shared albums
`gparch_cli -s`

Download just your favorited items
`gparch_cli -f`

Specify the amount of threads you want to download with to be 12:
`gparch_cli -t 12`

You can combine any of the following commands to do what you specifically want.
- If no directory arg is provided the program will default to the current working directory.
- If no credentials are provided the program will search for 'credentials.json' in the directory.
- If no download options are provided, the program will download everything.
- The program automatically skips downloading existing files so running the program with any download option after downloading items already will update everything without re-downloading or deleting existing media. It will only ensure everything is downloaded from Google Photos.

## Contributors
### Loading Environment
Install `pipenv` using `pip install pipenv` then in this repo's root directory type:
`pipenv install` to build the virtual environment.

### Building Executable
Run `py cxfreeze_setup.py build`

An executable built for your system will appear in the build directory.
