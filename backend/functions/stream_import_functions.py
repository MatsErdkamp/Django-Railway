from .. import models
from .model_functions import create_db_entries
from .authorization_functions import get_token
from django.db import IntegrityError
from dateutil import parser
import spotipy
import json
import time
import os


def revert_user_stream_import(id):

    print('\033[91m' + 'REVERTING STREAMS IMPORT -- DELETING STREAMS NOW' + '\033[0m')
    
    user = models.User.objects.get(id=id)
    user.stream_set.filter(imported=True).delete()
    user.stream_set.update(active=True)
    models.EndsongFile.objects.filter(user=user).update(import_completed=False)


def deactivate_streams_before_last_import(id):

    user = models.User.objects.get(id=id)

    last_played_import = user.stream_set.filter(imported=True).order_by('-played_at')[0]

    non_imported_streams = user.stream_set.filter(imported=False)

    non_imported_streams_before_import = non_imported_streams.filter(played_at__lte=last_played_import.played_at)

    print('deactivating the local streams before the latest imported stream...')
    non_imported_streams_before_import.update(active=False)
    print('deactivated {} streams'.format(len(non_imported_streams_before_import)))

    print(last_played_import.played_at)



def import_all_user_endsong_files(id):

    user = models.User.objects.get(id=id)


    # user.stream_set.filter(imported=True).delete()

    clean_user_endsong_files(user.id)

    unverified_files = models.EndsongFile.objects.filter(user=user).filter(
        uris_available_in_database__in=['processing', 'unverified']).order_by('upload_timestamp')

    for unverified_file in unverified_files:
        create_missing_songs(unverified_file)

    files = models.EndsongFile.objects.filter(user=user).filter(cleaned=True).filter(
        uris_available_in_database='available').filter(import_completed=False)

    for file in files:
        add_db_objects_from_endsong_file(file, user)
        file.import_completed = True
        file.save()


def add_db_objects_from_endsong_file(file, user):

    folder_path = os.path.dirname(os.path.abspath(file.file.path))

    opened_file = json.loads(file.file.read())

    print(opened_file[0])

    streams_to_add = [x for x in opened_file if x['spotify_track_uri']
                      != None and x['reason_end'] == 'trackdone']

    error_list = []

    for index, stream in enumerate(streams_to_add):

        print('-------------------------------------------------------------- ' +
              '\033[91m' + str(index + 1) + "/" + str(len(streams_to_add)) + '\033[0m')


        print('\033[94m{}\033[0m'.format(stream['master_metadata_track_name']))
        print('{}'.format(stream['master_metadata_album_artist_name']))
        print('\033[90m{}\033[0m'.format(parser.parse(stream['ts'])))

        try:
            if models.Song.objects.filter(uri=stream['spotify_track_uri']).first():
                song = models.Song.objects.get(uri=stream['spotify_track_uri'])
                models.Stream.objects.create_stream(
                    user=user, song=song, played_at=parser.parse(stream['ts']), imported=True)
        except IntegrityError as e:

            if 'UNIQUE constraint failed' in e.args[0]:
                print(
                    '\033[91m' + 'unique contraint failed -- stream NOT added to error log' + '\033[0m')
            else:
                print(e)
                print(
                    '\033[91m' + 'ERROR ADDING SONG TO DATABASE -- see endsong_errors.json' + '\033[0m')
                error_list.append(stream)

    error_file = open(folder_path + '/endsong_errors.json', 'a+')

    error_file.write(json.dumps(
        {os.path.basename(file.file.name): error_list},))
    error_file.close()


def create_missing_songs(id):

    print('checking the endsong files for URIS not in the DB')
    file = models.EndsongFile.objects.get(id=id)

    file.uris_available_in_database = 'processing'
    file.save()

    if file.cleaned == False:
        clean_endsong_file(file)

    print(file.file.name)

    opened_file = json.loads(file.file.read())

    uris = [x['spotify_track_uri'] for x in opened_file if x['spotify_track_uri']
            != None and x['reason_end'] == 'trackdone']

    database_uris = [x.uri for x in models.Song.objects.all()]

    leftover_uris = list(set(uris) - set(database_uris))


    print('URIS IN FILE: ' + str(len(uris)))
    print('URIS NOT IN DB: ' + str(len(leftover_uris)))

    while len(leftover_uris) > 0:

        token = get_token(file.user)
        response = spotipy.Spotify(token).tracks(leftover_uris[:50])
        
        for index, track in enumerate(response['tracks']):
                print('-------------------------------------------------------------- ' +
                    '\033[91m' + str(len(leftover_uris) - index - 1) + '\033[0m' + ' | ' + str(index+1))
                create_db_entries(file.user, track)

        leftover_uris = leftover_uris[50:]

        print('============================================================================== ' + \
              '\033[91m' + str(len(leftover_uris) - index - 1) + '\033[0m')

    if len(leftover_uris) == 0:
        file.uris_available_in_database = 'available'
        file.save()
        return True


def clean_user_endsong_files(id):

    user = models.User.objects.get(id=id)

    files = models.EndsongFile.objects.filter(user=user).filter(cleaned=False)

    for file in files:
        clean_endsong_file(file)


def clean_endsong_file(file):

    # also clean songs with no URI !!!

    print('cleaning the endsong file; removing unneeded data')

    with open(file.file.path, 'r+', encoding="utf8") as f:

        try:
            endsong_file = json.loads(f.read())
            endsong_file_cleaned = [clean_dict(d) for d in endsong_file]

            f.seek(0)
            f.write(json.dumps(endsong_file_cleaned))
            f.truncate()

            file.cleaned = True
            file.save()
        except:
            print('error cleaning the file!')


def clean_dict(old_dict):
    n = old_dict.copy()
    n.pop('platform', None)
    n.pop('episode_show_name', None)
    n.pop('ip_addr_decrypted', None)
    n.pop('conn_country', None)
    n.pop('user_agent_decrypted', None)
    n.pop('episode_name', None)
    n.pop('incognito_mode', None)
    n.pop('shuffle', None)
    n.pop('spotify_episode_uri', None)
    n.pop('username', None)
    return n
