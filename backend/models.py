from doctest import master
from django.db import models
from .functions import authorization_functions, color_functions, model_functions, spotify_get_functions, image_functions, object_container_functions
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import dateutil.parser
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
import logging
import requests
import spotipy
import spotipy.util as util
from spotipy import oauth2
import time
import threading
import datetime
import hashlib, base64


logger = logging.getLogger(__name__)






class Genre(models.Model):
    name = models.CharField(max_length=64, default=None, unique=True)

    def __str__(self):
        return self.name

class GenreContainer(models.Model):
    name = models.CharField(max_length=64, default=None, unique=True)
    subgenres = models.ManyToManyField(Genre)

    def __str__(self):
        return self.name


class ImageManager(models.Manager):
    def create_image(self, px640, px300, px64, primary_color):
        image = self.create(px640=px640, px300=px300,
                            px64=px64, primary_color=primary_color)

        return image


class Image(models.Model):
    px640 = models.URLField(max_length=400)
    px300 = models.URLField(max_length=400)
    px64 = models.URLField(max_length=400)
    primary_color = models.CharField(max_length=15, default=None, null=True)

    objects = ImageManager()


class ProfileManager(models.Manager):

    def create_profile(self, user):
        
        try:
            image = image_functions.create_or_refresh_profile_image_object(user)
        except:
            image = None

        profile = self.create(user=user, last_request=timezone.now, image=image )
        return profile


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_request = models.DateTimeField(auto_now_add=True)
    image = models.ForeignKey(Image, default=None, blank=True, null=True, on_delete=models.SET_NULL)
    banner_image = models.URLField(blank=True, null=True)
    search_history = models.TextField(default='[]')
    objects = ProfileManager()

    def __str__(self):
        return self.user.username


def group_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_files/user_<id>/<filename>
    return 'group_files/group_{0}/images/{1}'.format(instance.id, filename)


class Group(models.Model):
    name = models.CharField(max_length=64)
    identifier = models.CharField(max_length=32, unique=True)
    owner = models.ForeignKey(User, default=None, blank=True, null=True, on_delete=models.SET_DEFAULT)
    image = models.FileField(upload_to=group_directory_path, default=None, blank=True, null=True)
    private = models.BooleanField(default=False)

    def __str__(self):
        return self.identifier


class GroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'group'], name='Can not join the same group twice')
        ]

class UserFollow(models.Model):
    user = models.ForeignKey(
        User, related_name="follower", on_delete=models.CASCADE)
    follows = models.ForeignKey(
        User, related_name="follows", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'follows'], name='Can not follow user twice')
        ]


class ArtistManager(models.Manager):
    def create_artist(self, name, uri, genres, image_640px, image_300px, image_64px):

        primary_color = None
        image = Image.objects.create_image(
            image_640px, image_300px, image_64px, primary_color)

        artist = self.create(name=name, uri=uri, image=image)
        print('genres: ' + str(genres))
        artist.genre.add(*Genre.objects.filter(name__in=genres))

        return artist


class Artist(models.Model):
    name = models.CharField(max_length=255)
    uri = models.CharField(max_length=100, unique=True)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    genre = models.ManyToManyField(Genre)

    objects = ArtistManager()

    def __str__(self):
        return self.name






class AlbumManager(models.Manager):
    def create_album(self, name, uri, artist, image_640px, image_300px, image_64px, release_date, album_type):

        primary_color = None
        image = Image.objects.create_image(
            image_640px, image_300px, image_64px, primary_color)

        album_container = object_container_functions.find_container_for_album(name, release_date, artist)


        album = self.create(name=name, uri=uri, artist=artist,
                            image=image, release_date=release_date, album_type=album_type, album_container=album_container)

        return album


ALBUM_TYPE_CHOICES = (
    ('album', 'album'),
    ('single', 'single'),
    ('appears_on', 'appears_on'),
    ('compilation', 'compilation'),
    ('unknown', 'unknown'),
)


