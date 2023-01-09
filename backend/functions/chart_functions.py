import dis
from math import fabs
import math
from django.db.models.aggregates import Count
from django.db.models import Q, F, Value, Case, When, Max, IntegerField
from ..serializers import AlbumContainerSerializer, SongContainerSerializer
from dateutil.relativedelta import *
from django.db.models.functions import Trunc
from .. import models
from . import utils, authorization_functions
import spotipy
import operator
from collections import OrderedDict
import datetime


def get_album_container_distribution_chart(id, user, left, right, timeframe):

    # albums = get_artist_albums(id, user)

    chart_data = []
    biggest_left = 0
    biggest_right = 0

    song_containers = models.AlbumContainer.objects.get(
        id=id).songcontainer_set.all()
    # print(album_containers.annotate(left=Count('album__song__stream'), right=Count('album__song__stream')).values('left', 'right'))

    distribution_data = song_containers.annotate(
        left=Count('song__stream', filter=(Q(
            song__stream__user__id=left) & Q(
            song__stream__active=True))),
        right=Count('song__stream', filter=(Q(
            song__stream__user__id=right) & Q(
            song__stream__active=True))),
    ).order_by('-bonus', '-disc_number', '-track_number')

    distribution_chart_dict = {}
    distribution_chart_dict = {}
    distribution_chart_dict['users'] = {'left': left, 'right': right}
    distribution_chart_dict['data'] = []

    biggest_right = distribution_data.aggregate(Max('right'))['right__max']
    biggest_left = distribution_data.aggregate(Max('left'))['left__max']

    if biggest_right == None:
        biggest_right = 0

    if biggest_left == None:
        biggest_left = 0

    distribution_chart_dict['biggest_values'] = {
        "all": max(biggest_left, biggest_right),
        "left": biggest_left,
        "right": biggest_right
    }

    for container in distribution_data:

        song_object = SongContainerSerializer(
            container).data
        song_object['streams'] = {
            'left': container.left, 'right': container.right}

        distribution_chart_dict['data'].insert(0, song_object)

    return distribution_chart_dict


def get_artist_distribution_chart(uri, user, left, right, timeframe):

    # albums = get_artist_albums(id, user)

    chart_data = []
    biggest_left = 0
    biggest_right = 0

    album_containers = models.Artist.objects.get(
        uri=uri).albumcontainer_set.filter(album_type='album')
    # print(album_containers.annotate(left=Count('album__song__stream'), right=Count('album__song__stream')).values('left', 'right'))

    distribution_data = album_containers.annotate(
        left=Count('album__song__stream', filter=(Q(
            album__song__stream__user__id=left) & Q(
            album__song__stream__active=True))),
        right=Count('album__song__stream', filter=(Q(
            album__song__stream__user__id=right) & Q(
            album__song__stream__active=True))),
    )

    distribution_chart_dict = {}
    distribution_chart_dict = {}
    distribution_chart_dict['users'] = {'left': left, 'right': right}
    distribution_chart_dict['data'] = []

    biggest_right = distribution_data.aggregate(Max('right'))['right__max']
    biggest_left = distribution_data.aggregate(Max('left'))['left__max']

    if biggest_right == None:
        biggest_right = 0

    if biggest_left == None:
        biggest_left = 0

    distribution_chart_dict['biggest_values'] = {
        "all": max(biggest_left, biggest_right),
        "left": biggest_left,
        "right": biggest_right
    }



    for container in distribution_data.order_by('master_child_album__release_date'):

        album_object = AlbumContainerSerializer(
            container).data
        album_object['streams'] = {
            'left': container.left, 'right': container.right}

        distribution_chart_dict['data'].insert(0, album_object)

    return distribution_chart_dict

