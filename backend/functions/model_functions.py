from . import authorization_functions, color_functions, spotify_get_functions
import spotipy
from .. import models
import logging
from django.db.models import Count, Case, When, IntegerField
from django.db.models.fields import DateField
import time
import re
import string
import json
import os
import sys
import math
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import *
from spotipy import oauth2
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def set_correct_album_types_all_albums():

    # models.Album.objects.update(album_type='unknown')

    all_artists = models.Artist.objects.all()
    user = models.User.objects.get(username="MatsErdkamp")

    for artist in all_artists:

        print('\033[94m{}\033[0m'.format(artist.name))
        artist_local_albums = artist.album_set.all()

        if len(artist_local_albums.filter(album_type='unknown')) > 0:
            set_correct_album_types(artist_local_albums, user)


def set_correct_album_types(albums, user):

    ids = [x.uri for x in albums]
    response_albums = spotify_get_functions.get_albums(ids, user)

    for response_album in response_albums:

        local_album = models.Album.objects.get(uri=response_album['uri'])

        local_album.album_type = response_album['album_type']
        local_album.save()


def create_db_entries(user, track):

    token = authorization_functions.get_token(user)
    sp = spotipy.Spotify(auth=token)

    newObject = False  # used to check if we need to generate colors

    # Check if the artist exist in the database, if not, add
    if models.Artist.objects.filter(uri=track['artists'][0]['uri']).exists():
        logger.error("Artist Exists!")
    else:
        fetchArtist = sp.artist(track["artists"][0]['uri'])
        newObject = True
        try:
            models.Artist.objects.create_artist(
                fetchArtist['name'],
                fetchArtist["uri"],
                fetchArtist["genres"],
                fetchArtist["images"][0]["url"],
                fetchArtist["images"][1]["url"],
                fetchArtist["images"][2]["url"]
            )
        except:  # if artist has no image
            models.Artist.objects.create_artist(
                fetchArtist['name'],
                fetchArtist["uri"],
                fetchArtist["genres"],
                '#',
                '#',
                '#'
            )

    # Check if the album exist in the database, if not, add
    if models.Album.objects.filter(uri=track['album']['uri']).exists():
        logger.error("Album Exists!")
    else:
        fetchAlbum = sp.album(track["album"]['uri'])

        try:
            img0 = track['album']['images'][0]['url']
            img1 = track['album']['images'][1]['url']
            img2 = track['album']['images'][2]['url']
        except:
            img0 = '#'
            img1 = '#'
            img2 = '#'

        newObject = True
        if models.Artist.objects.filter(uri=fetchAlbum['artists'][0]['uri']).exists():
            models.Album.objects.create_album(
                track['album']['name'],
                track['album']['uri'],
                models.Artist.objects.get(
                    uri=fetchAlbum['artists'][0]['uri']),
                img0,
                img1,
                img2,
                track['album']['release_date'][:4],
                track['album']['album_type']
            )
        else:
            fetchAlbumArtist = sp.artist(
                fetchAlbum["artists"][0]['uri'])

            try:
                artist = models.Artist.objects.create_artist(
                    fetchAlbumArtist['name'],
                    fetchAlbumArtist["uri"],
                    fetchAlbumArtist["genres"],
                    fetchAlbumArtist['images'][0]['url'],
                    fetchAlbumArtist['images'][1]['url'],
                    fetchAlbumArtist['images'][2]['url'])
            except:
                artist = models.Artist.objects.create_artist(
                    fetchAlbumArtist['name'],
                    fetchAlbumArtist["uri"],
                    fetchAlbumArtist["genres"],
                    '#',
                    '#',
                    '#')

            models.Album.objects.create_album(
                track['album']['name'],
                track['album']['uri'],
                artist,
                img0,
                img1,
                img2,
                track['album']['release_date'][:4],
                track['album']['album_type']
            )

    # Check if the song exist in the database, if not, add
    if models.Song.objects.filter(uri=track['uri']).exists():
        logger.error("Track Exists!")
    else:
        models.Song.objects.create_song(
            track['name'],
            track["uri"],
            models.Artist.objects.get(uri=track['artists'][0]['uri']),
            models.Album.objects.get(uri=track["album"]['uri']),
        )
    if newObject:
        # if statement before this maybe
        print("New objects! generating colors!")
        color_functions.generate_colors()


