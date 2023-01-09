from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import authentication, permissions
from django.contrib.auth.models import User
from .models import *
from .functions import utils, compatibility_functions
from django.db.models import Count
from django.db.models import F
from django.core.cache import cache
from .serializers import *
from django.db.models import Case, When
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from collections import defaultdict
from collections import OrderedDict
from itertools import islice
from rest_framework.permissions import AllowAny


class V2GetGroupSongs(APIView):

    """
    get the top streamed/compatible songs for groups.
    tries to find the result in the redis cache first.
    """
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        """
        Return the top songs within the selected sort mode (streams, compatibility). 
        """

        if 'sort' not in request.query_params:
            return Response('No sort mode provided in request.', status.HTTP_400_BAD_REQUEST)

        queryset = find_or_create_requested_list_for_group(
            request.query_params['group'], 'songs', request.query_params)
        slice_tuple = get_offset_limit_range(offset=int(
            request.query_params['offset']), limit=int(request.query_params['limit']))
        queryset_list = list(queryset.items())[slice_tuple[0]:slice_tuple[1]]

        serialized_response = queryset_serializer(
            queryset_list, MediumSongContainerSerializer, SongContainer, 'song_container', request.query_params['sort'])

        return Response(serialized_response)


class V2GetGroupAlbums(APIView):
    """
    get the top streamed/compatible albums for groups.
    tries to find the result in the redis cache first.
    """
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        """
        Return the top songs within the selected sort mode (streams, compatibility). 
        """

        if 'sort' not in request.query_params:
            return Response('No sort mode provided in request.', status.HTTP_400_BAD_REQUEST)

        queryset = find_or_create_requested_list_for_group(
            request.query_params['group'], 'albums', request.query_params)
        slice_tuple = get_offset_limit_range(offset=int(
            request.query_params['offset']), limit=int(request.query_params['limit']))
        queryset_list = list(queryset.items())[slice_tuple[0]:slice_tuple[1]]

        serialized_response = queryset_serializer(
            queryset_list, MediumAlbumContainerSerializer, AlbumContainer, 'album_container', request.query_params['sort'])

        return Response(serialized_response)


class V2GetGroupArtists(APIView):
    """
    get the top streamed/compatible albums for groups.
    tries to find the result in the redis cache first.
    """
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        """
        Return the top songs within the selected sort mode (streams, compatibility). 
        """

        if 'sort' not in request.query_params:
            return Response('No sort mode provided in request.', status.HTTP_400_BAD_REQUEST)

        queryset = find_or_create_requested_list_for_group(
            request.query_params['group'], 'artists', request.query_params)
        slice_tuple = get_offset_limit_range(offset=int(
            request.query_params['offset']), limit=int(request.query_params['limit']))
        queryset_list = list(queryset.items())[slice_tuple[0]:slice_tuple[1]]

        serialized_response = queryset_serializer(
            queryset_list, ArtistSerializer, Artist, 'artist', request.query_params['sort'])

        return Response(serialized_response)


class V2GetUserSongs(APIView):
    """
    get the top streamed/compatible songs for users.
    tries to find the result in the redis cache first
    """

    def get(self, request, format=None):
        """
        Return the top songs within the selected sort mode (streams, compatibility). 
        """

        if 'sort' not in request.query_params:
            return Response('No sort mode provided in request.', status.HTTP_400_BAD_REQUEST)

        queryset = find_or_create_requested_list_for_users(
            request.query_params['users'], 'songs', request.query_params)
        slice_tuple = get_offset_limit_range(offset=int(
            request.query_params['offset']), limit=int(request.query_params['limit']))
        queryset_list = list(queryset.items())[slice_tuple[0]:slice_tuple[1]]

        serialized_response = queryset_serializer(
            queryset_list, ListSongContainerSerializer, SongContainer, 'song_container', request.query_params['sort'])

        return Response(serialized_response)


class V2GetUserAlbums(APIView):
    """
    get the top streamed/compatible songs for users.
    tries to find the result in the redis cache first
    """

    def get(self, request, format=None):
        """
        Return the top songs within the selected sort mode (streams, compatibility). 
        """

        if 'sort' not in request.query_params:
            return Response('No sort mode provided in request.', status.HTTP_400_BAD_REQUEST)

        queryset = find_or_create_requested_list_for_users(
            request.query_params['users'], 'albums', request.query_params)

        slice_tuple = get_offset_limit_range(offset=int(
            request.query_params['offset']), limit=int(request.query_params['limit']))
        queryset_list = list(queryset.items())[slice_tuple[0]:slice_tuple[1]]

        serialized_response = queryset_serializer(
            queryset_list, MediumAlbumContainerSerializer, AlbumContainer, 'album_container', request.query_params['sort'])

        return Response(serialized_response)


