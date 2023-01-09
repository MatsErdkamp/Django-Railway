
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import *
from django.db.models import Count, F, Avg
from .models import Stream, Artist, Album, Song, Playlist, UserFollow, Genre, Profile, SocialDisplaySession
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import datetime
from .functions import recommendation_playlist_functions, compatibility_functions, chart_functions, color_functions, spotify_get_functions, spotify_post_functions, model_functions, utils
from django.utils.timezone import make_aware
from django.db.models import Case, When
from rest_framework.permissions import AllowAny
import json
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from random import randint


class APIGetSearchResults(APIView):

    def get(self, request):

        q = self.request.query_params.get('q')

        user = self.request.user
        response = spotify_get_functions.search(
            user=user, q=q, type='track', limit=50)

        response_uris_songs = [x['uri'] for x in response['tracks']['items']]

        # does this preserve order?
        # it does not lmao
        response_filtered_songs = Song.objects.filter(
            uri__in=response_uris_songs).exclude(song_container=None)
        artist_count = response_filtered_songs.values(
            'artist').annotate(count=Count('artist'))
        album_count = response_filtered_songs.values(
            'album').annotate(count=Count('album'))

        search_response = []

        for search in artist_count:
            if search["count"] > 4:
                artist = Artist.objects.get(id=search['artist'])
                search_data = {}
                search_data["id"] = artist.id
                search_data["uri"] = artist.uri
                search_data["name"] = artist.name
                search_data["image"] = ImageSerializer(artist.image).data
                search_data["type"] = "artist"
                search_response.append(search_data)

        for search in album_count:
            if search["count"] > 6:
                album = Album.objects.get(id=search['album'])
                search_data = {}
                search_data["id"] = album.id
                search_data["uri"] = album.uri
                search_data["name"] = album.name
                search_data["album_container"] = album.album_container.id
                search_data["image"] = ImageSerializer(album.image).data
                search_data["type"] = "album"

                if q.lower() in album.name.lower():
                    search_response.insert(0, search_data)
                else:
                    search_response.append(search_data)

        for search in response_filtered_songs:

            search_data = {}
            search_data["id"] = search.id
            search_data["uri"] = search.uri
            search_data["name"] = search.name
            search_data["artist"] = search.artist.name
            search_data["song_container"] = search.song_container.id
            search_data["image"] = ImageSerializer(search.album.image).data
            search_data["type"] = "song"
            search_response.append(search_data)

        return Response(search_response)


class APIGetUser(APIView):

    def get(self, request):

        user = self.request.user


        response = {}
        response['authenticated'] = self.request.user.is_authenticated
        response['user'] = UserSerializer(User.objects.get(id=user.id)).data

        # exclude accounts without auth AND yourself from friends (without auth is hotfix -> del once friends added)
        # + [x.id for x in User.objects.filter(social_auth=None)]
        excluded = [user.id] + \
            [x.id for x in User.objects.filter(social_auth=None)]
        follows_ids = [x.follows.id for x in user.follower.all()]

        response['following'] = UserSerializer(
            User.objects.filter(id__in=follows_ids), many=True).data

        return Response(response)


class APITerminateUser(APIView):

    def get(self, request):

        user = self.request.user

        user.is_active = False
        user.save()
        

        return Response('user has been deactivated')


class APIGetUserProfile(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):

        user = self.request.user


        response = {}
        response['authenticated'] = self.request.user.is_authenticated

        if response['authenticated'] == False:
            return response


        id = self.request.query_params.get('id')
        username = self.request.query_params.get('username')

        if (id != None):
            profile_user = User.objects.get(id=id)
        elif (username != None):
            profile_user = User.objects.get(username=username)
        else:
            profile_user = user

        # NEEDS TO BE CHANGED TO ACCOUNT FOR INACTIVE SUBSCRIPTIONS
        response['pro_user'] = StripeCustomer.objects.filter(
            user=profile_user).exists()

        try:
            profile = profile_user.profile
        except ObjectDoesNotExist:
            profile = Profile.objects.create_profile(profile_user)

        image_functions.refresh_profile_images([profile])

        if profile.image != None:
            if profile.image.primary_color == None:
                color_functions.generate_colors(profile.image)

        response['profile'] = ProfileSerializer(profile).data

        response['favorites'] = {}

        groups = [x.group for x in GroupMembership.objects.filter(
            user=profile_user)]

        response['groups'] = SmallGroupSerializer(
            groups, many=True).data

        follows_ids = [x.follows.id for x in user.follower.all()]
        follower_ids = [x.user.id for x in user.follows.all()]

        response['profile']['following'] = UserSerializer(
            User.objects.filter(id__in=follows_ids), many=True).data

        response['profile']['followers'] = UserSerializer(
            User.objects.filter(id__in=follower_ids), many=True).data

        return response

    def get(self, request):

        response = self.get_queryset()

        return Response(response)


class APIUserRecommendations(APIView):

    def post(self, request, format=None):

        user_from = self.request.user
        song_to_recommend = Song.objects.get(id=request.data['song_id'])
        user_to = User.objects.filter(id=request.data['user_to_id']).first()
        description = request.data['description']

        if user_to != None:
            SongRecommendation.objects.create(
                user_from=user_from, user_to=user_to, song=song_to_recommend, description=description)
            recommendation_playlist_functions.update_recommendation_playlist_content(
                user_to.id)
            return Response('Recommendation posted!')
        else:
            return Response('no valid user selected!', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):

        user = self.request.user

        response = {}
        response['received'] = SongRecommendationSerializer(
            user.recommendation_receiver.all().order_by('-timestamp'), many=True).data
        response['sent'] = SongRecommendationSerializer(
            user.recommendation_sender.all().order_by('-timestamp'), many=True).data

        return Response(response)


class APIUserSearchHistory(APIView):

    def post(self, request):

        user = self.request.user
        profile = Profile.objects.get(user__id=user.id)

        search_history = json.loads(profile.search_history)

        print(request.data)

        for s in search_history:
            if s["id"] == request.data["id"]:
                search_history.remove(s)

        search_result_dict = {
            "id": request.data["id"], "type": request.data["type"]}

        search_history.insert(
            0, search_result_dict)
        profile.search_history = json.dumps(search_history[:20])
        profile.save()
        response = []

        return Response(response)

    def get(self, request):

        user = self.request.user
        profile = Profile.objects.get(user__id=user.id)

        search_history = json.loads(profile.search_history)

        search_history_response = []

        for search in search_history:

            if search["type"] == "song":
                search_data = search
                search_obj = Song.objects.get(id=search["id"])
                search_data["song_container"] = search_obj.song_container.id
                search_data["uri"] = search_obj.uri
                search_data["image"] = ImageSerializer(
                    search_obj.album.image).data
                search_data["name"] = search_obj.name
                search_history_response.append(search_data)

            elif search["type"] == "album":
                search_data = search
                search_obj = Album.objects.get(id=search["id"])
                search_data["album_container"] = search_obj.album_container.id
                search_data["uri"] = search_obj.uri
                search_data["image"] = ImageSerializer(
                    search_obj.image).data
                search_data["name"] = search_obj.name
                search_history_response.append(search_data)

            elif search["type"] == "artist":
                search_data = search
                search_obj = Artist.objects.get(id=search["id"])
                search_data["uri"] = search_obj.uri
                search_data["image"] = ImageSerializer(search_obj.image).data
                search_data["name"] = search_obj.name
                search_history_response.append(search_data)

        response = search_history_response

        return Response(response)