def remove_db_duplicates():

    # albums
    duplicate_albums = models.Album.objects.values('name').annotate(
        Count('uri')).order_by().filter(uri__count__gt=1)

    albums = models.Album.objects.filter(
        name__in=[item['name'] for item in duplicate_albums]).order_by('name')

    fmt = '{:<40} {:<1} {:<10} '
    albumstr = ""
    duplicates_num = 0

    for album in albums:

        if albumstr != album.name:
            print("----------")
            albumstr = album.name
            alb = album

        print(fmt.format("++" + album.name[:40],
                         '|' + str(""), str(album.id)))

        children = album.song_set.all()

        for child in children:

            obj = models.Song.objects.get(id=child.id)
            obj.album = alb
            obj.save()
            # print(fmt.format(obj.name[:40], '|' + str(obj.album.id), ""))

        children_left = len(album.song_set.all())

        if children_left == 0:
            print(album.name + "is getting deleted")
            models.Album.objects.get(id=album.id).delete()
            duplicates_num += 1

    print("deleted and merged " + str(duplicates_num) + " albums")

    duplicate_songs = models.Song.objects.values('name').annotate(
        Count('uri')).order_by().filter(uri__count__gt=1)

    songs = models.Song.objects.filter(
        name__in=[item['name'] for item in duplicate_songs]).order_by('name', 'id')

    songstr = ""
    artstr = ""
    duplicates_num = 0

    for song in songs:

        if songstr != song.name or artstr != song.artist.name:
            print("----------")
            songstr = song.name
            artstr = song.artist.name
            sng = song

        print(fmt.format("++" + song.name[:40],
                         '|' + str(song.artist.name), str(song.id)))

        children = song.stream_set.all()

        for child in children:

            obj = models.Stream.objects.get(id=child.id)
            obj.song = sng
            obj.save()
            # print(fmt.format(obj.name[:40], '|' + str(obj.album.id), ""))

    for song in songs:
        children_left = len(song.stream_set.all())

        if children_left == 0:
            print(song.name + "is getting deleted")
            models.Song.objects.get(id=song.id).delete()
            duplicates_num += 1

    print("deleted and merged " + str(duplicates_num) + " albums")
    print(len(songs))