class V2GetUserArtists(APIView):
    """
    get the top streamed/compatible songs for users.
    tries to find the result in the redis cache first
    """

    def get(self, request, format=None):
        """
        Return the top songs within the selected sort mode (streams, compatibility). 
        """

        if 'sort' not in request.query_params:
            return Response('No sort mode provided in request.', status.HTTP_400_BAD_REQUEST)

        queryset = find_or_create_requested_list_for_users(
            request.query_params['users'], 'artists', request.query_params)

        slice_tuple = get_offset_limit_range(offset=int(
            request.query_params['offset']), limit=int(request.query_params['limit']))
        queryset_list = list(queryset.items())[slice_tuple[0]:slice_tuple[1]]

        serialized_response = queryset_serializer(
            queryset_list, ArtistSerializer, Artist, 'artist', request.query_params['sort'])

        return Response(serialized_response)


def find_or_create_requested_list_for_group(group_id, cache_type, params):
    """
    Tries to find the requested top list in the cache. Otherwise it gets created.
    """

    group = Group.objects.get(id=group_id)

    group_memberships = GroupMembership.objects.filter(group=group)

    group_member_ids = [x['user__id']
                        for x in group_memberships.values('user__id')]

    cached_group_objects = GroupCacheObject.objects.filter(
        group=group, cache_type=cache_type, sort_mode=params['sort'], timeframe=params['timeframe'])

    if cached_group_objects.exists():

        cache_data = cache.get(cached_group_objects[0].key)

        percentage_invalid = int(
            (len(group_member_ids) - cached_group_objects[0].valid_subcaches.count()) / len(group_member_ids) * 100)

        if cache_data == None or percentage_invalid > 20:
            cached_group_objects[0].delete()
        else:
            cached_group_objects.update(
                invalidated_subcache_percentage=percentage_invalid)
            return cache_data

    ranked_list_group = {}

    for group_membership in group_memberships:

        user_ranked_list = find_or_create_requested_list_for_user(
            group_membership.user, cache_type, params)

        for song in user_ranked_list.items():

            if song[0] not in ranked_list_group:
                ranked_list_group[song[0]] = {
                    'name': song[1]['name'], 'score': song[1]['score'], 'energy': 0}
            else:
                ranked_list_group[song[0]]['score'] += song[1]['score']


    if params['sort'] == 'compatibility':
        for k, v in ranked_list_group.items():
            v['score'] = v['score'] / group_memberships.count()

    sorted_ranked_list_group = OrderedDict(
        sorted(ranked_list_group.items(), key=lambda x: (-x[1]['score'], x[1]['name'])))




    # --!-- cache the queryset

    cache_key = f'{group.identifier}:{cache_type}:{params["sort"]}:{params["timeframe"]}'
    cache.set(cache_key, sorted_ranked_list_group, 60 * 60 * 10)
    group_cache = GroupCacheObject.objects.create(
        key=cache_key, group=group, cache_type=cache_type, sort_mode=params['sort'], timeframe=params['timeframe'])

    user_caches = UserCacheObject.objects.filter(
        user__id__in=group_member_ids, cache_type=cache_type, sort_mode=params['sort'], timeframe=params['timeframe'])
    group_cache.valid_subcaches.add(*user_caches)
    group_cache.save()

    return sorted_ranked_list_group





def find_or_create_requested_list_for_users(user_ids, cache_type, params):
    """
    Tries to find the requested top list in the cache. Otherwise it gets created.
    """

    user_ids_list = user_ids.split(',')

    users = User.objects.filter(id__in=user_ids_list)

    ranked_list_users = {}

    for user in users:

        user_ranked_list = find_or_create_requested_list_for_user(
            user, cache_type, params)

        for song in user_ranked_list.items():

            if song[0] not in ranked_list_users:
                ranked_list_users[song[0]] = {
                    'name': song[1]['name'], 'score': song[1]['score'], 'energy': 0}
            else:
                ranked_list_users[song[0]]['score'] += song[1]['score']


    if params['sort'] == 'compatibility':
        for k, v in ranked_list_users.items():
            v['score'] = v['score'] / users.count()

    sorted_ranked_list_group = OrderedDict(
        sorted(ranked_list_users.items(), key=lambda x: (-x[1]['score'], x[1]['name'])))

    return sorted_ranked_list_group