def get_streams_over_time_chart_album(album_container, user, timeframe, group_one, group_two, detailed_date=False):

    response = {}

    # get the active streams for group one and two
    album_streams = models.Stream.objects.active().filter(
        song__song_container__album_container=album_container)

    if timeframe == 'weekly':
        strftime_string = '%a'  # Weekday as locale’s abbreviated name.
        stepsize = "day"
        timedelta = 7
        threshold_date = datetime.datetime.now(
            datetime.timezone.utc) - datetime.timedelta(days=timedelta)
        songs_streams_in_timeframe = album_streams.filter(played_at__gte=threshold_date).annotate(timeframe=Trunc(
            'played_at', stepsize)).values('timeframe')
    elif timeframe == 'monthly':
        strftime_string = '%d'  # Weekday as locale’s abbreviated name.
        stepsize = "day"
        timedelta = 31
        threshold_date = datetime.datetime.now(
            datetime.timezone.utc) - datetime.timedelta(days=timedelta)
        songs_streams_in_timeframe = album_streams.filter(played_at__gte=threshold_date).annotate(timeframe=Trunc(
            'played_at', stepsize)).values('timeframe')
    elif timeframe == 'quarterly':
        strftime_string = '%d'  # Weekday as locale’s abbreviated name.
        stepsize = "day"
        timedelta = 92
        threshold_date = datetime.datetime.now(
            datetime.timezone.utc) - datetime.timedelta(days=timedelta)
        songs_streams_in_timeframe = album_streams.filter(played_at__gte=threshold_date).annotate(timeframe=Trunc(
            'played_at', stepsize)).values('timeframe')
    else:
        strftime_string = '%b'  # Month as locale’s abbreviated name..
        stepsize = "month"
        songs_streams_in_timeframe = album_streams.annotate(timeframe=Trunc(
            'played_at', stepsize)).values('timeframe')
        if len(songs_streams_in_timeframe) > 0:
            threshold_date = songs_streams_in_timeframe[0]["timeframe"]
        else:
            threshold_date = datetime.datetime.now(datetime.timezone.utc)

        timedelta = math.ceil((datetime.datetime.now(
            datetime.timezone.utc) - threshold_date).days / 31) - 1

    # count group stream occurences in timeframe
    songs_streams_in_timeframe = songs_streams_in_timeframe.annotate(
        group_one=Count(Case(When(user_id__in=group_one, then=1), output_field=IntegerField()))).annotate(
        group_two=Count(Case(When(user_id__in=group_two, then=1), output_field=IntegerField())))

    for timeframe in songs_streams_in_timeframe:
        temp_dict = {
            "name": timeframe['timeframe'].isoformat(),
            "streams": {
                "group_one": timeframe['group_one'],
                "group_two": timeframe['group_two']
            }
        }
        response[str(timeframe['timeframe'].isoformat())] = temp_dict

    return OrderedDict(sorted(response.items()))


def get_streams_over_time_chart_artist(artist, user, timeframe, group_one, group_two):

    response = {}

    if timeframe == 'weekly':
        strftime_string = '%a'  # Weekday as locale’s abbreviated name.
        stepsize = "day"
        timedelta = 7
        threshold_date = datetime.datetime.now(
            datetime.timezone.utc) - datetime.timedelta(days=timedelta)
        songs_streams_in_timeframe = models.Stream.objects.active().filter(song__artist=artist).filter(played_at__gte=threshold_date).annotate(timeframe=Trunc(
            'played_at', stepsize)).values('timeframe')
    elif timeframe == 'monthly':
        strftime_string = '%d'  # Weekday as locale’s abbreviated name.
        stepsize = "day"
        timedelta = 31
        threshold_date = datetime.datetime.now(
            datetime.timezone.utc) - datetime.timedelta(days=timedelta)
        songs_streams_in_timeframe = models.Stream.objects.active().filter(song__artist=artist).filter(played_at__gte=threshold_date).annotate(timeframe=Trunc(
            'played_at', stepsize)).values('timeframe')
    elif timeframe == 'quarterly':
        strftime_string = '%d'  # Weekday as locale’s abbreviated name.
        stepsize = "day"
        timedelta = 92
        threshold_date = datetime.datetime.now(
            datetime.timezone.utc) - datetime.timedelta(days=timedelta)
        songs_streams_in_timeframe = models.Stream.objects.active().filter(song__artist=artist).filter(played_at__gte=threshold_date).annotate(timeframe=Trunc(
            'played_at', stepsize)).values('timeframe')
    else:
        strftime_string = '%b'  # Month as locale’s abbreviated name..
        stepsize = "month"
        songs_streams_in_timeframe = models.Stream.objects.active().filter(song__artist=artist).filter(played_at__gte=datetime.datetime(1970, 1, 1)).annotate(timeframe=Trunc(
            'played_at', stepsize)).values('timeframe')

        if len(songs_streams_in_timeframe) > 0:
            threshold_date = songs_streams_in_timeframe[0]["timeframe"]
        else:
            threshold_date = datetime.datetime.now(datetime.timezone.utc)

        timedelta = math.ceil((datetime.datetime.now(
            datetime.timezone.utc) - threshold_date).days / 31) - 1

    # count group stream occurences in timeframe
    songs_streams_in_timeframe = songs_streams_in_timeframe.annotate(
        group_one=Count(Case(When(user_id__in=group_one, then=1), output_field=IntegerField()))).annotate(
        group_two=Count(Case(When(user_id__in=group_two, then=1), output_field=IntegerField())))

    for timeframe in songs_streams_in_timeframe:
        temp_dict = {
            "name": timeframe['timeframe'].isoformat(),
            "streams": {
                "group_one": timeframe['group_one'],
                "group_two": timeframe['group_two']
            }
        }
        response[str(timeframe['timeframe'].isoformat())] = temp_dict

    response = OrderedDict(sorted(response.items()))
    return response
