import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from exif import Image
import json
from urllib.request import urlretrieve as download


# Define Scopes for Application
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']

def get_service():
    # The file photos_token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds = None

    if os.path.exists('photoslibrary_token.pickle'):
        with open('photoslibrary_token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('photoslibrary_token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

def download_images(media_items, media_num):
    for x in media_items:
        if 'image' in x['mimeType']:
            url = x['baseUrl'] + '=d'
        else:
            url = x['baseUrl'] + '=dv'
        filename = str(media_num) + '_' + x['filename']
        print('Downloading ' + filename)
        download(url, 'Google Photos Library/' + filename)
        
        # Check for description metadata and add to the image if there
        if 'description' in x:
            print('Found Description: ' + x['description'])
            with open('Google Photos Library/' + filename, 'rb') as image_file:
                exif_image = Image(image_file)
                exif_image.image_description = x['description']
                with open('Google Photos Library/' + str(media_num) + '_desc_' + x['filename'], 'wb') as new_image:
                    new_image.write(exif_image.get_file())
            os.remove('Google Photos Library/' + filename)
        media_num += 1
    return media_num


# Get API Service
print('Getting API Service...')
service = get_service()
print('API Service loaded.')

# Find and Download Media
if not os.path.exists('Google Photos Library'):
    os.makedirs('Google Photos Library')

results = service.mediaItems().list(pageSize=100).execute()
with open('result0' + '.json', 'w') as f:
    print('saving results...')
    f.write(json.dumps(results))
media_num = download_images(results['mediaItems'], 0)
next = results['nextPageToken']

while True:
    results = service.mediaItems().list(pageSize=100, pageToken=next).execute()
    with open('result' + str(media_num) + '.json', 'w') as f:
        print('saving results...')
        f.write(json.dumps(results))
    media_num = download_images(results['mediaItems'], media_num)
    try:
        next = results['nextPageToken']
    except KeyError:
        break
print('All Media Has Been Downloaded.')
print(media_num + ' items have been downloaded.')