def fix_song_album_relation():

    songs = models.Song.objects.all()
    song_uris = [x.uri for x in songs]

    print('{} songs in database'.format(len(songs)))
    print('scanning if songs have the correct associated album')

    user = models.User.objects.get(username="famerdkamp")
    token = authorization_functions.get_token(user)
    sp = spotipy.Spotify(auth=token)

    songs_data = []

    for index in range(int(len(songs)/50)+1):

        front = int(index*50)
        back = int(index*50 + 50)

        song_slice = song_uris[front:back]
        response = sp.tracks(song_slice)
        songs_data += response['tracks']
        print(str(front) + ":" + str(back))
        # time.sleep(0.3)

    absent_albums = []

    for index, song in enumerate(songs):

        local_album_uri = songs[index].album.uri
        if local_album_uri == songs_data[index]['album']['uri']:
            pass
        else:
            print("ERROR FOR: " + str(songs_data[index]['name']))
            if models.Album.objects.filter(uri=songs_data[index]['album']['uri']).exists() == False:

                if songs_data[index]['album']['uri'] not in absent_albums:
                    absent_albums.append(songs_data[index]['album']['uri'])

    print('ABSENT ALBUMS')
    print(absent_albums)

    if (len(absent_albums) > 0):
        for index in range(int(len(absent_albums)/20)+1):

            front = int(index*20)
            back = int(index*20 + 20)

            album_slice = absent_albums[front:back]

            if(len(album_slice) > 0):
                fetchAlbums = sp.albums(album_slice)['albums']

                for i in range(len(album_slice)):

                    album = fetchAlbums[i]
                    print(album['name'])

                    models.Album.objects.create_album(
                        album['name'],
                        album['uri'],
                        models.Artist.objects.get(
                            uri=album['artists'][0]['uri']),
                        album['images'][0]['url'],
                        album['images'][1]['url'],
                        album['images'][2]['url'],
                        album['release_date'][:4],
                        album['album_type']
                    )

    count = 0
    for index, song in enumerate(songs):

        local_album_uri = songs[index].album.uri
        if local_album_uri == songs_data[index]['album']['uri']:
            pass
        else:
            print("CONVERTING ALBUM URI FOR: " +
                  str(songs_data[index]['name']))
            if models.Album.objects.filter(uri=songs_data[index]['album']['uri']).exists():
                count += 1
                song = models.Song.objects.get(uri=song_uris[index])
                song.album = models.Album.objects.get(
                    uri=songs_data[index]['album']['uri'])
                song.save()

    print("changed album for {} songs".format(count))


def scan_for_hidden_albums(artistOffset=0):

    user = models.User.objects.get(username="famerdkamp")
    artists = models.Artist.objects.all()[artistOffset:]
    # artist_uris = [x.uri for x in artists]
    hidden_albums = []

    for index, artist in enumerate(artists):
        albums_spotify = spotify_get_functions.get_artist_albums(
            id=artist.uri, user=user, album_type=None)

        albums_local = artist.album_set.all()

        spotify_uris = []
        spotify_names = []

        for album in albums_spotify:

            spotify_uris.extend(album['uris'])
            spotify_names.append(album['name'])

        for album_local in albums_local:

            if album_local.uri not in spotify_uris:
                # print(album_local)
                # print(uris)
                hidden_albums.append(album_local.uri)

                # delete punctuation marks and make lowercase
                album_name = album_local.name.translate(
                    str.maketrans('', '', string.punctuation))
                # remove spaces
                album_name = album_name.replace(" ", "").replace("'", "").replace(
                    '"', '').replace("’", "").replace("‘", '').casefold().casefold()

                albums_spotify_names = [name.translate(str.maketrans('', '', string.punctuation)).replace(
                    " ", "").casefold() for name in spotify_names]

                # print('ALBUM_NAME: ' + album_name)
                # print('SPOTIFY ALBUM NAMES: ' + str(albums_spotify_names))

                if album_name in albums_spotify_names:

                    index = albums_spotify_names.index(album_name)
                    spotify_album_uris = albums_spotify[index]['uris']

                    print('{} -- was found in the Spotify album list. at index {} with uris {}'.format(
                        album_name, index, spotify_album_uris))

                    best_option = -1
                    best_option_streams = 0

                    for index_album, alb in enumerate(spotify_album_uris):

                        local_alb = models.Album.objects.filter(uri=alb)
                        if local_alb:
                            songs_associated = len(
                                local_alb[0].song_set.all())
                            print('album exists locally with {} song associated'.format(
                                songs_associated))
                            if songs_associated > best_option_streams:
                                best_option_streams = songs_associated
                                best_option = index_album

                    if best_option != -1:

                        new_parent_album_uri = spotify_album_uris[best_option]
                        print("{} streams are going to be ported to {}".format(
                            album_local.name, new_parent_album_uri))

                        try:
                            port_streams(from_alb=album_local.uri,
                                         to_alb=new_parent_album_uri)
                        except:
                            print(
                                'error porting -- {} | {}'.format(album_local.name, album_local.uri))

                    else:
                        print('no local alternative for {}. Write code to import a Spotify db album...'.format(
                            album_local.name))

                else:
                    print('no alternative for {}. The album might be removed from spotify'.format(
                        album_local))

        print(str("{}/{}".format(index+1+artistOffset, len(artists)+artistOffset)))

    # print("{} albums missing".format(len(hidden_albums)))


