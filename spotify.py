import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Vul hier je eigen gegevens in
CLIENT_ID = "608e84d64a84485988c331ecaed17027"
CLIENT_SECRET = "a6a2863b966e4997a2213d494177e8e5"
REDIRECT_URI = "http://127.0.0.1:8888/callback"
PLAYLIST_URI = "https://open.spotify.com/playlist/7JhWxjbduGZQ2mT9qxfSdY?si=8398c1458da94f53"

# Maak Spotify client aan
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-modify-playback-state user-read-playback-state"
))

# Haal actieve apparaten op
devices = sp.devices()
if not devices['devices']:
    print("Geen actieve apparaten gevonden. Start Spotify op een apparaat.")
else:
    device_id = devices['devices'][0]['id']

    # Start afspelen van de playlist op het eerste actieve apparaat
    sp.shuffle(state=False, device_id=device_id)
    sp.start_playback(device_id=device_id, context_uri=PLAYLIST_URI)
    print("Playlist wordt afgespeeld op apparaat:", devices['devices'][0]['name'])
