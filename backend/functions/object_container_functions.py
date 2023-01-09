from doctest import master
from os import dup
from .. import models
from . import spotify_get_functions, utils, authorization_functions, color_functions
import spotipy
from django.db.models import Count
import collections


def find_container_for_song(song, album):

    if album.album_container == None:
        proposed_container = find_container_for_album(album.name, album.release_date, album.artist)
        
        if proposed_container != None:
            album.album_container = proposed_container
            album.save()
        else:
            artist = create_artist_missing_album_containers(song.artist.id)
            proposed_container = find_container_for_album(album.name, album.release_date, artist)
            album.album_container = proposed_container
            album.save()

            if proposed_container != None:  
                create_album_container_song_containers(proposed_container.id)


    song_identifier = utils.create_song_identifier(name=song.name, include_brackets=False)

    if album.album_container != None:
        song_containers = album.album_container.songcontainer_set.all()

        best_match_container = None

        for container in song_containers:

            print(container.name)

            if song_identifier == container.identifier:
                
                print('song identifier matches container identifier!')

                if best_match_container == None:
                    best_match_container = container
                else:
                    try:
                        contender_energy_delta = abs(container.energy - song.energy)
                        defender_energy_delta = abs(best_match_container.energy - song.energy)

                        if contender_energy_delta < defender_energy_delta:
                            best_match_container = container
                    except:
                        print('something went wrong reading the energy!!')

        song.song_container = best_match_container


        if song.song_container != None:
            if song.song_container.master_child_song == None:
                song.song_container.master_child_song = song
                song.song_container.save()

        song.save()



                    






def redo_all_containers_for_artist(artist):

    artist.albumcontainer_set.all().delete()

    create_artist_album_containers(artist.id)

    artist_album_containers = artist.albumcontainer_set.all()

    for container in artist_album_containers:
        create_album_container_song_containers(container.id)

    color_functions.generate_colors()



def create_all_song_containers(delete_existing=False, offset=0):

    if delete_existing: 
        models.SongContainer.objects.all().delete()

    album_containers = models.AlbumContainer.objects.all()[offset:]
    number_of_album_containers = len(album_containers)

    for index, container in enumerate(album_containers):

        print('ID: {} ---------- {}/{}'.format(container.id,
                                               index+1, number_of_album_containers))


        if container.songcontainer_set.count() == 0: 
            create_album_container_song_containers(id=container.id)