def port_streams(from_alb, to_alb):

    # print(str(from_alb) +" " +str(to_alb))

    donor_album = models.Album.objects.get(uri=from_alb)
    donor_songs = donor_album.song_set.all()
    # donor_streams = [song.stream_set.all() for song in donor_songs]

    receiver_album = models.Album.objects.get(uri=to_alb)
    receiver_songs = receiver_album.song_set.all()
    receiver_song_names = [x.name.casefold()
                           for x in receiver_album.song_set.all()]
    # print(receiver_song_names)

    for song in donor_songs:

        receiver_song = None

        try:
            song_index = receiver_song_names.index(song.name.casefold())
            receiver_song = receiver_songs[song_index]
        except:

            song_index = None
            print('the destination song does not exist yet.. creating it now!')

            user = models.User.objects.get(username="famerdkamp")
            token = authorization_functions.get_token(user)
            sp = spotipy.Spotify(auth=token)

            track_index = sp.track(song.uri)['track_number']-1

            call_counter = 1
            tracks_left = True
            tracks = []

            while (tracks_left):
                response = sp.album_tracks(
                    receiver_album.uri, limit=50, offset=call_counter*50)
                tracks += response['items']
                if response['next'] is None:
                    tracks_left = False
                else:
                    call_counter += 1

            if models.Song.objects.filter(uri=tracks[track_index]['uri']).exists():
                receiver_song = models.Song.objects.get(
                    uri=tracks[track_index]['uri'])
            elif track_index < len(tracks):
                if song.name.casefold() in tracks[track_index]['name'].casefold():
                    print('creating {} for {}'.format(
                        song.name, tracks[track_index]['name']))
                    receiver_song = models.Song.objects.create_song(
                        tracks[track_index]['name'],
                        tracks[track_index]['uri'],
                        models.Artist.objects.get(
                            uri=receiver_album.artist.uri),
                        models.Album.objects.get(uri=receiver_album.uri)
                    )
                    print('CREATED SONG: {}'.format(receiver_song))
            print("song index out of bounds for " + song.name)

        if receiver_song != None:

            streams = song.stream_set.all()

            for stream in streams:
                obj = models.Stream.objects.get(id=stream.id)
                print('{},{},{}'.format(stream, obj.song, receiver_song))
                obj.song = models.Song.objects.get(uri=receiver_song.uri)
                obj.save()

        else:
            print('cant port! no good match for {}'.format(song.name))


def delete_empty_db_objects():

    songs = models.Song.objects.all()

    song_counter = 0
    for song in songs:
        if len(song.stream_set.all()) == 0:
            # print('{} has not streams! deleting!'.format(song.name))
            models.Song.objects.get(uri=song.uri).delete()
            song_counter += 1

    print('deleted {} songs'.format(song_counter))

    albums = models.Album.objects.all()

    album_counter = 0
    for album in albums:
        if len(album.song_set.all()) == 0:
            models.Album.objects.get(uri=album.uri).delete()
            album_counter += 1

    print('deleted {} albums'.format(album_counter))


def scan_for_demomyms():
    print('scanning for demomyms in database')

    with open(os.path.join(sys.path[0], "backend/functions/data/countries.json"), "r") as f:
        data = json.load(f)

    dems = [x['demonyms']['eng']['m']
            for x in data if len(x['demonyms']['eng']['m']) > 0]

    print(dems)
    genres = models.Genre.objects.all()

    for dem in dems:
        for genre in genres:

            if str(dem).lower() in str(genre.name).lower():
                stripped_genre_name = str(genre.name).replace(
                    str(dem + " ").lower(), '')
                stripped_genre_query = models.Genre.objects.filter(
                    name=stripped_genre_name)
                if stripped_genre_query.exists():

                    artists = genre.artist_set.all()
                    for artist in artists:
                        artist.genre.add(stripped_genre_query[0])
                        print('added {} to {} with genre {}'.format(
                            stripped_genre_query[0].name, artist.name, genre.name))