class Album(models.Model):
    name = models.CharField(max_length=255)
    uri = models.CharField(max_length=100, unique=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, default=None, blank=True, null=True, on_delete=models.SET_NULL)
    release_date = models.IntegerField(default=None, blank=True, null=True)
    album_type = models.CharField(max_length=100, default='unknown', choices=ALBUM_TYPE_CHOICES)
    album_container = models.ForeignKey('AlbumContainer', default=None, null=True, blank=True, on_delete=models.SET_NULL)
    objects = AlbumManager()

    def __str__(self):
        return self.name


class AlbumContainerManager(models.Manager):
    def create_album_container(self, name, identifier, master_child_album):

        albumContainer = self.create(name=name, identifier=identifier, artist=master_child_album.artist,
                            master_child_album=master_child_album, album_type=master_child_album.album_type)

        return albumContainer

class AlbumContainer(models.Model):
    name = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    album_type = models.CharField(max_length=100, default='unknown', choices=ALBUM_TYPE_CHOICES)
    master_child_album = models.ForeignKey(Album, on_delete=models.PROTECT)
    objects = AlbumContainerManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['album_type', 'artist', 'identifier'], name='Artist can not have the same identifier twice')
        ]


    def __str__(self):
        return self.name


class SongManager(models.Manager):
    def create_song(self, name,  uri, artist, album):

        user = User.objects.get(username="MatsErdkamp")
        token = authorization_functions.get_token(user)
        sp = spotipy.Spotify(auth=token)
        audio_features = sp.audio_features(tracks=[uri])[0]

        if audio_features != None:
            energy = audio_features['energy']
            valence = audio_features['valence']
            danceability = audio_features['danceability']
        else:
            energy = 0.50001
            valence = 0.50001
            danceability = 0.50001

        song = self.create(name=name, uri=uri, artist=artist, album=album,
                           energy=energy, valence=valence, danceability=danceability)


        # object_container_functions.redo_all_containers_for_artist(artist)
        object_container_functions.find_container_for_song(song, album)

        return song


class Song(models.Model):
    name = models.CharField(max_length=500)
    uri = models.CharField(max_length=100, unique=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    song_container = models.ForeignKey('SongContainer', default=None, null=True, blank=True, on_delete=models.SET_NULL)
    energy = models.FloatField(default=0)
    valence = models.FloatField(default=0)
    danceability = models.FloatField(default=0)

    objects = SongManager()

    def __str__(self):
        return self.name


class SongContainerManager(models.Manager):
    def create_song_container(self, name, identifier, track_number, disc_number, bonus, artist_uri, album_container, master_child_song):

        try:
            artist = Artist.objects.get(uri=artist_uri)
        except:
            print('NEED TO CREATE ARTIST: {}'.format(artist_uri))
            user = User.objects.get(username='MatsErdkamp')
            token = authorization_functions.get_token(user)
            sp = spotipy.Spotify(auth=token)
            fetchArtist = sp.artist(artist_id=artist_uri)
            try:
                artist = Artist.objects.create_artist(
                    fetchArtist['name'],
                    fetchArtist["uri"],
                    fetchArtist["genres"],
                    fetchArtist["images"][0]["url"],
                    fetchArtist["images"][1]["url"],
                    fetchArtist["images"][2]["url"]
                )
            except:  # if artist has no image
                artist = Artist.objects.create_artist(
                    fetchArtist['name'],
                    fetchArtist["uri"],
                    fetchArtist["genres"],
                    '#',
                    '#',
                    '#'
                )

        uri_string = artist.uri+identifier+str(track_number)+str(disc_number)
        uri = hashlib.md5(uri_string.encode('utf-8')).hexdigest()[:12]

        song_container = self.create(name=name, identifier=identifier, uri=uri, track_number=track_number, disc_number=disc_number, bonus=bonus, artist=artist,
                            album_container=album_container, master_child_song=master_child_song)

        return song_container

class SongContainer(models.Model):
    name = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255)
    uri = models.CharField(max_length=64, default='?')
    track_number = models.IntegerField(default=0)
    disc_number = models.IntegerField(default=0)
    bonus = models.BooleanField(default=False)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    album_container = models.ForeignKey(AlbumContainer, on_delete=models.CASCADE)
    master_child_song = models.ForeignKey(Song, on_delete=models.PROTECT, default=None, null=True, blank=True)
    objects = SongContainerManager()

    def __str__(self):
        return self.name


