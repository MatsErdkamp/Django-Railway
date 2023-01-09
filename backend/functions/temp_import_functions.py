#functions that in principle only need to be called once
from .. import models
from . import authorization_functions, model_functions
import spotipy
import json
import os, sys
import time
from datetime import datetime

def  import_streams_temp(id, username):

    user = models.User.objects.get(username=username)


    with open(os.path.join(sys.path[0], f"/home/mats/rootnote/SITE_CODE/backend/functions/data/endsong_temporary/StreamingHistory{id}.json"), "r", encoding="utf8") as f:
        songs = json.load(f)

        for index, song in enumerate(songs):
            try:
                song = models.Song.objects.filter(name=song['trackName'], artist__name=song['artistName'])[0]
                models.Stream.objects.create_stream(song=song, user=user, played_at=datetime.utcnow(), imported=True)
                print(f"{index}/{len(songs)}")
            except:
                print('failed!')


    # folder_path = os.path.dirname(os.path.abspath(file.file.path))

    # opened_file = json.loads(file.file.read())

    # print(opened_file[0])

    # streams_to_add = [x for x in opened_file if x['spotify_track_uri']
    #                   != None and x['reason_end'] == 'trackdone']

    # error_list = []

    # for index, stream in enumerate(streams_to_add):

    #     print('-------------------------------------------------------------- ' +
    #           '\033[91m' + str(index + 1) + "/" + str(len(streams_to_add)) + '\033[0m')


    #     print('\033[94m{}\033[0m'.format(stream['master_metadata_track_name']))
    #     print('{}'.format(stream['master_metadata_album_artist_name']))
    #     print('\033[90m{}\033[0m'.format(parser.parse(stream['ts'])))

    #     try:
    #         if models.Song.objects.filter(uri=stream['spotify_track_uri']).first():
    #             song = models.Song.objects.get(uri=stream['spotify_track_uri'])
    #             models.Stream.objects.create_stream(
    #                 user=user, song=song, played_at=parser.parse(stream['ts']), imported=True)
    #     except IntegrityError as e:

    #         if 'UNIQUE constraint failed' in e.args[0]:
    #             print(
    #                 '\033[91m' + 'unique contraint failed -- stream NOT added to error log' + '\033[0m')
    #         else:
    #             print(e)
    #             print(
    #                 '\033[91m' + 'ERROR ADDING SONG TO DATABASE -- see endsong_errors.json' + '\033[0m')
    #             error_list.append(stream)

    # error_file = open(folder_path + '/endsong_errors.json', 'a+')

    # error_file.write(json.dumps(
    #     {os.path.basename(file.file.name): error_list},))
    # error_file.close()




def genenate_streams_from_temp_import(id=id):

    artists = models.Artist.objects.all()
    db_songs = models.Song.objects.all()


    master_dict = {}

    with open(os.path.join(sys.path[0], f"/home/mats/rootnote/SITE_CODE/backend/functions/data/endsong_temporary/StreamingHistory{id}.json"), "r", encoding="utf8") as f:
        songs = json.load(f)

        for index, song in enumerate(songs):
            

            if artists.filter(name=song['artistName']).exists():
                pass
            else:
                print(f"{song['artistName']} does not exist yet")
                user = models.User.objects.get(username="MatsErdkamp")
                token = authorization_functions.get_token(user)
                search_query = spotipy.Spotify(
                    token).search(q=f"artist:{song['artistName']}", type='artist')



                if len(search_query['artists']['items']) == 0:
                    continue
                else:
                    fetchArtist = spotipy.Spotify(
                        token).artist(search_query['artists']['items'][0]['uri'])


                if models.Artist.objects.filter(uri=fetchArtist["uri"]).exists() == False:

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
                            '#')

            print(f"{index}/{len(songs)}")
            if artists.filter(name=song['artistName']).exists():
                if  db_songs.filter(artist__name=song['artistName']).filter(name=song['trackName']).exists():
                    pass
                else:
                    if song['artistName'] in master_dict:
                        if song['trackName'] in master_dict[song['artistName']]:
                            master_dict[song['artistName']][song['trackName']] += 1
                        else:
                            master_dict[song['artistName']][song['trackName']] = 1
                    else:
                        master_dict[song['artistName']] = {}
                        master_dict[song['artistName']][song['trackName']] = 1




    for artist in master_dict.keys():

        print(f"ARTIST: {artist}")
        songs = master_dict[artist]


        for song in songs:

            user = models.User.objects.get(username="MatsErdkamp")
            token = authorization_functions.get_token(user)
            search_query = spotipy.Spotify(
                token).search(q=f"{song} {artist}", type='track')

            print(search_query['tracks']['items'][0]['id'])   

            track = spotipy.Spotify(token).track(search_query['tracks']['items'][0]['id'])
            
            model_functions.create_db_entries(user=user, track=track)

            song = models.Song.objects.get(uri=f"spotify:track:{search_query['tracks']['items'][0]['id']}")


            time.sleep(1)   
