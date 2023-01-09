from time import sleep
from .. import models, views, serializers
from .image_functions import get_hue_shifted_image, get_recommendation_playlist_image
from .authorization_functions import get_token
import spotipy
import spotipy.util as util
from spotipy import oauth2
from django.contrib.auth.models import User
import datetime
from django.db.models import Count, F
from django.utils.timezone import make_aware


def post_user_recommendation_playlist(user, song_uris):

    try:
        token = get_token(user)
    except:
        print('User ' + str(user).upper() + ' has no social auth')

  
    # create the playlist
    name = 'Recommended to You'
    dt = datetime.datetime.now()
    description = 'ROOTNOTE generated playlist. Last updated on ' + dt.strftime('%Y-%m-%d')
    playlist = spotipy.Spotify(token).user_playlist_create(
        user=user.social_auth.get(provider='spotify').uid, name=name, public=True, description=description)

    # upload the image
    img = get_recommendation_playlist_image()
    playlist_refetched = get_playlist_and_check_for_key(token, playlist['id'], 'id')
    spotipy.Spotify(token).playlist_upload_cover_image(
        playlist_id=playlist_refetched['id'], image_b64=img)

    # add the tracks
    spotipy.Spotify(token).user_playlist_add_tracks(
        user=user.social_auth.get(provider='spotify').uid, playlist_id=playlist_refetched['id'], tracks=song_uris)
    
    #get the completed playlist
    playlist_complete = get_playlist_and_check_for_key(token, playlist['id'], 'images')

    print('playlist generated for ' + str(user).upper())

    return playlist_complete




def post_user_playlist(user, data):

    try:
        token = get_token(user)
    except:
        print('User ' + str(user).upper() + ' has no social auth')

    
        
    # create the playlist

    dt = datetime.datetime.now()

    description = 'ROOTNOTE generated playlist. Last updated on ' + \
        dt.strftime('%Y-%m-%d')

    playlist = spotipy.Spotify(token).user_playlist_create(
        user=user.social_auth.get(provider='spotify').uid, name=data['name'], public=True, description=description)

    # upload the image
    img = get_hue_shifted_image(int(data['image_index']))


    playlist_refetched = get_playlist_and_check_for_key(token, playlist['id'], 'id')

    spotipy.Spotify(token).playlist_upload_cover_image(
        playlist_id=playlist_refetched['id'], image_b64=img)

    # add the tracks
    spotipy.Spotify(token).user_playlist_add_tracks(
        user=user.social_auth.get(provider='spotify').uid, playlist_id=playlist_refetched['id'], tracks=data['uris'])
    
    
    #get the completed playlist
    playlist_complete = get_playlist_and_check_for_key(token, playlist['id'], 'images')

    print('playlist generated for ' + str(user).upper())

    return playlist_complete

        

def get_playlist_and_check_for_key(token,id,key):
    playlist_found = False

    #make sure that the generation of the playlist has happened in spotify
    while playlist_found == False:
        
        try:
            playlist = spotipy.Spotify(token).playlist(playlist_id=id)
            
            if key in playlist:

                if playlist[key] != [] and playlist[key] != None:
                    playlist_found = True
                else:
                    sleep(1)
            else:
                sleep(1)
        except:
            print('playlist not found yet')
            sleep(1)

    return playlist




def get_songs_queryset(user):

    month = make_aware(datetime.datetime.now() - datetime.timedelta(days=30))
    queryset = models.Stream.objects.filter(played_at__gte=month).values('song', 'song__uri', 'song__name', 'song__artist'
                                                                         ).annotate(Count('song')).order_by('-song__count', 'song__name')

    queryset = queryset.filter(user=user)
    queryset = queryset[:50]
    return queryset


def get_songs(user):

    songs = get_songs_queryset(user)
    response = []

    for song in songs:

        obj = {'song': serializers.SmallSongSerializer(models.Song.objects.filter(
        id=song['song']), many=True).data[0]}
        response.append(obj)

    return response

def next_track(user):
    
    try:
        token = get_token(user)
    except:
        print('User ' + str(user).upper() + ' has no social auth')

    response = spotipy.Spotify(token).next_track() 

    return response

def add_to_queue(user, uri):

    try:
        token = get_token(user)
    except:
        print('User ' + str(user).upper() + ' has no social auth')

    response = spotipy.Spotify(token).add_to_queue(uri)

    return response


def play_track(user, context_uri, offset=0):
    
    try:
        token = get_token(user)
    except:
        print('User ' + str(user).upper() + ' has no social auth')

    spotipy.Spotify(token).start_playback(context_uri=context_uri, offset={'position': offset})