def find_or_create_requested_list_for_user(user, cache_type, params):
    """
    Tries to find the requested top list in the cache. Otherwise it gets created.
    """

    cached_objects = UserCacheObject.objects.filter(
        user=user, cache_type=cache_type, sort_mode=params['sort'], timeframe=params['timeframe'])

    if cached_objects.exists():

        cache_data = cache.get(cached_objects[0].key)

        if cache_data != None:
            return cache_data
        else:

            cached_objects[0].delete()

    # --!-- cache does not exist.. requested data needs to be created and cached

    ranked_list_user = create_ranked_list_for_user(
        user=user, list_type=cache_type, params=params)

    sorted_ranked_list_user = OrderedDict(
        sorted(ranked_list_user.items(), key=lambda x: (-x[1]['score'], x[1]['name'])))


    # --!-- cache the queryset

    cache_key = f'{user.username}:{cache_type}:{params["sort"]}:{params["timeframe"]}'
    cache.set(cache_key, sorted_ranked_list_user)
    UserCacheObject.objects.create(key=cache_key, user=user, cache_type=cache_type,
                                   sort_mode=params['sort'], timeframe=params["timeframe"])

    return sorted_ranked_list_user


def create_ranked_list_for_user(user, list_type, params):

    if list_type == 'songs':
        counted_field = 'song__song_container'
        name_field = 'song__song_container__name'
        queryset = Stream.objects.active().filter(
            user=user).prefetch_related('song__song_container')
    elif list_type == 'albums':
        counted_field = 'song__album__album_container'
        name_field = 'song__album__album_container__name'
        queryset = Stream.objects.active().filter(
            user=user).prefetch_related('song__album__album_container')
    elif list_type == 'artists':
        counted_field = 'song__artist'
        name_field = 'song__artist__name'
        queryset = Stream.objects.active().filter(
            user=user).prefetch_related('song__artist')

    queryset_timeframe = utils.set_timeframe(queryset, params['timeframe'])

    user_dict_to_cache = {}

    if (params['sort'] == 'streams'):
        queryset_timeframe = queryset_timeframe.values(object_name=F(name_field), object_id=F(counted_field)).annotate(stream_count=Count(
            counted_field))
        for q in queryset_timeframe:
            user_dict_to_cache[q['object_id']] = {
                'name': q['object_name'], 'score': q['stream_count'], 'energy': 0}

    elif (params['sort'] == 'compatibility'):
        queryset_timeframe = compatibility_functions.annotate_compatibility_logarithmic_v2(
            queryset_timeframe, name_field, counted_field, [user.id])
        for q in queryset_timeframe:
            user_dict_to_cache[q['object_id']] = {
                'name': q['object_name'], 'score': q['compatibility_score'], 'energy': 0}

    return user_dict_to_cache


def queryset_serializer(queryset, serializer, model_type, name, sort_mode='streams'):

    serialized_response = []

    query_object_ids = [object[0] for object in queryset]

    prefetch_relations = []

    if model_type == SongContainer:
        prefetch_relations = ['artist', 'album_container',
                              'album_container__master_child_album', 'album_container__master_child_album__image']
    elif model_type == AlbumContainer:
        prefetch_relations = [
            'artist', 'master_child_album', 'master_child_album__image']
    elif model_type == Artist:
        prefetch_relations = ['image']


    all_serialized_objects = serializer(model_type.objects.filter(
        id__in=query_object_ids).prefetch_related(*prefetch_relations),  many=True).data


    for object in queryset:


        try:

            value = next((index, item) for index, item in enumerate(
                all_serialized_objects) if item["id"] == object[0])
            obj = {name: value[1]}

            all_serialized_objects.pop(value[0])

            if sort_mode == 'streams':
                obj['score'] = object[1]['score']
                serialized_response.append(obj)
            else:
                obj['score'] = object[1]['score']
                serialized_response.append(obj)
        except:
            pass

    return serialized_response


def get_offset_limit_range(offset, limit):

    if offset == None:
        offset = 0

    if limit == None:
        limit = 5

    return (offset, offset+limit)
