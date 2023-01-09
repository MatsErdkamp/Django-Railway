import math
from .. import models, decorators
from .authorization_functions import get_token
from .utils import *
import spotipy
import spotipy.util as util
from spotipy import oauth2
import re
import string
from django.contrib.auth.models import User



def get_album_distribution_chart(id, user, left, right, timeframe):

    token = get_token(user)

    response = spotipy.Spotify(token).album_tracks(id)

    names = [i['name'] for i in response['items']]

    uris = [i['uri'] for i in response['items']]

    chart_data = []
    biggest_left = 0
    biggest_right = 0

    for index, i in enumerate(uris):

        song_dict = {'name': names[index]}

        try:
            song = models.Song.objects.get(uri=i)
            song_dict['id'] = song.id
            song_dict['streams'] = {}

            all_streams = song.stream_set.active()
            timeframe_streams = set_timeframe(all_streams, timeframe)

            song_dict['streams']['left'] = left_data = len(
                timeframe_streams.filter(user=left))
            song_dict['streams']['right'] = right_data = len(
                timeframe_streams.filter(user=right))

            if left_data > biggest_left:
                biggest_left = left_data

            if right_data > biggest_right:
                biggest_right = right_data

        except models.Song.DoesNotExist:
            song_dict['id'] = '#'
            song_dict['streams'] = {}
            song_dict['streams']['left'] = 0
            song_dict['streams']['right'] = 0

        chart_data.append(song_dict)

    users = {'left': left, 'right': right}
    biggest_values = {'all': max(
        biggest_left, biggest_right), 'left': biggest_left, 'right': biggest_right}

    return {'users': users, 'data': chart_data, 'biggest_values': biggest_values}





def get_albums(ids, user):

    album_ids = ids
    album_list = []

    calls_required = math.ceil(len(ids) / 20)

    for i in range(calls_required):

        user = User.objects.get(username="MatsErdkamp")
        # print(user)

        token = get_token(user)

        first = i*20
        last = first+20

        albumListSlice = album_ids[first:last]

        # print(artistListSliceURI)

        x = spotipy.Spotify(auth=token).albums(albumListSlice)

        album_list += x['albums']

    return album_list


def get_artist_albums(id, user, album_type='album'):

    token = get_token(user)

    albums_left = True
    call_counter = 0
    albums = []

    while (albums_left):
        response = spotipy.Spotify(token).artist_albums(
            id, album_type=album_type, limit=50, offset=call_counter*50)

        albums += response['items']

        if response['next'] is None:
            albums_left = False
        else:
            call_counter += 1

    uri_dict = {}
    names = []
    images = []
    best_name = ""

    for i in albums:

        # delete text between parentheses
        album_name = re.sub("([\(\[]).*?([\)\]])", "", i['name']).strip()
        # delete punctuation marks and make lowercase
        album_name = album_name.translate(
            str.maketrans('', '', string.punctuation))
        # remove spaces
        album_name = album_name.replace(" ", "").replace("'", "").replace(
            '"', '').replace("’", "").replace("‘", '').casefold()

        if album_name in uri_dict:

            uri_dict[album_name.casefold()].append(i['uri'])

            if len(i['name']) < len(best_name):

                names.remove(best_name)
                best_name = i['name']

                names.append(best_name)
        else:
            uri_dict[album_name.casefold()] = [i['uri']]
            best_name = i['name']

            try:
                images.append(i['images'][-1]['url'])
            except:
                images.append('#')
                print('could not find an image for: ' +
                      i['name'] + ' | ' + i['uri'])
            names.append(best_name)

    album_list = []

    for index, (key, value) in enumerate(uri_dict.items()):

        dict = {'name': names[index],
                'image_px64': images[index], 'uris': value}
        album_list.append(dict)

    return album_list


