from .models import Stream, StreamManager, Profile, Album
from django.contrib.auth.models import User
from .functions import image_functions, playlist_generation_functions


def cron_fetch():

    profiles = Profile.objects.order_by('last_request')[:4]

    for profile in profiles:
        Stream.objects.fetch_streams(profile.user)

def cron_refresh_artist_images():
    image_functions.refresh_artist_images()

def cron_update_user_playlists():
    playlist_generation_functions.update_playlists()
