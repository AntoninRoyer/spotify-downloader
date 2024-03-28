import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from googleapiclient.discovery import build
import yt_dlp as youtube_dl
from pytube import YouTube
import os
from mutagen.id3 import ID3, TIT2, TPE1, TCON, TDRC, APIC
from mutagen.mp3 import MP3
from Metadata import Metadata
import requests

# Vos identifiants d'application Spotify
client_id = 'client_id'
client_secret = 'secret_key'

# Votre clé API YouTube
youtube_api_key = 'api_key'

# Utilisez vos identifiants pour vous authentifier
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Construisez le service YouTube
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

def sanitize_filename(filename):
    invalid_chars = "<>:\"/\\|?*"
    for char in invalid_chars:
        filename = filename.replace(char, "#")
    return filename


# Rechercher un morceau sur YouTube
def search_youtube(artist, track):
    query = f"{artist} {track}"
    request = youtube.search().list(
        part="snippet",
        maxResults=1,
        q=query
    )
    response = request.execute()

    # Retournez l'URL de la première vidéo
    return 'https://www.youtube.com/watch?v=' + response['items'][0]['id']['videoId']

# Télécharger une vidéo YouTube
def download_youtube(url, metadata):
    file_name = sanitize_filename(metadata.title)
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320'
        }],
        'outtmpl': 'downloads/' + file_name + '.%(ext)s',
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        file_path = 'E:/Scripts/downloads/' + file_name + '.mp3'
        print(file_path)

        # Add metadata
        audio = MP3(file_path, ID3=ID3)
        audio.tags.add(TIT2(encoding=3, text=metadata.title))
        audio.tags.add(TPE1(encoding=3, text=[artist for artist in metadata.artists]))
        if metadata.genres:
            audio.tags.add(TCON(encoding=3, text=[genre for genre in metadata.genres]))
        audio.tags.add(TDRC(encoding=3, text=metadata.release_date))
        # add album cover
        if metadata.image:
            try:
                response = requests.get(metadata.image)
                if response.status_code == 200:
                    audio.tags.add(
                        APIC(
                            encoding=3,
                            mime='image/jpeg',  # Assurez-vous que c'est le bon type MIME
                            type=3,  # 3 est pour la couverture
                            desc=u'Cover',
                            data=response.content
                        )
                    )
            except Exception as e:
                print("Une erreur s'est produite lors de l'ajout de l'image de couverture :", e)
        audio.save()
        print('Metadata added')


# Demandez à l'utilisateur de saisir l'URL de la playlist
playlist_url = input('Enter the Spotify playlist URL: ')

# Récupérez l'ID de la playlist
playlist_id = playlist_url.split('/')[-1].split('?')[0]
print('Playlist ID: ' + playlist_id)

# Obtenez la playlist
playlist = sp.playlist(playlist_id)

# Parcourez tous les morceaux de la playlist et imprimez leurs noms et liens d'écoute
for item in playlist['tracks']['items']:
    #  make objects
    track = item['track']
    title = track['name']
    artist = track['artists'][0]['name'] # Prend le premier nom d'artiste
    artists = [artist['name'] for artist in track['artists']]  # Prend tous les noms d'artistes
    release_date = track['album']['release_date']
    genres = None
    # image = track['album']['images'][0]['url']
    image = None
    metadata = Metadata(title, artists, release_date, genres, image)

    print(artist + ': ' + track['name'] + ' - ' + track['external_urls']['spotify'])
    # Recherchez le morceau sur YouTube et imprimez l'URL de la vidéo
    youtube_url = search_youtube(artist, track['name'])
    print('YouTube URL: ' + youtube_url)
    # Téléchargez la vidéo YouTube
    download_youtube(youtube_url, metadata)
    print('Downloaded')
