import spotipy
import spotipy.util as util
from spotipy import oauth2
from datetime import datetime, timedelta

SPOTIPY_CLIENT_ID = '5d7b7b63771f45efb4c618aa0046adb7'
SPOTIPY_CLIENT_SECRET = '0cb723fd54fb43bd86bde40acaa65916'
SPOTIPY_REDIRECT_URI = 'rootnote.io'

sp_oauth = oauth2.SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI)


def get_token(user):
    """function called when an access token is needed to make API calls.
    checks if a new token in needed and uses the refresh token accordingly.
    """

    social = user.social_auth.get(provider='spotify')

    refresh = bool(datetime.fromtimestamp(social.extra_data['auth_time']) < (
        datetime.now() + timedelta(minutes=2)))  # two minutes added to make sure token is still valid when making actual API call

    if(refresh):
        token_info = sp_oauth.refresh_access_token(
            social.extra_data['refresh_token'])
        token = token_info['access_token']
        social.extra_data['access_token'] = token_info['access_token']
        social.extra_data['refresh_token'] = token_info['refresh_token']
        social.extra_data['auth_time'] = token_info['expires_at']
        social.save()
    else:
        token = social.extra_data['access_token']

    return token
