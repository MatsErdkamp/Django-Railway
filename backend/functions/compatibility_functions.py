import math
from django.db.models import Count
from collections import defaultdict
from timeit import Timer, default_timer as timer
from ..models import Song, User
from django.db.models import F


def annotate_compatibility_logarithmic_v2(queryset, name_field, counted_field, group_ids):

    for person in group_ids:

        queryset_user = queryset.filter(user=person).values(object_name=F(name_field), object_id=F(counted_field)).annotate(stream_count=Count(
                counted_field)).order_by('-stream_count')


        if not queryset_user:
            continue

        highest_count = max(queryset_user[0]['stream_count']+1, 5)
        highest_value = math.log2(highest_count)  #log2(100) = 6.643856

        for object in queryset_user:
            object['compatibility_score'] = min(1, math.log2(object['stream_count']+1) / highest_value)


    return queryset_user




def sort_by_compatibility_logarithmic(queryset, group_ids, object_to_count):

    master_stream_dict = defaultdict(int)

    for person in group_ids:

        user_queryset = queryset.filter(user=person).prefetch_related(object_to_count).values(object_to_count
                                                            ).annotate(count = Count(object_to_count)).order_by('-count', object_to_count + '__name')


        if not user_queryset:
            continue


        highest_count = max(user_queryset[0]['count']+1, 5)

        highest_value = min(highest_count, 6.643856)  #log2(100) = ~6.643856

        for q in user_queryset:

            master_stream_dict[q[object_to_count]] += min(1, math.log2(q['count']+1) / highest_value)  * ( 1 / len(group_ids))


    master_stream_dict = sorted(master_stream_dict.items(), key=lambda item: item[1], reverse=True)


    return master_stream_dict


def sort_by_compatibility_logarithmic_max_artists(queryset, group_ids, artist_maximum=100, limit=100):

    master_artist_dict = defaultdict(float)

    for person in group_ids:

        queryset_user = queryset.filter(user=person).values('song__song_container', 'song__artist'
                                                            ).annotate(stream_count=Count('song__song_container')).order_by('-stream_count', 'song__song_container__name')

        if not queryset_user:
            continue

        highest_count = max(queryset_user[0]['stream_count']+1, 5)
        highest_value = math.log2(highest_count)  #log2(100) = 6.643856

        for q in queryset_user:

            if q['song__artist'] not in master_artist_dict:
                master_artist_dict[q['song__artist']] = defaultdict(float)

            master_artist_dict[q['song__artist']][q['song__song_container']] += min(1, math.log2(q['stream_count']+1) / highest_value)  * ( 1 / len(group_ids))

    for artist in master_artist_dict:
        master_artist_dict[artist] = {k: v for k, v in sorted(master_artist_dict[artist].items(
        ), key=lambda item: item[1], reverse=True)[:artist_maximum]}

    sorted_song_dict = {}
    for artist in master_artist_dict:
        sorted_song_dict.update(master_artist_dict[artist])


    return dict(sorted(sorted_song_dict.items(), key=lambda item: item[1], reverse=True)[:limit])




def get_compatibility_score_for_song(song_id, group_ids, queryset, object_to_count = 'song__song_container'):

    master_stream_dict = defaultdict(int)

    song_container = Song.objects.get(id=song_id).song_container

    compatibility_score = 0

    for person in group_ids:

        user_queryset = queryset.filter(user=person).prefetch_related(object_to_count).values(object_to_count
                                                            ).annotate(count = Count(object_to_count)).order_by('-count', object_to_count + '__name')


        if not user_queryset:
            continue
        
        song_score = 0

        for obj in user_queryset:

            if obj['song__song_container'] == song_container.id:

                song_score = math.log2(obj['count']+1)

                break


        highest_value = math.log2(user_queryset[0]['count']+1)
        
        compatibility_score += min(1, song_score / highest_value)  * ( 1 / len(group_ids))


    return compatibility_score




def get_compatibilities_score_for_song(song_id, group_ids, queryset, object_to_count = 'song__song_container'):

    master_stream_dict = defaultdict(int)

    song_container = Song.objects.get(id=song_id).song_container

    compatibility_score = 0

    compatibility_score_dict = {}

    for person in group_ids:

        user_queryset = queryset.filter(user=person).prefetch_related(object_to_count).values(object_to_count
                                                            ).annotate(count = Count(object_to_count)).order_by('-count', object_to_count + '__name')

        
        song_score = 0

        for obj in user_queryset:

            if song_container != None:

                if obj['song__song_container'] == song_container.id:

                    song_score = math.log2(obj['count']+1)
                    print('found!')
                    break


        highest_value = math.log2(user_queryset[0]['count']+1)

        username = User.objects.get(id=person).username;
        
        compatibility_score_dict[username] = min(1.0, song_score/(highest_value))


    return compatibility_score_dict