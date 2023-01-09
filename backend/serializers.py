from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User


class GenreSerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        return value.name

    class Meta:
        model = Genre


class ImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Image
        fields = '__all__'


class ArtistSerializer(serializers.ModelSerializer):

    image = ImageSerializer()
    genre = GenreSerializer(many=True)

    class Meta:
        model = Artist
        fields = '__all__'


class SmallArtistSerializer(serializers.ModelSerializer):

    class Meta:
        model = Artist
        fields = fields = ('id', 'name')


class AlbumSerializer(serializers.ModelSerializer):

    artist = ArtistSerializer()
    image = ImageSerializer()

    class Meta:
        model = Album
        fields = ('id', 'name', 'uri', 'artist', 'image', 'album_container')


class AlbumContainerSerializer(serializers.ModelSerializer):

    artist = ArtistSerializer()
    master_child_album = AlbumSerializer()

    class Meta:
        model = AlbumContainer
        fields = ('id', 'name', 'identifier', 'album_type',
                  'artist', 'master_child_album')


class SmallAlbumSerializer(serializers.ModelSerializer):

    image = ImageSerializer()

    class Meta:
        model = Album
        fields = ('id', 'name', 'uri', 'image', 'album_container')


class MediumAlbumContainerSerializer(serializers.ModelSerializer):

    artist = SmallArtistSerializer()
    master_child_album = SmallAlbumSerializer()

    class Meta:
        model = AlbumContainer
        fields = ('id', 'name', 'identifier', 'album_type',
                  'artist', 'master_child_album')



class SmallAlbumContainerSerializer(serializers.ModelSerializer):

    master_child_album = SmallAlbumSerializer()

    class Meta:
        model = AlbumContainer
        fields = ('id', 'name', 'master_child_album')


class SongSerializer(serializers.ModelSerializer):

    artist = ArtistSerializer()
    album = AlbumSerializer()

    class Meta:
        model = Song
        fields = ('id', 'name', 'uri', 'artist', 'album', 'song_container',
                  'energy', 'danceability', 'valence')


class SmallSongSerializer(serializers.ModelSerializer):

    artist = SmallArtistSerializer()
    album = SmallAlbumSerializer()

    class Meta:
        model = Song
        fields = ('id', 'name', 'uri', 'artist', 'album', 'song_container')


class SongContainerSerializer(serializers.ModelSerializer):

    artist = ArtistSerializer()
    master_child_song = SongSerializer()
    album_container = AlbumContainerSerializer()

    class Meta:
        model = SongContainer
        fields = ('id', 'name', 'identifier', 'artist', 'track_number',
                  'bonus', 'album_container', 'master_child_song')


class ListSongContainerSerializer(serializers.ModelSerializer):

    artist = SmallArtistSerializer()
    album_container = AlbumContainerSerializer()

    class Meta:
        model = SongContainer
        fields = ('id', 'name', 'identifier', 'artist',
                  'album_container', 'master_child_song')


class MediumSongContainerSerializer(serializers.ModelSerializer):

    artist = SmallArtistSerializer()
    album_container = SmallAlbumContainerSerializer()

    class Meta:
        model = SongContainer
        fields = ('id', 'name', 'identifier', 'artist', 'track_number',
                  'bonus', 'album_container', 'master_child_song')



class SmallSongContainerSerializer(serializers.ModelSerializer):

    artist = SmallArtistSerializer()

    class Meta:
        model = SongContainer
        fields = ('id', 'name', 'identifier', 'artist',
                  'track_number', 'bonus', 'master_child_song')





class MyModelIdSerializer(serializers.Serializer):

    SongContainer = serializers.PrimaryKeyRelatedField(
        many=True, queryset=SongContainer.objects.all())


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')


class ProfileSerializer(serializers.ModelSerializer):

    user = UserSerializer()
    image = ImageSerializer()

    class Meta:
        model = Profile
        fields = ('image', 'user', 'banner_image')
        extra_kwargs = {'image': {'required': False},
                        'banner_image': {'required': False}}


class GroupMembershipSerializer(serializers.ModelSerializer):

    profile = ProfileSerializer(source='user.profile')

    class Meta:
        model = GroupMembership
        fields = ('profile', 'is_admin')


class SmallGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ('id', 'identifier', 'name')


class GroupSerializer(serializers.ModelSerializer):

    owner = ProfileSerializer(source='owner.profile')
    members = GroupMembershipSerializer(
        source='groupmembership_set', many=True)

    class Meta:
        model = Group
        fields = ('id', 'identifier', 'name', 'owner', 'image', 'members')
        extra_kwargs = {'image': {'required': False}}


class StreamSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    song = SmallSongSerializer()

    class Meta:
        model = Stream
        fields = ('id', 'song', 'user', 'played_at')


class RankingSerializer(serializers.ModelSerializer):

    song = SmallSongSerializer()

    class Meta:
        model = Ranking
        fields = ('ranking_position', 'ranking_change_trend',
                  'ranking_change_amount', 'compatibility', 'song')


class SmallPlaylistSerializer(serializers.ModelSerializer):

    user = UserSerializer()
    image = ImageSerializer()

    class Meta:
        model = Playlist
        fields = ('name', 'playlist_id', 'user', 'new_entries_amount', 'image')


class PlaylistSerializer(serializers.ModelSerializer):

    user = UserSerializer()
    songs = RankingSerializer(source='ranking_set', many=True)

    image = ImageSerializer()

    class Meta:
        model = Playlist
        fields = ('name', 'playlist_id', 'user', 'image', 'songs')


class GroupPlaylistSerializer(serializers.ModelSerializer):

    songs = RankingSerializer(source='groupranking_set', many=True)

    image = ImageSerializer()

    class Meta:
        model = GroupPlaylist
        fields = ('name', 'playlist_id', 'group', 'image', 'songs')


class SmallGroupPlaylistSerializer(serializers.ModelSerializer):

    image = ImageSerializer()

    class Meta:
        model = GroupPlaylist
        fields = ('name', 'playlist_id', 'group',
                  'new_entries_amount', 'image')


class SongRecommendationSerializer(serializers.ModelSerializer):

    song = SmallSongSerializer()
    profile_from = ProfileSerializer(source='user_from.profile')
    profile_to = ProfileSerializer(source='user_to.profile')

    class Meta:
        model = SongRecommendation
        fields = ('id', 'song', 'profile_from',
                  'profile_to', 'timestamp', 'description',)


class SocialDisplaySessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = SocialDisplaySession
        fields = '__all__'