def create_album_container_song_containers(id):

    user = models.User.objects.get(username="MatsErdkamp")

    token = authorization_functions.get_token(user)

    album_container = models.AlbumContainer.objects.get(id=id)
    albums = album_container.album_set.all()

    album_container.songcontainer_set.all().delete()

    master_child_album = album_container.master_child_album

    tracks_master_child = spotipy.Spotify(
        token).album_tracks(master_child_album.uri)


    names_tracks_master_child_empty = [x['name'] for x in tracks_master_child['items'] if len(x['name']) == 0]

    if len(names_tracks_master_child_empty) > 0:
        print('ALBUM BROKEN ON SPOTIFY SIDE -- SKIPPING')
        return None

    names = []
    uris = []

    songs = []

    for album in albums:

        songs += album.song_set.all()


    leftover_songs = songs.copy()

    identifiers_list = [utils.create_song_identifier(
        x['name'], include_brackets=False) for x in tracks_master_child['items']]

    duplicate_identifiers = [item for item, count in collections.Counter(
        identifiers_list).items() if count > 1]

    master_container_list = []

    if len(duplicate_identifiers) > 0:
        print('ALBUM HAS DUPLICATE IDENTIFIERS, ENABLING ENERGY MATCHING')

    for track in tracks_master_child['items']:

        container_dict = {}

        track_identifier = utils.create_song_identifier(
            track['name'], include_brackets=False)

        container_dict['identifier'] = track_identifier
        container_dict['identifier_extended'] = utils.create_song_identifier(track['name'], include_brackets=True)
        container_dict['name'] = track['name']
        container_dict['artist_uri'] = track['artists'][0]['uri']
        container_dict['track_number'] = track['track_number']
        container_dict['disc_number'] = track['disc_number']
        container_dict['bonus'] = False
        container_dict['songs'] = []

        for song in songs:

            if len(leftover_songs) == 0:
                break

            song_identifier = utils.create_song_identifier(
                name=song.name, include_brackets=False)
        
            if song_identifier == track_identifier:

                if song_identifier not in duplicate_identifiers:
                    container_dict['songs'].append(song)
                    if song in leftover_songs:
                        leftover_songs.remove(song)
                else:
                    # print('not sure if the song {} needs to be added to this container... checking audio features for clarification'.format(song.name))
                    
                    if utils.create_song_identifier(song.name, include_brackets=True) == utils.create_song_identifier(track['name'], include_brackets=True):
   
                        song_audio_features = spotipy.Spotify(
                            token).audio_features(track['id'])[0]
                        
                        try:
                            delta_danceability = abs(
                                song_audio_features['danceability'] - song.danceability)
                            delta_energy = abs(
                                song_audio_features['energy'] - song.energy)
                            delta_valence = abs(
                                song_audio_features['valence'] - song.valence)

                            if delta_danceability < 0.1 and delta_energy < 0.1 and delta_valence < 0.1:
                                container_dict['songs'].append(song)
                                if song in leftover_songs:
                                    leftover_songs.remove(song)
                        except:
                            print('issue using audio features as a song container identifier...')


        master_container_list.append(container_dict)

    # print('\033[91mLeftover songs found: \033[0m{}'.format(leftover_songs))

    unmatchable_songs = leftover_songs.copy()

    if len(leftover_songs) > 0:
        # print('there are song left over... checking if they are present on different versions')

        parent_albums = set([x.album.uri for x in leftover_songs])

        for parent_album in parent_albums:

            if len(unmatchable_songs) == 0:
                break

            spotify_tracks_parent_album = spotipy.Spotify(
                token).album_tracks(parent_album)['items']


            for track in spotify_tracks_parent_album:

                container_dict = {}

                track_identifier = utils.create_song_identifier(
                    track['name'], include_brackets=False)

                container_dict['identifier'] = track_identifier
                container_dict['name'] = track['name']
                container_dict['artist_uri'] = track['artists'][0]['uri']
                container_dict['track_number'] = track['track_number']
                container_dict['disc_number'] = track['disc_number']
                container_dict['bonus'] = True
                container_dict['songs'] = []

                for song in leftover_songs:

                    song_identifier = utils.create_song_identifier(
                        name=song.name, include_brackets=False)

                    if song_identifier == track_identifier:

                        if song_identifier not in duplicate_identifiers:
                            container_dict['songs'].append(song)

                            if song in unmatchable_songs:
                                unmatchable_songs.remove(song)
                        else:
                            if utils.create_song_identifier(song.name, include_brackets=True) == utils.create_song_identifier(track['name'], include_brackets=True):
                                song_audio_features = spotipy.Spotify(
                                    token).audio_features(track['id'])[0]

                                try:
                                    delta_danceability = abs(
                                        song_audio_features['danceability'] - song.danceability)
                                    delta_energy = abs(
                                        song_audio_features['energy'] - song.energy)
                                    delta_valence = abs(
                                        song_audio_features['valence'] - song.valence)

                                    if delta_danceability < 0.1 and delta_energy < 0.1 and delta_valence < 0.1:
                                        container_dict['songs'].append(song)
                                        if song in unmatchable_songs:
                                            unmatchable_songs.remove(song)
                                except:
                                    print('issue using audio features as a song container identifier...')

                if len(container_dict['songs']) > 0:
                    master_container_list.append(container_dict)



    if len(unmatchable_songs) > 0:
        print('\033[91mUnmatchable songs found: \033[0m{}'.format(
            unmatchable_songs))

    for container in master_container_list:


        try:
            master_child = container['songs'][0]
        except:
            master_child = None

        song_container = models.SongContainer.objects.create_song_container(
            name=container['name'], identifier=container['identifier'], track_number=container['track_number'], disc_number=container['disc_number'],  bonus=container['bonus'], artist_uri=container['artist_uri'], album_container=album_container, master_child_song=master_child)

        for song in container['songs']:

            song.song_container = song_container
            song.save()

    


def set_container_master_child_albums():

    print('setting the master child albums (to be non deluxe etc.)')

    album_containers = models.AlbumContainer.objects.all()
    

    updated_val_counter = 0

    for container in album_containers:


        contained_albums = container.album_set.all()

        if len(contained_albums) > 1:

            print('\033[94m----{}----\033[0m'.format(container.name))

            album_list = []

            for album in contained_albums:

                stream_count = album.song_set.all().aggregate(
                    count=Count('stream'))['count']
                album_identifier = utils.create_album_identifier(
                    album.name, album.release_date)

                album_list.append({'album_id': album.id, 'identifier': album_identifier, 'stream_count': stream_count})\

            print(album_list)

            best_option = None

            for option in album_list:

                if best_option == None:
                    best_option = option

                if len(option['identifier']) < len(best_option['identifier']):
                    best_option = option

                if len(option['identifier']) == len(best_option['identifier']):
                    if option['stream_count'] > best_option['stream_count']:
                        best_option = option

            print('\033[91m{}\033[0m'.format(best_option))

            best_option_object = models.Album.objects.get(
                id=best_option['album_id'])

            if container.master_child_album != best_option_object:
                container.master_child_album = best_option_object
                container.album_type = best_option_object.album_type
                container.save()

                updated_val_counter += 1



    print('')
    print('Changed the master child album for {} album containers'.format(
        updated_val_counter))