def add_release_year(limit):

    dateless_albums = models.Album.objects.filter(release_date=None)
    dateless_albums_limited = models.Album.objects.filter(release_date=None)[
        :limit]
    dateless_albums_uris = [x['uri']
                            for x in dateless_albums_limited.values('uri')]
    print('ALBUMS WITHOUT RELEASE DATE: ' + str(len(dateless_albums)))

    user = models.User.objects.get(username='famerdkamp')

    spotify_api_albums = spotify_get_functions.get_albums(
        ids=dateless_albums_uris, user=user)

    for index, album in enumerate(dateless_albums_limited):

        if album.uri == spotify_api_albums[index]['uri']:
            album.release_date = spotify_api_albums[index]['release_date'][:4]
            album.save()
            print(album.name + ': ' + album.release_date)
        else:
            print("URIS DO NOT MATCH!!!")


def refresh_audio_features(queryset=None):

    if queryset == None:
        queryset = models.Song.objects.all()

    responseList = []

    print("SONGS:" + str(len(queryset)))

    for i in range(math.ceil(len(queryset)/50)):

        user = User.objects.get(username="MatsErdkamp")
        # print(user)

        token = authorization_functions.get_token(user)
        sp = spotipy.Spotify(auth=token)

        first = i*50
        last = first+50

        songListSlice = queryset[first:last]
        songListSliceURI = [i.uri for i in songListSlice]

        # print(artistListSliceURI)

        x = sp.audio_features(songListSliceURI)

        responseList += x
        print(str(first) + '/' + str(math.ceil(len(queryset))))

    print(len(responseList))

    for i in responseList:

        try:
            song = models.Song.objects.get(uri=i['uri'])
            print(song.name)

            song.energy = i['energy']
            song.valence = i['valence']
            song.danceability = i['danceability']
            song.save()

        except Exception as e:

            print(e)
            print('could not update audio features')


def get_database_playlists(user, include_friend_set=True, include_group_set=True):

    playlists = {}

    owner_playlists = models.Playlist.objects.filter(user=user)
    playlists['by_user'] = owner_playlists

    all_playlists = user.playlist_as_member.all()

    noColor = all_playlists.select_related().filter(image__primary_color=None)
    for p in noColor:
        color_functions.generate_colors(p.image)

    if include_friend_set == True:
        friend_playlists = all_playlists.exclude(id__in=owner_playlists)
        playlists['by_friends'] = friend_playlists


    if include_group_set == True:

        group_ids = [x.group.id for x in user.groupmembership_set.all().prefetch_related('group')]

        group_playlists = models.GroupPlaylist.objects.filter(group__id__in=group_ids)

        playlists['by_groups'] = group_playlists

    return playlists


def get_audio_features(user, ids):

    token = authorization_functions.get_token(user)

    response = spotipy.Spotify(token).audio_features(tracks=ids[:100])

    return response


def refresh_playlist_info(user, playlist):

    token = authorization_functions.get_token(user)

    response = spotify_get_functions.get_playlist(user, playlist.playlist_id)

    print(response['images'])

    playlist.name = response['name']

    if playlist.image.px300 != response['images'][0]['url']:
        playlist.image.px64 = response['images'][0]['url']
        playlist.image.px300 = response['images'][0]['url']
        playlist.image.px640 = response['images'][0]['url']
        playlist.image.primary_color = ','.join(
            str(x) for x in color_functions.get_colors(playlist.image.px64))
        playlist.image.save()
    playlist.save()

    return playlist