class APIPostStreams(APIView):

    def post(self, request, format=None):

        print(request.data)

        return Response('poop scoop')


class APIGetUsers(APIView):

    def get(self, request):

        user = self.request.user
        response = {}
        # exclude accounts without auth AND yourself from friends (without auth is hotfix -> del once friends added)

        # + [x.id for x in User.objects.filter(social_auth=None)]
        excluded = [user.id] + \
            [x.id for x in User.objects.filter(social_auth=None)]

        follows_ids = [x.follows.id for x in user.follower.all()]

        response['following'] = UserSerializer(
            User.objects.filter(id__in=follows_ids), many=True).data

        # response['following'] = []
        response['other_users'] = UserSerializer(
            User.objects.all().exclude(id__in=excluded + follows_ids), many=True).data

        return Response(response)


class APIGetUserProfiles(APIView):

    def get(self, request):

        user = self.request.user
        response = {}
        # exclude accounts without auth AND yourself from friends (without auth is hotfix -> del once friends added)

        # + [x.id for x in User.objects.filter(social_auth=None)]
        excluded = [user.id] + \
            [x.id for x in User.objects.filter(social_auth=None)]

        follows_ids = [x.follows.id for x in user.follower.all()]
        follower_ids = [x.user.id for x in user.follows.all()]

        response['following'] = ProfileSerializer(
            Profile.objects.filter(user__id__in=follows_ids), many=True).data

        response['followers'] = ProfileSerializer(
            Profile.objects.filter(user__id__in=follower_ids), many=True).data

        # response['following'] = []
        response['other_users'] = ProfileSerializer(
            Profile.objects.all().exclude(user__id__in=follows_ids+excluded), many=True).data

        return Response(response)


class APIFollowUser(APIView):

    def post(self, request):

        user = self.request.user
        user_to_follow = User.objects.get(
            id=request.data['user_to_follow'])

        UserFollow.objects.create(user=user,
                                  follows=user_to_follow)

        follows_ids = [x.follows.id for x in user.follower.all()]

        response = UserSerializer(
            User.objects.filter(id__in=follows_ids), many=True).data

        return Response(response)


class APIUnfollowUser(APIView):

    def post(self, request):

        user = self.request.user

        print(request.data)

        user_to_unfollow = request.data['user_to_unfollow']

        UserFollow.objects.filter(user=user).get(
            follows=user_to_unfollow).delete()

        follows_ids = [x.follows.id for x in user.follower.all()]

        response = UserSerializer(
            User.objects.filter(id__in=follows_ids), many=True).data

        return Response(response)