def get_artist_albums_for_containers(id, user, album_type='album'):

    token = get_token(user)

    albums_left = True
    call_counter = 0
    albums = []

    while (albums_left):
        response = spotipy.Spotify(token).artist_albums(
            id, album_type=album_type, limit=50, offset=call_counter*50)

        albums += response['items']

        if response['next'] is None:
            albums_left = False
        else:
            call_counter += 1

    uri_dict = {}
    names = []
    images = []
    best_name = ""

    for i in albums:

        # check if we are the first credited artist
        if i['artists'][0]['uri'] != id:
            print(
                "{} is not the main artist for {} -- skipping!".format(id, i['name']))
            continue

        album_name = create_album_identifier(
            i['name'], i['release_date'], include_brackets=False)

        if album_name in uri_dict:

            uri_dict[album_name.casefold()].append(i['uri'])

            if len(i['name']) < len(best_name):

                names.remove(best_name)
                best_name = i['name']

                names.append(best_name)
        else:
            uri_dict[album_name.casefold()] = [i['uri']]
            best_name = i['name']

            try:
                images.append(i['images'][-1]['url'])
            except:
                images.append('#')
                print('could not find an image for: ' +
                      i['name'] + ' | ' + i['uri'])
            names.append(best_name)

    album_list = []

    for index, (key, value) in enumerate(uri_dict.items()):

        dict = {'name': names[index],
                'identifier': key,
                'uris': value}
        album_list.append(dict)

    return album_list


def get_spotify_playlists(user, rootnote_only=False):

    token = get_token(user)

    all_playlists = []
    playlists_left = True
    fetch_index = 0

    while(playlists_left != False):

        response = spotipy.Spotify(token).user_playlists(user.social_auth.get(
            provider='spotify').uid, limit=50, offset=50*fetch_index)
        fetch_index += 1

        all_playlists.extend([x for x in response['items']])

        if response['next'] == None:
            playlists_left = False

    if rootnote_only:

        stored_playlists = [
            obj.playlist_id for obj in models.Playlist.objects.filter(user=user) ] + [ obj.playlist_id for obj in models.GroupPlaylist.objects.filter(user=user)]

        rootnote_playlists = []

        for playlist in all_playlists:

            if (playlist['id'] in stored_playlists):
                rootnote_playlists.append(playlist)

        return rootnote_playlists
    else:
        return all_playlists


def get_audio_features(user, ids):

    token = get_token(user)

    response = spotipy.Spotify(token).audio_features(tracks=ids[:100])

    return response


def refresh_artist_genres():

    allArtists = models.Artist.objects.all()

    responseList = []

    print("ARTISTS:" + str(len(allArtists)))

    for i in range(int(len(allArtists)/50)+1):

        user = User.objects.get(username="famerdkamp")
        # print(user)

        token = get_token(user)

        first = i*50
        last = first+50

        artistListSlice = allArtists[first:last]
        artistListSliceURI = [i.uri for i in artistListSlice]

        # print(artistListSliceURI)

        x = spotipy.Spotify(auth=token).artists(artistListSliceURI)

        responseList += x['artists']

    unique_genres = []

    for i in responseList:
        # print(i['uri'])
        artist = models.Artist.objects.get(uri=i['uri'])

        try:
            genres = i['genres']
        except:
            genres = '#'

        for genre in genres:
            if genre not in unique_genres:
                if models.Genre.objects.filter(name=genre).exists() == False:
                    models.Genre.objects.create(name=genre)

            if artist.genre.filter(name=genre).exists() == False:
                artist.genre.add(models.Genre.objects.get(name=genre))


def get_album_tracks(user, uri, limit=5, offset=0):

    token = get_token(user)

    response = spotipy.Spotify(token).album_tracks(uri)

    response_cleaned = response['items'][offset:offset+limit]

    return response_cleaned


def get_playlist(user, id):

    token = get_token(user)

    response = spotipy.Spotify(token).user_playlist(
        user=user.social_auth.get(provider='spotify').uid, playlist_id=id)

    if 'id' in response:
        return response
    else:
        return None


def get_playlist_tracks(user, uri, limit=5, offset=0):

    token = get_token(user)

    response = spotipy.Spotify(token).playlist_tracks(uri)

    response_cleaned = response['items'][offset:offset+limit]

    return response_cleaned


def get_track(user, uri):

    token = get_token(user)

    response = spotipy.Spotify(token).track(uri)

    return response


def search(user, q, type, limit):

    token = get_token(user)

    response = spotipy.Spotify(token).search(
        q=q, offset=0, type=type, limit=limit)

    return response


def get_spotify_profile(user):

    # print(user)

    social = user.social_auth.get(provider='spotify')

    token = get_token(user)

    print(social)
    response = spotipy.Spotify(auth=token).user(social.uid)

    return response
