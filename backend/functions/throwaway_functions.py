#functions that in principle only need to be called once
from unicodedata import name
from .. import models
from . import authorization_functions, playlist_generation_functions, spotify_get_functions, color_functions, model_functions
from django.db.models import Count
from datetime import datetime
from collections import Counter
import pytz
import spotipy
import hashlib, base64
import json
import os, sys
from collections import defaultdict
import time


def throwaway():

    print('throwaway function started!')

    artists = models.Artist.objects.all()
    db_songs = models.Song.objects.all()


    master_dict = {}

    with open(os.path.join(sys.path[0], "backend/functions/data/endsong_temporary/StreamingHistory0.json"), "r", encoding="utf8") as f:
        songs = json.load(f)

        for song in songs:
            
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


    
    print(master_dict)


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

            time.sleep(1)   



    # sorted_artists = sorted(missing_artists.items(), key=lambda x: x[1], reverse=True)

    # print(sorted_artists[0][0])




    # print(artist_query)

    # for container in models.SongContainer.objects.iterator():

    #     print(container.name)

    #     uri_string = container.artist.uri+container.identifier+str(container.track_number)+str(container.disc_number)
    #     uri = hashlib.md5(uri_string.encode('utf-8')).hexdigest()[:12]

    #     container.uri = uri
    #     container.save()



    # songs = models.Song.objects.filter(energy__lte = -0.5)


    # for song in songs:

    #     print(song.name)

    #     if song.energy < 0:
    #         song.energy = 0.50001
    #     if song.danceability < 0:
    #         song.danceability = 0.50001
    #     if song.valence < 0:
    #         song.valence = 0.50001

    #     song.save()

    # artists = models.Artist.objects.all()

    # for artist in artists:

    #     containers = artist.albumcontainer_set.all().order_by('identifier')

    #     for container in containers:

    #         other_container_identifiers = [x.identifier for x in containers if x != container]

    #         if container.identifier in other_container_identifiers:
    #             print(container.identifier)

    #             if container.songcontainer_set.count() == 0:

    #                 container.delete()


    




#def throwaway():
#    print('getting recent streams lars')
#    token = authorization_functions.get_token(models.User.objects.get(username="lars.derhaag"))
#
#    sp = spotipy.Spotify(auth=token)
#    recent = [x['track']['name'] for x in sp.current_user_recently_played()['items']]
#
#    print(recent)

# def throwaway():
#     print('executing throwaway function')

#     streams = [datetime.timestamp(x['played_at']) for x in models.Stream.objects.all().values('played_at')]
#     streams = Counter(streams)
#     streams = [word for word, occurrences in streams.items() if occurrences >= 2]
#     streams = [datetime.utcfromtimestamp(stream) for stream in streams]
#     streams = models.Stream.objects.filter(played_at__in=streams).order_by('song__name')

#     unique_name = ''
#     for stream in streams:
#         if stream.song.name != unique_name:
#             unique_name = stream.song.name
#         else:
#             stream.delete()

#     print(streams)