def find_container_for_album(name, release_date, artist):

    album_identifier = utils.create_album_identifier(name, release_date,)
    album_identifier_stripped = album_identifier.split('#', 1)[0]

    try:
        container = artist.albumcontainer_set.get(identifier=album_identifier)

        if album_identifier == container.identifier or album_identifier_stripped == container.identifier:
            print('container match found!')
            return container
    except:
        return None


def create_all_album_containers():

    all_artists = models.Artist.objects.all()

    user = models.User.objects.get(username="MatsErdkamp")

    for artist in all_artists:

        print('\033[94m{}\033[0m'.format(artist.name))

        if len(artist.album_set.filter(album_type='album').filter(album_container=None)) > 0 and len(artist.album_set.filter(album_type='album')) > 0:
            print('\033[91m{} has uncontained albums!\033[0m'.format(artist.name))
            create_artist_album_containers(artist.id)
        else:
            print('{} has no uncontained albums!'.format(artist.name))



def create_artist_missing_album_containers(artist_id):

    print('creating artist album containers')

    user = models.User.objects.get(username="MatsErdkamp")

    artist = models.Artist.objects.get(id=artist_id)


    spotify_artist_response = spotify_get_functions.get_artist_albums_for_containers(
        artist.uri, user, album_type='album,single,compilation')

    existing_identifiers = [x.identifier for x in artist.albumcontainer_set.all()]

    filtered_albums = []

    for unfiltered_album in spotify_artist_response:


        if unfiltered_album['identifier'] not in existing_identifiers:
            filtered_albums.append(unfiltered_album)


    for album in filtered_albums:

        database_albums = artist.album_set.all()

        child_albums_list = []

        best_fit_master_child = None
        best_fit_master_child_amount = -1
        shortest_album_identifier = None

        for database_album in database_albums:

            album_identifier = utils.create_album_identifier(
                database_album.name, database_album.release_date)
            album_identifier_stripped = album_identifier.split('#', 1)[0]

            if album_identifier == album['identifier'] or album_identifier_stripped == album['identifier']:
                child_albums_list.append(database_album)
                # print(album_identifier)

                stream_count = database_album.song_set.all(
                ).aggregate(count=Count('stream'))['count']

                if shortest_album_identifier == None:
                    shortest_album_identifier = album_identifier
                    best_fit_master_child_amount = stream_count
                    best_fit_master_child = database_album
                else:
                    if len(album_identifier) < len(shortest_album_identifier):
                        best_fit_master_child_amount = stream_count
                        best_fit_master_child = database_album
                        shortest_album_identifier = album_identifier

                    elif len(album_identifier) == len(shortest_album_identifier):
                        if stream_count > best_fit_master_child_amount:
                            best_fit_master_child_amount = stream_count
                            best_fit_master_child = database_album
                            shortest_album_identifier = album_identifier

        # print(most_streamed_child_amount)
        # print('')

        if best_fit_master_child != None:
            album_container = models.AlbumContainer.objects.create_album_container(
                album['name'], album['identifier'], best_fit_master_child)

            for child in child_albums_list:

                child.album_container = album_container
                child.save()

    return artist



def create_artist_album_containers(artist_id):

    print('creating artist album containers')

    user = models.User.objects.get(username="MatsErdkamp")

    artist = models.Artist.objects.get(id=artist_id)

    artist.albumcontainer_set.all().delete()

    spotify_artist_response = spotify_get_functions.get_artist_albums_for_containers(
        artist.uri, user, album_type='album,single,compilation')

    for album in spotify_artist_response:

        database_albums = artist.album_set.all()

        child_albums_list = []

        best_fit_master_child = None
        best_fit_master_child_amount = -1
        shortest_album_identifier = None

        for database_album in database_albums:

            album_identifier = utils.create_album_identifier(
                database_album.name, database_album.release_date)
            album_identifier_stripped = album_identifier.split('#', 1)[0]

            if album_identifier == album['identifier'] or album_identifier_stripped == album['identifier']:
                child_albums_list.append(database_album)
                # print(album_identifier)

                stream_count = database_album.song_set.all(
                ).aggregate(count=Count('stream'))['count']

                if shortest_album_identifier == None:
                    shortest_album_identifier = album_identifier
                    best_fit_master_child_amount = stream_count
                    best_fit_master_child = database_album
                else:
                    if len(album_identifier) < len(shortest_album_identifier):
                        best_fit_master_child_amount = stream_count
                        best_fit_master_child = database_album
                        shortest_album_identifier = album_identifier

                    elif len(album_identifier) == len(shortest_album_identifier):
                        if stream_count > best_fit_master_child_amount:
                            best_fit_master_child_amount = stream_count
                            best_fit_master_child = database_album
                            shortest_album_identifier = album_identifier

        # print(most_streamed_child_amount)
        # print('')

        if best_fit_master_child != None:
            album_container = models.AlbumContainer.objects.create_album_container(
                album['name'], album['identifier'], best_fit_master_child)

            for child in child_albums_list:

                child.album_container = album_container
                child.save()

    return artist