class StreamManager(models.Manager):

    def active(self):
        return self.filter(active=True)

    def create_stream(self, song, user, played_at, imported=False):
        stream = self.create(
            song=song, user=user, played_at=played_at, imported=imported)

        #INVALIDATE THE USER CACHES
        UserCacheObject.objects.filter(user=user).delete()

        return stream

    def generate_stream_data(self, user, track):

        model_functions.create_db_entries(user, track)


    def fetch_playing(self, user):

        token = authorization_functions.get_token(user)

        sp = spotipy.Spotify(auth=token)

        try:
            playing = sp.current_playback(market=None)
        except requests.exceptions.Timeout:
            return None


        # check also serves to see if we are streaming at all
        if bool(playing) and playing['item'] != None and playing['item']['is_local'] == False:

            if Song.objects.filter(uri=playing['item']['uri']).exists() == False:

                Stream.objects.generate_stream_data(
                    user, playing['item'])  # IMPORTANT (FUNNEL CHECK)

            return playing
        else:
            return None

    def fetch_streams(self, user):

        if user.is_authenticated:

            if Profile.objects.filter(user=user).exists():
                Profile.objects.filter(user=user).update(
                    last_request=timezone.now())
            else:
                Profile.objects.create_profile(user)

            token = authorization_functions.get_token(user)

            sp = spotipy.Spotify(auth=token)

            lastUserStream = Stream.objects.filter(  # get the latest entry by user
                user_id=user.id).order_by('-played_at').first()

            # if there is a last entry, only add songs after that one

            last_played_uri = ''

            if lastUserStream:
                last_played_at = lastUserStream.played_at
                last_played_uri = lastUserStream.song.uri
                results = sp.current_user_recently_played(
                    after=str(int(last_played_at.timestamp())*1000+1000))
                # TIMESTAMP IN UTC MILLISECONDS

             # if there is no latest entry, add all recently played tracks
            else:
                results = sp.current_user_recently_played()
                last_played_at = None

            uris = []
            played_at = []

            if results['items']:

                for item in reversed(results['items']):
                    track = item['track']
                    uris.append(track['uri'])
                    played_at.append(item['played_at'])

                # fetch several tracks with recent track uris
                fetchTrack = sp.tracks(uris, market=None)

                for index, track in enumerate(fetchTrack['tracks']):

                    track['played_at'] = played_at[index]

                    if Song.objects.filter(uri=track['uri']).exists() == False:
                        Stream.objects.generate_stream_data(
                            user, track)  # IMPORTANT (FUNNEL CHECK)

                    # extra check to see if we already have the stream

                    if (last_played_at):
                        delta = dateutil.parser.isoparse(track['played_at']).timestamp(
                        ) - dateutil.parser.isoparse(str(last_played_at)).timestamp()
                    else:
                        delta = 3600

                    if last_played_uri != '':
                        if last_played_uri == track['uri']:
                            if delta * 10000 > track['duration_ms']:
                                logger.error(
                                    'Same song streamed again! (same song new stream)')
                                Stream.objects.create_stream(  # Create the stream (song + user who played it)
                                    Song.objects.get(uri=track['uri']),
                                    user,
                                    track['played_at'])
                            else:
                                logger.error(
                                    "Same song streamed again. Too soon!")

                        else:
                            logger.error(
                                'stream does not exist yet!!! (new song)')
                            Stream.objects.create_stream(  # Create the stream (song + user who played it)
                                Song.objects.get(uri=track['uri']),
                                user,
                                track['played_at'])
                    else:
                        logger.error('stream does not exist yet!')
                        Stream.objects.create_stream(  # Create the stream (song + user who played it)
                            Song.objects.get(uri=track['uri']),
                            user,
                            track['played_at'])

                    last_played_at = track['played_at']

                    last_played_uri = track['uri']





