from django.urls import path
from .views import *
from .views_v2 import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
# from cacheops import cached_view_as

urlpatterns = [
    path('', APIGetStreams.as_view(), name='api-get-streams-recent'),
    path('recent/', APIGetStreams.as_view(), name='api-get-streams'),
    path('artists/', APIGetArtists.as_view(), name='api-get-artists'),
    path('album/', APIGetAlbumItems.as_view(), name='api-get-album'),
    path('albums/', APIGetAlbums.as_view(), name='api-get-albums'),
    path('songs/', APIGetSongs.as_view(), name='api-get-songs'),
    path('playlists/', APIGetPlaylists.as_view(), name='api-get-playlists'),
    path('playlist/', APIGetPlaylistItems.as_view(), name='api-get-playlist'),
    path('playlists/create/', APICreatePlaylist.as_view(), name='api-create-playlist'),
    path('playlists/recommend/', APIRecommendPlaylistSongs.as_view(), name='api-recommend-playlist'),
    path('current/', APIGetCurrentlyStreaming.as_view(),name='api-get-currently-streaming'),
    path('songs/detail/', APIGetSongDetail.as_view(), name='api-get-song-detail'),
    path('songs/compatibility/', APIGetSongCompatibility.as_view(), name='api-get-song-compatibility'),
    path('songs/compatibilities/', APIGetSongCompatibilities.as_view(), name='api-get-song-compatibilities'),
    path('song-containers/detail/', APIGetSongContainerDetail.as_view(), name='api-get-song-container-detail'),
    path('artists/detail/', APIGetArtistDetail.as_view(), name='api-get-artist-detail'),
    path('artists/detail/distribution/', APIGetArtistDetailDistribution.as_view(), name='api-get-artist-distribution-detail'),
    path('artists/detail/streams-over-time/', APIGetArtistStreamsOverTime.as_view(), name='api-get-artist-detail-streams-over-time'),
    path('albums/detail/', APIGetAlbumDetail.as_view(), name='api-get-album-detail'),
    path('albums/detail/distribution/', APIGetAlbumDetailDistribution.as_view(), name='api-get-album-detail-distribution'),
    path('albums/c/detail/distribution/', (APIGetAlbumContainerDetailDistribution.as_view()), name='api-get-album-detail-distribution'),
    path('albums/detail/streams-over-time/', APIGetAlbumStreamsOverTime.as_view(), name='api-get-album-detail-streams-over-time'),
    path('album-containers/detail/', APIGetAlbumContainerDetail.as_view(), name='api-get-album-detail'),
    path('search/', APIGetSearchResults.as_view(), name='api-get-search-results'),
    path('user/', APIGetUser.as_view(), name='api-get-user'),
    path('user/terminate/', APITerminateUser.as_view(), name='api-terminate-user'),
    path('user/profile/', APIGetUserProfile.as_view(), name='api-get-user-profile'),
    path('user/groups/', APIGetUserGroups.as_view(), name='api-get-user-groups'),
    path('user/recommendations/', APIUserRecommendations.as_view(), name='api-get-or-post-user-recommendations'),
    path('user/search-history/', APIUserSearchHistory.as_view(), name='api-get-user-search-history'),
    path('user/social-displays/', APIUserSocialDisplays.as_view(), name='api-get-user-social-display-sessions'),
    path('user/upload-streams/', APIPostStreams.as_view(), name='api-post-streams'),
    path('users/', APIGetUsers.as_view(), name='api-get-users'),
    path('users/profiles/', APIGetUserProfiles.as_view(), name='api-get-user-profiles'),
    path('user/follow', APIFollowUser.as_view(), name='api-follow-user'),
    path('user/unfollow', APIUnfollowUser.as_view(), name='api-unfollow-user'),
    path('next/', APINextSong.as_view(), name="api-next"),
    path('group/', APIGetGroup.as_view(), name='api-get-group'),
    path('group/playlists/', APIGetGroupPlaylists.as_view(), name='api-get-group-playlists'),
    path('group/join', APIJoinGroup.as_view(), name='api-join-group'),
    path('group/leave', APILeaveGroup.as_view(), name='api-leave-group'),
    path('play/', APIPlaySong.as_view(), name="api-play"),
    path('moodtracker/', APIMoodTracker.as_view(), name="api-track-mood"),

]


urlpatterns += [
    path('v2/songs/', V2GetUserSongs.as_view(), name='api-get-user-songs'),
    path('v2/group/songs/', V2GetGroupSongs.as_view(), name='api-get-group-songs'),
    path('v2/albums/', V2GetUserAlbums.as_view(), name='api-get-user-albums'),
    path('v2/group/albums/', V2GetGroupAlbums.as_view(), name='api-get-group-albums'),
    path('v2/artists/', V2GetUserArtists.as_view(), name='api-get-user-artists'),
    path('v2/group/artists/', V2GetGroupArtists.as_view(), name='api-get-group-artists'),
]