class APIGetGroup(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        identifier = self.request.query_params.get('identifier')
        print(identifier)

        response = GroupSerializer(Group.objects.get(
            identifier=identifier), context={'request': request}).data

        response['primary_color'] = '75,75,75'

        if identifier == 'theneedledrop':
            response['primary_color'] = '241,239,128'
        elif identifier == 'hivemind':
            response['primary_color'] = '251,194,1'



        return Response(response)

class APIGetGroupPlaylists(APIView):

    def get(self, request):

        identifier = self.request.query_params.get('identifier')

        group_playlists = GroupPlaylist.objects.filter(group__identifier=identifier)

        response = SmallGroupPlaylistSerializer(group_playlists, context={'request': request}, many=True).data

        return Response(response)


class APIGetUserGroups(APIView):


    def get(self, request):

        joined_groups = [
            x.group for x in self.request.user.groupmembership_set.select_related('group').all()]

        other_groups = Group.objects.filter(private=False).exclude(
            id__in=[x.id for x in joined_groups])

        response = {}
        response['joined_groups'] = GroupSerializer(joined_groups, context={
            'request': request}, many=True).data

        response['other_groups'] = GroupSerializer(other_groups, context={
            'request': request}, many=True).data

        return Response(response)


class APIJoinGroup(APIView):

    def post(self, request):

        user = self.request.user
        group_to_join = Group.objects.get(
            id=request.data['group_to_join'])

        GroupMembership.objects.create(user=user,
                                       group=group_to_join)

        response = {}

        groups = [x.group for x in GroupMembership.objects.filter(
            user=user)]

        response['groups'] = SmallGroupSerializer(
            groups, many=True).data

        return Response(response)


class APILeaveGroup(APIView):

    def post(self, request):

        user = self.request.user
        group_to_leave = Group.objects.get(
            id=request.data['group_to_leave'])

        membership = GroupMembership.objects.filter(
            user=self.request.user).filter(group=group_to_leave)

        if membership.exists():
            membership.delete()

        response = {}

        groups = [x.group for x in GroupMembership.objects.filter(
            user=user)]

        response['groups'] = SmallGroupSerializer(
            groups, many=True).data


        return Response(response)


class APIGetStreams(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self, user):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """

        users = self.request.query_params.get('users')
        limit = self.request.query_params.get('limit')
        offset = self.request.query_params.get('offset')
        after = self.request.query_params.get('after')
        before = self.request.query_params.get('before')

        #MESSY CODE
        if users == 'undefined':
            return None

        if users:
            group_ids = users.split(',')
        else:
            return None


        if before is None:

            if user.id in list(group_ids):
                Stream.objects.fetch_streams(user)
            else:
                Stream.objects.fetch_streams(User.objects.get(id=group_ids[0]))

        queryset = Stream.objects.active().prefetch_related('user', 'song', 'song__artist',
                                                            'song__album', 'song__album__image').order_by('-played_at')



        queryset = queryset.filter(user__in=group_ids)

        if before is not None:
            time = make_aware(datetime.datetime.utcfromtimestamp(
                int(before)/1000)).isoformat()
            queryset = queryset.filter(played_at__lt=time)

        if after is not None:
            time = make_aware(datetime.datetime.utcfromtimestamp(
                int(after)/1000)).isoformat()
            queryset = queryset.filter(played_at__gt=time)

        queryset = set_offset(queryset, offset)
        queryset = set_limit(queryset, limit)

        return queryset

    def get(self, request, format=None):

        user = self.request.user

        if self.request.query_params.get('demo') == 'true':
            demo_streams = Stream.objects.active().order_by('-played_at')

            before = self.request.query_params.get('before')

            if before is not None:
                time = make_aware(datetime.datetime.utcfromtimestamp(
                    int(before)/1000)).isoformat()
                demo_streams = demo_streams.filter(played_at__lt=time)

            offset = 0
            if self.request.query_params.get('offset') != None:
                offset = int(self.request.query_params.get('offset'))

            demo_streams = set_offset(demo_streams, offset)
            demo_streams = set_limit(demo_streams, int(
                self.request.query_params.get('limit')))
            demo_streams_serialized = StreamSerializer(demo_streams, many=True)
            return Response(demo_streams_serialized.data)

        if self.request.query_params.get('after') != 'NaN':

            streams = self.get_queryset(user)
            streams_serialized = StreamSerializer(streams, many=True)
            return Response(streams_serialized.data)
        else:
            return Response({"Failure": "Error"}, status=status.HTTP_400_BAD_REQUEST)


class APIGetArtists(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self, user):

        users = self.request.query_params.get('users', None)
        group_id = self.request.query_params.get('group', None)
        # group_weights = self.request.query_params.get('weights', None)
        limit = self.request.query_params.get('limit', None)
        offset = self.request.query_params.get('offset', None)
        sort = self.request.query_params.get('sort', None)
        timeframe = self.request.query_params.get('timeframe', None)
        genres = self.request.query_params.get('genres', None)

        queryset = Stream.objects.active()
        queryset = utils.set_timeframe(queryset, timeframe)

        if genres:
            queryset = filter_artist_genres(queryset, genres.split(","))

        if group_id:
            users_ids = [x['user__id'] for x in Group.objects.get(
                id=group_id).groupmembership_set.all().values('user__id')]
            queryset = queryset.filter(user__in=users_ids)
        elif users:
            users_ids = users.split(',')
            queryset = queryset.filter(user__in=users_ids)
        else:
            users_ids = ""

        # if group_weights:
        #     group_weights = group_weights.split(',')

        if (sort == 'streams'):
            queryset = queryset.values('song__artist').annotate(artist_stream_count=Count(
                'song__artist')).order_by('-artist_stream_count', 'song__artist__name')
        else:
            queryset = compatibility_functions.sort_by_compatibility_logarithmic(
                queryset, users_ids, object_to_count='song__artist')

        queryset = set_limit(queryset, 999)

        return queryset

    def get(self, request, format=None):

        demo = self.request.query_params.get('demo', None)
        if demo == 'true':
            self.request.user = User.objects.get(username='MatsErdkamp')

        query_cache_key = convert_query_params_to_hashed_cache_key(
            self.request.user, 'chart-artists-query', self.request.query_params, ['limit', 'offset'])
        query_cache = cache.get(query_cache_key)

        limit = self.request.query_params.get('limit', None)
        offset = self.request.query_params.get('offset', None)

        query_was_cached = False

        if query_cache != None:
            query = query_cache
            query_was_cached = True
        else:
            query = self.get_queryset(self.request.user)
            cache.set(query_cache_key, query, 300)

        response_cache_key = convert_query_params_to_hashed_cache_key(
            self.request.user, 'chart-artists-response', self.request.query_params,  [])
        response_cache = cache.get(response_cache_key)

        if response_cache != None and query_was_cached == True:
            serialized_response = response_cache
        else:
            query_offset = set_offset(query, offset)
            query_offset_limited = set_limit(query_offset, limit)

            sort = self.request.query_params.get('sort', None)
            serialized_response = []

            for artist in query_offset_limited:

                if sort == 'streams':
                    obj = {'artist': ArtistSerializer(Artist.objects.get(
                        id=artist['song__artist'])).data}
                    obj['count'] = artist['artist_stream_count']
                else:
                    obj = {'artist': ArtistSerializer(Artist.objects.get(
                        id=artist[0])).data}
                    obj['score'] = artist[1]

                serialized_response.append(obj)

        # we could decrease the cache time based on the offset...
        cache.set(response_cache_key, serialized_response, 300)

        return Response(serialized_response)


class APIGetAlbumItems(APIView):

    def get(self, request, format=None):

        uri = self.request.query_params.get('id', None)
        user = self.request.user

        context = {}
        context['uri'] = str('spotify:album:' + uri)
        context['items'] = spotify_get_functions.get_album_tracks(
            user=user, uri=uri, limit=100, offset=0)
        context['primary_color'] = Album.objects.get(
            uri=str('spotify:album:' + uri)).image.primary_color

        return Response(context)


class APIGetAlbums(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self, user):

        users = self.request.query_params.get('users', None)
        group_id = self.request.query_params.get('group', None)
        limit = self.request.query_params.get('limit', None)
        offset = self.request.query_params.get('offset', None)
        sort = self.request.query_params.get('sort', None)
        timeframe = self.request.query_params.get('timeframe', None)
        genres = self.request.query_params.get('genres', None)

        queryset = Stream.objects.active()
        queryset = utils.set_timeframe(queryset, timeframe)

        if genres:
            queryset = filter_artist_genres(queryset, genres.split(","))

        if group_id:
            users_ids = [x['user__id'] for x in Group.objects.get(
                id=group_id).groupmembership_set.all().values('user__id')]
            queryset = queryset.filter(user__in=users_ids)
        elif users:
            users_ids = users.split(',')
            queryset = queryset.filter(user__in=users_ids)
        else:
            users_ids = ""

        if (sort == 'streams'):
            # queryset = queryset.values('song__album').annotate(album_stream_count=Count(
            #     'song__album')).order_by('-album_stream_count', 'song__album__name')
            queryset = queryset.values('song__album__album_container').annotate(album_stream_count=Count(
                'song__album__album_container')).order_by('-album_stream_count', 'song__album__album_container__name')

        else:
            queryset = compatibility_functions.sort_by_compatibility_logarithmic(
                queryset, users_ids, object_to_count='song__album__album_container')

        queryset = set_limit(queryset, 999)

        return queryset

    def get(self, request, format=None):

        demo = self.request.query_params.get('demo', None)
        if demo == 'true':
            self.request.user = User.objects.get(username='MatsErdkamp')

        query_cache_key = convert_query_params_to_hashed_cache_key(
            self.request.user, 'chart-albums-query', self.request.query_params, ['limit', 'offset'])

        query_cache = cache.get(query_cache_key)

        limit = self.request.query_params.get('limit', None)
        offset = self.request.query_params.get('offset', None)

        query_was_cached = False

        if query_cache != None:
            query = query_cache
            query_was_cached = True
        else:
            query = self.get_queryset(self.request.user)
            cache.set(query_cache_key, query, 300)

        response_cache_key = convert_query_params_to_hashed_cache_key(
            self.request.user, 'chart-albums-response', self.request.query_params,  [])
        response_cache = cache.get(response_cache_key)

        if response_cache != None and query_was_cached == True:
            serialized_response = response_cache
        else:
            query_offset = set_offset(query, offset)
            query_offset_limited = set_limit(query_offset, limit)

            sort = self.request.query_params.get('sort', None)
            serialized_response = []

            for album in query_offset_limited:

                try:
                    if sort == 'streams':

                        obj = {'album_container': AlbumContainerSerializer(
                            AlbumContainer.objects.get(id=album['song__album__album_container'])).data}
                        obj['count'] = album['album_stream_count']
                    else:
                        obj = {'album_container': AlbumContainerSerializer(
                            AlbumContainer.objects.get(id=album[0])).data}
                        obj['score'] = album[1]
                except:
                    pass

                serialized_response.append(obj)

            # we could decrease the cache time based on the offset...
            cache.set(response_cache_key, serialized_response, 300)

        return Response(serialized_response)


class APIGetSongs(APIView):
    permission_classes = [AllowAny]


    # @cached_as(Stream, timeout=120)
    def get_queryset(self):

        users = self.request.query_params.get('users', None)
        group_id = self.request.query_params.get('group', None)
        sort = self.request.query_params.get('sort', None)
        artists = self.request.query_params.get('artists', None)
        timeframe = self.request.query_params.get('timeframe', None)
        # popularity_range = self.request.query_params.get('popularity', None)
        # genres = self.request.query_params.get('genres', None)
        release_range = self.request.query_params.get('release_range', None)
        energy_range = self.request.query_params.get('energy', None)
        valence_range = self.request.query_params.get('valence', None)
        danceability_range = self.request.query_params.get(
            'danceability', None)

        user = self.request.user

        queryset = Stream.objects.active()
        queryset = utils.set_timeframe(queryset, timeframe)

        if artists:
            artist_ids = artists.split(',')
            queryset = queryset.filter(song__artist__id__in=artist_ids)

        if release_range:
            release_range = release_range.split(',')
            queryset = set_query_range(
                queryset, 'song__album__release_date', release_range[0], release_range[1])

        if energy_range:
            energy_range = energy_range.split(',')
            queryset = set_query_range(
                queryset, 'song__energy', energy_range[0], energy_range[1])

        if valence_range:
            valence_range = valence_range.split(',')
            queryset = set_query_range(
                queryset, 'song__valence', valence_range[0], valence_range[1])

        if danceability_range:
            danceability_range = danceability_range.split(',')
            queryset = set_query_range(
                queryset, 'song__danceability', danceability_range[0], danceability_range[1])

        if group_id:
            users_ids = [x['user__id'] for x in Group.objects.get(
                id=group_id).groupmembership_set.all().values('user__id')]
            queryset = queryset.filter(user__in=users_ids)
        elif users:
            users_ids = users.split(',')
            queryset = queryset.filter(user__in=users_ids)
        else:
            users_ids = ""

        if (sort == 'streams'):
            queryset = queryset.values('song__song_container').annotate(song_stream_count=Count(
                'song__song_container')).order_by('-song_stream_count', 'song__song_container__name')
        else:
            queryset = compatibility_functions.sort_by_compatibility_logarithmic(
                queryset, users_ids, object_to_count='song__song_container')

        queryset = set_limit(queryset, 999)

        return queryset


    def get(self, request, format=None):


        demo = self.request.query_params.get('demo', None)
        if demo == 'true':
            self.request.user = User.objects.get(username='MatsErdkamp')

        query_cache_key = convert_query_params_to_hashed_cache_key(
            self.request.user, 'chart-songs-query', self.request.query_params, ['limit', 'offset'])
        query_cache = cache.get(query_cache_key)

        limit = self.request.query_params.get('limit', None)
        offset = self.request.query_params.get('offset', None)

        query_was_cached = False

        if query_cache != None:
            query = query_cache
            query_was_cached = True
        else:
            query = self.get_queryset()
            cache.set(query_cache_key, query, 300)

        response_cache_key = convert_query_params_to_hashed_cache_key(
            self.request.user, 'chart-songs-response', self.request.query_params,  [])
        response_cache = cache.get(response_cache_key)

        if response_cache != None and query_was_cached == True:
            serialized_response = response_cache
        else:
            query_offset = set_offset(query, offset)
            query_offset_limited = set_limit(query_offset, limit)

            serialized_response = []

            sort = self.request.query_params.get('sort', None)
            for song in query_offset_limited:

                if sort == 'streams':
                    try:
                        obj = {'song_container': ListSongContainerSerializer(SongContainer.objects.get(
                            id=song['song__song_container'])).data}
                        obj['count'] = song['song_stream_count']
                    except:
                        # SONG CONTAINER NOT FOUND!
                        pass
                else:
                    obj = {'song_container': ListSongContainerSerializer(SongContainer.objects.get(
                        id=song[0])).data}
                    obj['score'] = song[1]

                serialized_response.append(obj)

            # we could decrease the cache time based on the offset...
            cache.set(response_cache_key, serialized_response, 300)

        return Response(serialized_response)


class APIGetCurrentlyStreaming(APIView):

    def get(self, request, format=None):

        user = self.request.user
        group = self.request.query_params.get('users', None)

        if group:
            group_ids = group.split(',')

        else:
            group_ids = []

        response = {}
        response['user'] = []
        response['group'] = []

        user_current = None
        user_current = Stream.objects.fetch_playing(user=user)

        if user_current is not None:
            context = SongSerializer(Song.objects.filter(
                uri=user_current['item']['uri']), many=True).data[0]
            context['user'] = UserSerializer(user).data
            response['user'].append(context)

        for member in group_ids:
            friend_current = None
            friend_current = Stream.objects.fetch_playing(
                user=User.objects.get(id=member))

            if friend_current is not None:
                context = SongSerializer(Song.objects.filter(
                    uri=friend_current['item']['uri']), many=True).data[0]
                context['user'] = UserSerializer(
                    User.objects.get(id=member)).data
                response['group'].append(context)

        return Response(response)


class APIGetSongDetail(APIView):

    def get(self, request, format=None):

        user = self.request.user

        id = self.request.query_params.get('id', None)
        timeframe = self.request.query_params.get('timeframe', None)

        if(id):

            streams_all = Stream.objects.active().filter(song=id)

            streams_timeframe = utils.set_timeframe(streams_all, timeframe)

            stream_count_all = streams_timeframe.count()
            stream_count_personal = streams_timeframe.filter(user=user).count()

            context = {'song': SongSerializer(Song.objects.filter(
                id=id), many=True).data[0]}

            context['stream_counts'] = {
                'total': stream_count_all,
                'self': stream_count_personal,
            }

            top_streamers = streams_timeframe.values('user__username').annotate(
                Count('song')).order_by('-song__count', 'user__username')
            context['top_streamers'] = top_streamers.values(
                name=F('user__username'), stream_count=F('song__count'))

            return Response(context)

        else:
            return Response(['ENTER AN ID AS PARAM'])


class APIGetSongContainerDetail(APIView):
    permission_classes = [AllowAny]

    @method_decorator(cache_page(60*5))
    def get(self, request, format=None):

        user = self.request.user

        id = self.request.query_params.get('id', None)
        timeframe = self.request.query_params.get('timeframe', None)

        if (id == 'null'):
            return Response('No ID provided.', status.HTTP_400_BAD_REQUEST)

        context = {'song_container': SongContainerSerializer(SongContainer.objects.filter(
            id=id).first()).data}

        # RETURN EARLY IN DEMO MODE
        if self.request.query_params.get('demo', None) == 'true':
            context['stream_counts'] = {
                'total': 0,
                'self': 0
            }
            context['suggested_comparison_friend_id'] = 1
            context['unauthorized'] = True
            return Response(context)

        streams_all = Stream.objects.active().filter(
            song__song_container__id=id)
        streams_timeframe = utils.set_timeframe(streams_all, timeframe)

        top_streamers = streams_timeframe.values('user__username', 'user__id').annotate(
            Count('song')).order_by('-song__count', 'user__username')

        stream_count_all = streams_timeframe.count()
        stream_count_personal = streams_timeframe.filter(user=user).count()

        context['stream_counts'] = {
            'total': stream_count_all,
            'self': stream_count_personal,
        }

        context['top_streamers'] = top_streamers.values(
            username=F('user__username'), id=F('user__id'), stream_count=F('song__count'))

        follows_ids = [x.follows.id for x in user.follower.all()]

        if len(top_streamers.filter(user__id__in=follows_ids)) > 0:
            left = top_streamers.filter(user__id__in=follows_ids)[
                0]['user__id']
        else:
            left = user.id

        try:
            receiver = user.follower.all()[0].follows.id
        except:
            receiver = None

        context['suggested_recommendation_receiver_id'] = receiver

        context['suggested_comparison_friend_id'] = left

        # album_distribution_chart = spotify_get_functions.get_album_distribution_chart(
        #     id=context['album']['uri'], user=user, left=left, right=user.id, timeframe=timeframe)

        # context['distribution_chart'] = album_distribution_chart

        return Response(context)


class APIGetSongCompatibility(APIView):

    def get(self, request, format=None):

        user = self.request.user

        song_id = self.request.query_params.get('song_id', None)
        group = self.request.query_params.get('users', None)

        if group:
            group_ids = group.split(',')
        else:
            group_ids = []

        queryset = Stream.objects.active().filter(user__id__in=group_ids)

        context = compatibility_functions.get_compatibility_score_for_song(
            song_id, group_ids, queryset)

        return Response(context)


class APIGetSongCompatibilities(APIView):

    def get(self, request, format=None):

        user = self.request.user

        song_id = self.request.query_params.get('song_id', None)
        group = self.request.query_params.get('users', None)

        if group:
            group_ids = group.split(',')
        else:
            group_ids = []

        queryset = Stream.objects.active().filter(user__id__in=group_ids)

        context = compatibility_functions.get_compatibilities_score_for_song(
            song_id, group_ids, queryset)

        return Response(context)


class APIGetArtistDetail(APIView):
    permission_classes = [AllowAny]

    @method_decorator(cache_page(60*5))
    def get(self, request, format=None):

        user = self.request.user

        id = self.request.query_params.get('id', None)
        timeframe = self.request.query_params.get('timeframe', None)

        if(id):

            context = {'artist': ArtistSerializer(Artist.objects.filter(
                id=id), many=True).data[0]}

            # RETURN EARLY IN DEMO MODE
            if self.request.query_params.get('demo', None) == 'true':
                context['stream_counts'] = {
                    'total': 0,
                    'self': 0
                }
                context['suggested_comparison_friend_id'] = 1
                context['unauthorized'] = True
                return Response(context)

            streams_all = Stream.objects.active().filter(song__artist__id=id)
            streams_timeframe = utils.set_timeframe(streams_all, timeframe)

            top_streamers = streams_timeframe.values('user__username', 'user__id').annotate(
                Count('song__artist')).order_by('-song__artist__count', 'user__username')

            stream_count_all = streams_timeframe.count()
            stream_count_personal = streams_timeframe.filter(user=user).count()

            context['stream_counts'] = {
                'total': stream_count_all,
                'self': stream_count_personal
            }

            context['top_streamers'] = top_streamers.values(
                username=F('user__username'), id=F('user__id'), stream_count=F('song__artist__count'))

            follows_ids = [x.follows.id for x in user.follower.all()]

            if len(top_streamers.filter(user__id__in=follows_ids)) > 0:
                left = top_streamers.filter(user__id__in=follows_ids)[
                    0]['user__id']
            else:
                left = user.id

            context['suggested_comparison_friend_id'] = left

            return Response(context)

        else:
            return Response(['ENTER AN ID AS PARAM'])


class APIGetArtistDetailDistribution(APIView):

    def get(self, request, format=None):

        left = self.request.query_params.get('left', None)
        right = self.request.query_params.get('right', None)

        user = self.request.user
        id = self.request.query_params.get('id', None)
        timeframe = self.request.query_params.get('timeframe', None)

        if(id):

            uri = Artist.objects.get(id=id).uri

            artist_stream_details = chart_functions.get_artist_distribution_chart(
                uri=uri, user=user, left=left, right=right, timeframe=timeframe)

            context = {}
            context['distribution_chart'] = artist_stream_details
            return Response(context)

        else:
            return Response(['ENTER AN ID AS PARAM'])


class APIGetArtistStreamsOverTime(APIView):

    def get(self, request, format=None):

        user = self.request.user
        group_one = self.request.query_params.get('group_one', None)
        group_two = self.request.query_params.get('group_two', None)
        timeframe = self.request.query_params.get('timeframe', None)
        id = self.request.query_params.get('id', None)

        if group_one == None:
            group_one = [user.id]
        else:
            group_one = list(map(int, group_one.split(",")))

        if group_two == None:
            streams_all = Stream.objects.active().filter(
                song__artist__id=id)
            streams_timeframe = utils.set_timeframe(streams_all, timeframe)

            top_streamers = streams_timeframe.values('user__username', 'user__id').annotate(
                Count('song__artist')).order_by('-song__artist__count', 'user__username')
            follows_ids = [x.follows.id for x in user.follower.all()]

            if (top_streamers.filter(user__id__in=follows_ids).exclude(user=user).exists()):
                group_two = [top_streamers.filter(user__id__in=follows_ids).exclude(user=user)[
                    0]['user__id']]
            else:
                group_two = [user.id]
        else:
            group_two = list(map(int, group_two.split(",")))

        if(id):

            artist = Artist.objects.get(id=id)

            album_stream_details = chart_functions.get_streams_over_time_chart_artist(
                artist=artist, user=user, timeframe=timeframe, group_one=group_one, group_two=group_two)

            group_one_dict = {}
            group_two_dict = {}

            for member in group_one:
                group_one_dict[member] = User.objects.get(id=member).username

            for member in group_two:
                group_two_dict[member] = User.objects.get(id=member).username

            response_dict = {}
            response_dict["users"] = {
                'group_one': group_one_dict, 'group_two': group_two_dict}
            response_dict["data"] = album_stream_details

            return Response(response_dict)

        else:
            return Response(['ENTER AN ID AS PARAM'])


class APIGetAlbumDetail(APIView):

    def get(self, request, format=None):

        user = self.request.user

        id = self.request.query_params.get('id', None)
        timeframe = self.request.query_params.get('timeframe', None)

        if (id):

            streams_all = Stream.objects.active().filter(song__album__id=id)
            streams_timeframe = utils.set_timeframe(streams_all, timeframe)

            top_streamers = streams_timeframe.values('user__username', 'user__id').annotate(
                Count('song__album')).order_by('-song__album__count', 'user__username')

            stream_count_all = streams_timeframe.count()
            stream_count_personal = streams_timeframe.filter(user=user).count()

            context = {'album': AlbumSerializer(Album.objects.filter(
                id=id), many=True).data[0]}

            context['stream_counts'] = {
                'total': stream_count_all,
                'self': stream_count_personal,
            }

            context['top_streamers'] = top_streamers.values(
                name=F('user__username'), stream_count=F('song__album__count'))

            follows_ids = [x.follows.id for x in user.follower.all()]

            if len(top_streamers.filter(user__id__in=follows_ids)) > 0:
                left = top_streamers.filter(user__id__in=follows_ids)[
                    0]['user__id']
            else:
                left = user.id

            context['suggested_comparison_friend_id'] = left

            # album_distribution_chart = spotify_get_functions.get_album_distribution_chart(
            #     id=context['album']['uri'], user=user, left=left, right=user.id, timeframe=timeframe)

            # context['distribution_chart'] = album_distribution_chart

            return Response(context)

        else:
            return Response(['ENTER AN ID AS PARAM'])


class APIGetAlbumContainerDetail(APIView):
    permission_classes = [AllowAny]

    @method_decorator(cache_page(60*5))
    def get(self, request, format=None):

        user = self.request.user

        id = self.request.query_params.get('id', None)
        timeframe = self.request.query_params.get('timeframe', None)

        if (id):

            context = {'album_container': AlbumContainerSerializer(AlbumContainer.objects.filter(
                id=id).first()).data}

            # RETURN EARLY IN DEMO MODE
            if self.request.query_params.get('demo', None) == 'true':
                context['stream_counts'] = {
                    'total': 0,
                    'self': 0
                }
                context['suggested_comparison_friend_id'] = 1
                context['unauthorized'] = True
                return Response(context)

            streams_all = Stream.objects.active().filter(
                song__album__album_container__id=id)
            streams_timeframe = utils.set_timeframe(streams_all, timeframe)

            top_streamers = streams_timeframe.values('user__username', 'user__id').annotate(
                Count('song__album')).order_by('-song__album__count', 'user__username')

            stream_count_all = streams_timeframe.count()
            stream_count_personal = streams_timeframe.filter(user=user).count()

            context['stream_counts'] = {
                'total': stream_count_all,
                'self': stream_count_personal,
            }

            context['top_streamers'] = top_streamers.values(
                username=F('user__username'), id=F('user__id'), stream_count=F('song__album__count'))

            follows_ids = [x.follows.id for x in user.follower.all()]

            if len(top_streamers.filter(user__id__in=follows_ids)) > 0:
                left = top_streamers.filter(user__id__in=follows_ids)[
                    0]['user__id']
            else:
                left = user.id

            context['suggested_comparison_friend_id'] = left

            # album_distribution_chart = spotify_get_functions.get_album_distribution_chart(
            #     id=context['album']['uri'], user=user, left=left, right=user.id, timeframe=timeframe)

            # context['distribution_chart'] = album_distribution_chart

            return Response(context)

        else:
            return Response(['ENTER AN ID AS PARAM'])


class APIGetAlbumDetailDistribution(APIView):

    def get(self, request, format=None):

        left = self.request.query_params.get('left', None)
        right = self.request.query_params.get('right', None)

        user = self.request.user
        id = self.request.query_params.get('id', None)
        timeframe = self.request.query_params.get('timeframe', None)

        if(id):

            uri = Album.objects.get(id=id).uri

            album_stream_details = spotify_get_functions.get_album_distribution_chart(
                id=uri, user=user, left=left, right=right, timeframe=timeframe)

            context = {}
            context['distribution_chart'] = album_stream_details
            return Response(context)

        else:
            return Response(['ENTER AN ID AS PARAM'])


class APIGetAlbumContainerDetailDistribution(APIView):

    def get(self, request, format=None):

        left = self.request.query_params.get('left', None)
        right = self.request.query_params.get('right', None)

        user = self.request.user
        id = self.request.query_params.get('id', None)
        timeframe = self.request.query_params.get('timeframe', None)

        if(id):

            album_stream_details = chart_functions.get_album_container_distribution_chart(
                id=id, user=user, left=left, right=right, timeframe=timeframe)

            context = {}
            context['distribution_chart'] = album_stream_details
            return Response(context)

        else:
            return Response(['ENTER AN ID AS PARAM'])


class APIGetAlbumStreamsOverTime(APIView):

    def get(self, request, format=None):

        user = self.request.user
        group_one = self.request.query_params.get('group_one', None)
        group_two = self.request.query_params.get('group_two', None)
        timeframe = self.request.query_params.get('timeframe', None)
        id = self.request.query_params.get('id', None)

        if group_one == None:
            group_one = [user.id]
        else:
            group_one = list(map(int, group_one.split(",")))

        if group_two == None:
            streams_all = Stream.objects.active().filter(
                song__album__id=id)
            streams_timeframe = utils.set_timeframe(streams_all, timeframe)

            top_streamers = streams_timeframe.values('user__username', 'user__id').annotate(
                Count('song__artist')).order_by('-song__artist__count', 'user__username')
            follows_ids = [x.follows.id for x in user.follower.all()]

            if (top_streamers.filter(user__id__in=follows_ids).exclude(user=user).exists()):
                group_two = [top_streamers.filter(user__id__in=follows_ids).exclude(user=user)[
                    0]['user__id']]
            else:
                group_two = [user.id]
        else:
            group_two = list(map(int, group_two.split(",")))

        if(id):

            album_container = AlbumContainer.objects.get(id=id)

            album_stream_details = chart_functions.get_streams_over_time_chart_album(
                album_container=album_container, user=user, timeframe=timeframe, group_one=group_one, group_two=group_two)

            group_one_dict = {}
            group_two_dict = {}

            for member in group_one:
                group_one_dict[member] = User.objects.get(id=member).username

            for member in group_two:
                group_two_dict[member] = User.objects.get(id=member).username

            response_dict = {}
            response_dict["users"] = {
                'group_one': group_one_dict, 'group_two': group_two_dict}
            response_dict["data"] = album_stream_details

            return Response(response_dict)

        else:
            return Response(['ENTER AN ID AS PARAM'])


class APIGetPlaylists(APIView):

    def get(self, request, format=None):

        user = self.request.user

        playlists = model_functions.get_database_playlists(
            user)

        queryset = {}
        queryset['by_user'] = SmallPlaylistSerializer(
            playlists['by_user'], many=True).data
        queryset['by_groups'] = SmallPlaylistSerializer(
            playlists['by_groups'], many=True).data
        queryset['by_friends'] = SmallPlaylistSerializer(
            playlists['by_friends'], many=True).data

        return Response(queryset)


class APIGetPlaylistItems(APIView):

    def get(self, request, format=None):

        id = self.request.query_params.get('id', None)
        user = self.request.user

        try:
            playlist = Playlist.objects.get(playlist_id=id)
            playlist_type = 'individual'
        except ObjectDoesNotExist:
            playlist = GroupPlaylist.objects.get(playlist_id=id)
            playlist_type = 'group'

        model_functions.refresh_playlist_info(user, playlist)

        if playlist_type == 'individual':
            context = PlaylistSerializer(playlist).data
        else:
            context = GroupPlaylistSerializer(playlist).data

        # context = spotify_get_functions.get_playlist_tracks(
        #     user=user, uri=uri, limit=100, offset=0)

        # print(context)

        # context['image'] = spotify_playlist['images']

        return Response(context)


class APICreatePlaylist(APIView):

    def post(self, request, format=None):

        user = self.request.user

        print(request.data["update"])

        spotify_playlist = spotify_post_functions.post_user_playlist(
            user, request.data)

        extra_data = request.data.copy()
        extra_data.pop('group', None)
        extra_data.pop('name', None)
        extra_data.pop('uris', None)
        extra_data.pop('image_index', None)
        extra_data.pop('update', None)

        image_url = spotify_playlist["images"][0]["url"]

        members_list = [int(n) for n in request.data['group'].split(',')]

        members = User.objects.filter(id__in=members_list)

        Playlist.objects.create_playlist(
            name=request.data["name"], playlist_id=spotify_playlist['id'], image_640px=image_url, image_300px=image_url, image_64px=image_url, user=user, members=members, uris=request.data['uris'], update=request.data["update"], extra_data=extra_data)

        return Response(spotify_playlist)


class APIRecommendPlaylistSongs(APIView):

    def get_queryset(self):

        group = self.request.query_params.get('users', None)
        # sort = self.request.query_params.get('sort', None)
        timeframe = self.request.query_params.get('timeframe', None)
        artist_maximum = self.request.query_params.get('maximum', None)
        # popularity_range = self.request.query_params.get('popularity', None)
        genres = self.request.query_params.get('genres', None)
        release_range = self.request.query_params.get('release_range', None)
        energy_range = self.request.query_params.get('energy', None)
        valence_range = self.request.query_params.get('valence', None)
        danceability_range = self.request.query_params.get(
            'danceability', None)

        user = self.request.user

        queryset = Stream.objects.active()
        queryset = utils.set_timeframe(queryset, timeframe)

        if release_range:
            release_range = release_range.split(',')
            queryset = set_query_range(
                queryset, 'song__album__release_date', release_range[0], release_range[1])

        if energy_range:
            energy_range = energy_range.split(',')
            queryset = set_query_range(
                queryset, 'song__energy', energy_range[0], energy_range[1])

        if valence_range:
            valence_range = valence_range.split(',')
            queryset = set_query_range(
                queryset, 'song__valence', valence_range[0], valence_range[1])

        if danceability_range:
            danceability_range = danceability_range.split(',')
            queryset = set_query_range(
                queryset, 'song__danceability', danceability_range[0], danceability_range[1])

        if artist_maximum:
            artist_maximum = int(artist_maximum)
        else:
            artist_maximum = None

        if genres:
            queryset = filter_artist_genres(queryset, genres.split(","))

        if group:
            group_ids = group.split(',')
            queryset = queryset.filter(user__in=group_ids)
        else:
            group_ids = ""

        queryset = compatibility_functions.sort_by_compatibility_logarithmic_max_artists(
            queryset, group_ids, artist_maximum=artist_maximum)

        return queryset

    def get(self, request, format=None):

        songs = self.get_queryset()

        song_ids = songs.keys()
        preserved = Case(*[When(pk=pk, then=pos)
                           for pos, pk in enumerate(song_ids)])
        song_container_objects = SongContainer.objects.filter(
            id__in=song_ids).order_by(preserved)

        response = SongContainerSerializer(
            song_container_objects, many=True).data

        return Response(response)


class APINextSong(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):

        user = self.request.user

        if self.request.user.is_authenticated == False:
            user = User.objects.get(id=2)

        same_artist = self.request.query_params.get('same_artist', None)
        artist_id = self.request.query_params.get('artist_id', None)
        same_album = self.request.query_params.get('same_album', None)
        album_id = self.request.query_params.get('album_id', None)

        if same_artist == 'true':
            artist = Artist.objects.get(id=artist_id)
            songs = artist.song_set.exclude(album__id=album_id)
            count = songs.count()
            random_song = songs[randint(0, count - 1)]
            spotify_post_functions.add_to_queue(user, random_song.uri)

        elif same_album == 'true':
            album = Album.objects.get(id=album_id)
            songs = album.song_set.all()
            count = songs.count()
            random_song = songs[randint(0, count - 1)]
            spotify_post_functions.add_to_queue(user, random_song.uri)

        spotify_post_functions.next_track(user)
        time.sleep(0.25)
        user_current = Stream.objects.fetch_playing(user=user)

        if user_current is not None:
            context = SongSerializer(Song.objects.filter(
                uri=user_current['item']['uri']), many=True).data[0]
            context['user'] = UserSerializer(user).data

        return Response(context)


class APIPlaySong(APIView):
    permission_classes = [AllowAny]

    def put(self, request, format=None):

        response = None
        context_uri = request.data['context_uri']
        # n_id = ':'.join(context_uri.split(':', 2)[2:])

        first_song_uri = request.data['first_song_uri']

        offset = request.data['offset']

        user = self.request.user

        spotify_post_functions.play_track(user, context_uri, offset)

        if Song.objects.filter(uri=first_song_uri).exists():
            print('first track available!')
            first_song = SongSerializer(Song.objects.filter(
                uri=first_song_uri), many=True).data[0]

        else:
            first_song = spotify_get_functions.get_track(user, first_song_uri)
            model_functions.create_db_entries(user, first_song)
            first_song = SongSerializer(Song.objects.filter(
                uri=first_song_uri), many=True).data[0]
            print('first track not available! Creating it!')

        songs = []

        # get album tracks and serialize for queue
        if 'album' in context_uri:
            print('getting the album tracks and serializing them!')

            songs = spotify_get_functions.get_album_tracks(
                user, context_uri, limit=100, offset=offset)  # +1 cuz we play the first one

        else:
            print('getting the playlist tracks and serializing them!')

            songs = spotify_get_functions.get_playlist_tracks(
                user, context_uri, limit=100, offset=offset)  # +1 cuz we play the first one

        return Response({'song': first_song, 'queue': songs})


class APIMoodTracker(APIView):

    def get(self, request, format=None):

        user = self.request.user

        days = int(self.request.query_params.get('days', None))
        feature = self.request.query_params.get('feature', None)

        if feature == None:
            feature = 'valence'

        weeks = days//7 + 1

        week_dict = {}

        for index, week in enumerate(range(weeks)):

            week_current = datetime.datetime.now()
            week_offset = datetime.timedelta(weeks=1*index + 1)
            today = datetime.date.today()
            week_label = ((week_current - week_offset) + datetime.timedelta(
                days=-today.weekday(), weeks=1)).strftime("%b %d, %Y")

            day_dict = {}

            for index, day in enumerate(range(7)):

                day_date = ((week_current - week_offset) + datetime.timedelta(
                    days=-today.weekday() - index + 6, weeks=1)).date()
                streams = Stream.objects.active().filter(
                    user=user).filter(played_at__date=day_date)

                if len(streams) > 0:

                    score = streams.values(
                        'song__' + feature).aggregate(Avg('song__' + feature))['song__' + feature + '__avg']

                else:
                    score = 0

                day_dict[7-day] = "{:.2f}".format(score)

            week_dict[str(week_label)] = day_dict

        return Response(week_dict)


class APIUserSocialDisplays(APIView):

    def get(self, request, format=None):

        user = self.request.user
        session_id = self.request.query_params.get('id', None)

        sessions = SocialDisplaySession.objects.filter(user=user)

        if session_id != None:
            sessions = sessions.filter(id=session_id)
            response = SocialDisplaySessionSerializer(
                sessions, many=True).data[0]
        else:
            response = SocialDisplaySessionSerializer(sessions, many=True).data

        return Response(response)

    def post(self, request, format=None):

        user = self.request.user

        session = SocialDisplaySession.objects.get(id=self.request.data['id'])
        session.last_update = timezone.now()
        session.save()

        log_data = self.request.data['log_data']

        current_timestamp = timezone.now()

        response = {}

        for user_name, user_value in log_data.items():
            print(user_name, user_value)

            session_user = User.objects.get(username=user_name)

            session_user_logs = SocialDisplayUserLog.objects.filter(
                session=session).filter(user=session_user).order_by('-timestamp')

            if session_user_logs.count() == 0:
                print('first user log!')
                SocialDisplayUserLog.objects.create(user=session_user, session=session, compatibility=0,
                                                    session_affinity=0, cumulative_user_session_time=0, time_delta=0, valid_update=False)
            elif session_user_logs.count() > 0:
                print('creating new log!')
                previous_log = session_user_logs.values()[0]

                # calculate the timedelta and see if it is valid
                time_delta = (timezone.now() -
                              previous_log['timestamp']).total_seconds()


                new_affinity = 0 


                if (time_delta < 20):
                    print('valid update!')

                    cum_sum = previous_log['cumulative_user_session_time'] + time_delta

                    new_affinity = (user_value * time_delta + previous_log['session_affinity'] *
                                    previous_log['cumulative_user_session_time']) / cum_sum

                    print(new_affinity)

                    SocialDisplayUserLog.objects.create(user=session_user, session=session, compatibility=user_value,
                                                        session_affinity=new_affinity, cumulative_user_session_time=cum_sum, time_delta=time_delta, valid_update=True)

                else:
                    print('invalid update!')
                    SocialDisplayUserLog.objects.create(user=session_user, session=session, compatibility=user_value,
                                                        session_affinity=previous_log['session_affinity'], cumulative_user_session_time=previous_log['cumulative_user_session_time'], time_delta=time_delta, valid_update=False)

            response[user_name] = {
                'session_affinity': new_affinity, 'compatibility': user_value}

        return Response(response)


# -=-=-=-=-= FILTER FUNCTIONS FOR QUERYSET -=-=-=-=-=
def filter_artist_genres(queryset, genre_containers):

    if genre_containers == ['all']:
        return queryset


    if genre_containers != ['']:
        
        
        allowed_artists = []
        
        for genre_container in genre_containers:

            genre_container_object = GenreContainer.objects.get(name=genre_container)

            print(genre_container_object.subgenres)


            subgenres = genre_container_object.subgenres.all()

            print(subgenres)

            for subgenre in subgenres:
                allowed_artists = set().union(allowed_artists, Genre.objects.get(name = subgenre).artist_set.all())

        queryset = queryset.filter(song__artist__in=allowed_artists)

    return queryset


def set_offset(queryset, offset):
    if offset != 0 and offset != None:
        queryset = queryset[int(offset):]
    return queryset


def set_limit(queryset, limit):
    if limit is not None:
        queryset = queryset[:int(limit)]
    else:
        queryset = queryset[:100]

    return queryset


def set_query_range(queryset, keyword, lower_bound, upper_bound):

    filter = {}
    filter[str(keyword) + '__gte'] = lower_bound
    filter[str(keyword) + '__lte'] = upper_bound

    queryset = queryset.filter(**filter)

    return queryset


def convert_query_params_to_hashed_cache_key(user, cache_type, query_params, params_to_exclude):

    query_key = dict(query_params)

    for param in params_to_exclude:
        del query_key[param]

    sorted_query_key = {key: value for key, value in sorted(
        query_key.items()) if value != ['']}
    hashed_query_key = hash(str(sorted_query_key))

    return ('user{}:{}:{}').format(user.id, cache_type, hashed_query_key)
