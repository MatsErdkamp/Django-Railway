from .. import models
import spotipy
from django.db.models import Count
import collections
from . import spotify_post_functions
import spotipy
from .authorization_functions import get_token
import datetime



def update_recommendation_playlist_content(user_id):
    #update a user's recommendation playlist content
    print('updating a users recommendation playlist!')


    user = models.User.objects.get(id=user_id)
    print(user)

    #if the user does not have the saved playlist in spotify, create a new one
    user_playlist = models.RecommendationPlaylist.objects.filter(user=user)

    songs_to_add = [x.song for x in models.SongRecommendation.objects.filter(user_to=user).prefetch_related('song').order_by('-timestamp')]
    uris = [x.uri for x in songs_to_add]

    if user_playlist.exists() == False:

        posted_playlist = spotify_post_functions.post_user_recommendation_playlist(user, uris)

        name = posted_playlist['name']
        playlist_id = posted_playlist['id']
        image_640px = image_300px = image_64px = posted_playlist['images'][0]['url']
        update = True
        
        models.RecommendationPlaylist.objects.create_recommendation_playlist(name=name, playlist_id=playlist_id, image_640px=image_640px, image_300px=image_300px, image_64px=image_64px, songs=songs_to_add, user=user, update=update)
    else:


        playlist_id = user_playlist.first().playlist_id
        
        token = get_token(user)
        spotipy.Spotify(token).user_playlist_replace_tracks(
            user=user, playlist_id=playlist_id, tracks=uris)

        
        dt = datetime.datetime.now()

        description = 'ROOTNOTE generated playlist. Last updated on ' + \
            dt.strftime('%Y-%m-%d')

        spotipy.Spotify(token).user_playlist_change_details(
            user=user, playlist_id=playlist_id, description=description)
        

        
    