class Stream(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    played_at = models.DateTimeField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    imported = models.BooleanField(default=False)
    active = models.BooleanField(default=True)


    objects = StreamManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['song', 'user', 'played_at', 'imported'], name='Can not stream the same song twice in the same moment (unless one is imported)')
        ]

    def __str__(self):
        return self.song.name


class PlaylistManager(models.Manager):
    def create_playlist(self, name, playlist_id, image_640px, image_300px, image_64px, uris, user, members, update, extra_data):

        primary_color = None
        image = Image.objects.create_image(
            image_640px, image_300px, image_64px, primary_color)

        playlist = self.create(
            name=name, user=user, playlist_id=playlist_id, image=image, update=update, extra_data=extra_data)

        playlist.members.add(*members)

        for index, uri in enumerate(uris):

            change_amount = None
            change_trend = 'new'

            song = Song.objects.get(uri=uri)

            ranking = Ranking(song=song, playlist=playlist, ranking_position=index+1,
                              ranking_change_trend=change_trend, ranking_change_amount=change_amount)
            ranking.save()

        playlist.save()

        return playlist


class Playlist(models.Model):
    name = models.TextField()
    playlist_id = models.TextField()
    image = models.ForeignKey(Image, default=None, blank=True, null=True, on_delete=models.SET_NULL)
    songs = models.ManyToManyField(Song, through='Ranking')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='playlist_as_member')
    update = models.BooleanField()
    new_entries_amount = models.IntegerField(default=0)
    last_update = models.DateTimeField(auto_now_add=True)
    extra_data = models.TextField(default='{}')

    objects = PlaylistManager()



class GroupPlaylistManager(models.Manager):
    def create_playlist(self, name, playlist_id, image_640px, image_300px, image_64px, uris, user, group, update, extra_data):

        primary_color = None
        image = Image.objects.create_image(
            image_640px, image_300px, image_64px, primary_color)

        playlist = self.create(
            name=name, user=user, group=group, playlist_id=playlist_id, image=image, update=update, extra_data=extra_data)


        for index, uri in enumerate(uris):

            change_amount = None
            change_trend = 'new'

            song = Song.objects.get(uri=uri)

            ranking = Ranking(song=song, playlist=playlist, ranking_position=index+1,
                              ranking_change_trend=change_trend, ranking_change_amount=change_amount)
            ranking.save()

        playlist.save()

        return playlist



SORT_CHOICES = (
    ('streams', 'streams'),
    ('compatibility', 'compatibility'),
)


class GroupPlaylist(models.Model):
    name = models.TextField()
    playlist_id = models.TextField()
    image = models.ForeignKey(Image, default=None, blank=True, null=True, on_delete=models.SET_NULL)
    sort_mode = models.CharField(max_length=32, default='streams', choices=SORT_CHOICES)
    songs = models.ManyToManyField(Song, through='GroupRanking')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    update = models.BooleanField()
    new_entries_amount = models.IntegerField(default=0)
    last_update = models.DateTimeField(auto_now_add=True)
    extra_data = models.TextField(default='{}')

    objects = PlaylistManager()


class RecommendationPlaylistManager(models.Manager):
    def create_recommendation_playlist(self, name, playlist_id, image_640px, image_300px, image_64px, songs, user, update):

        primary_color = None
        image = Image.objects.create_image(
            image_640px, image_300px, image_64px, primary_color)

        playlist = self.create(
            name=name, user=user, playlist_id=playlist_id, image=image, update=update)

        
        playlist.songs.add(*songs)

        playlist.save()

        return playlist


class RecommendationPlaylist(models.Model):
    name = models.TextField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    playlist_id = models.TextField()
    image = models.ForeignKey(Image, default=None, blank=True, null=True, on_delete=models.SET_NULL)
    songs = models.ManyToManyField(Song)
    update = models.BooleanField(default=True)
    last_update = models.DateTimeField(auto_now_add=True)

    objects = RecommendationPlaylistManager()


TREND_CHOICES = (
    ('up', 'up'),
    ('down', 'down'),
    ('new', 'new'),
    ('constant', 'constant'),
)


class Ranking(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    ranking_position = models.IntegerField()
    ranking_change_trend = models.CharField(
        max_length=32, default='new', choices=TREND_CHOICES)
    ranking_change_amount = models.IntegerField(
        null=True, blank=True, default=None)
    compatibility = models.FloatField(default=0)

    class Meta:
        ordering = ['ranking_position']

class GroupRanking(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    playlist = models.ForeignKey(GroupPlaylist, on_delete=models.CASCADE)
    ranking_position = models.IntegerField()
    ranking_change_trend = models.CharField(
        max_length=32, default='new', choices=TREND_CHOICES)
    ranking_change_amount = models.IntegerField(
        null=True, blank=True, default=None)
    compatibility = models.FloatField(default=0)

    class Meta:
        ordering = ['ranking_position']


class Recommendation(models.Model):
    user_from = models.ForeignKey(User, default=None, blank=True, null=True, on_delete=models.SET_NULL, related_name='recommendation_sender')
    user_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_receiver')
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=120, default='')

    class Meta:
        abstract = True



class SongRecommendation(Recommendation):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user_from', 'user_to', 'song'], name='Can not recommend a user the same song twice')
        ]

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_files/user_<id>/<filename>
    return 'user_files/user_{0}/endsong_files/{1}'.format(instance.user.id, filename)


AVAILABILITY_CHOICES = (
    ('unverified', 'unverified'),
    ('available', 'available'),
    ('processing', 'processing'),
    ('error', 'error'),
)

class EndsongFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path)
    cleaned = models.BooleanField(default=False)
    import_completed = models.BooleanField(default=False)
    uris_available_in_database = models.CharField(default='unverified', max_length=24, choices=AVAILABILITY_CHOICES)
    upload_timestamp = models.DateTimeField(auto_now_add=True)


class SocialDisplaySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_start = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now_add=True)


class SocialDisplayUserLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(SocialDisplaySession, on_delete=models.CASCADE)
    compatibility = models.FloatField()
    session_affinity = models.FloatField()
    cumulative_user_session_time = models.FloatField()
    time_delta = models.FloatField()
    valid_update = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)




# CACHING LOGIC -------------

CACHE_TYPE_CHOICES = (
    ('songs', 'songs'),
    ('artists', 'artists'),
    ('albums', 'albums'),
)

CACHE_SORT_CHOICES = (
    ('streams', 'streams'),
    ('compatibility', 'compatibility'),
)

TIMEFRAME_CHOICES = (
    ('weekly', 'weekly'),
    ('monthly', 'monthly'),
    ('quarterly', 'quarterly'),
    ('yearly', 'yearly'),
    ('all-time', 'all-time'),
    ('YTD', 'YTD'),
)


class UserCacheObject(models.Model):
    
    key = models.CharField(max_length=128, default=None, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cache_type = models.CharField(max_length=16, default='undefined', choices=CACHE_TYPE_CHOICES)
    sort_mode = models.CharField(max_length=16, default='undefined', choices=CACHE_SORT_CHOICES)
    timeframe = models.CharField(max_length=16, default='undefined', choices=TIMEFRAME_CHOICES)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.key

class GroupCacheObject(models.Model):
    
    key = models.CharField(max_length=128, default=None, unique=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    cache_type = models.CharField(max_length=16, default='undefined', choices=CACHE_TYPE_CHOICES)
    sort_mode = models.CharField(max_length=16, default='undefined', choices=CACHE_SORT_CHOICES)
    timeframe = models.CharField(max_length=16, default='undefined', choices=TIMEFRAME_CHOICES)
    valid_subcaches = models.ManyToManyField(UserCacheObject)
    invalidated_subcache_percentage = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.key


# END OF CACHING LOGIC ------