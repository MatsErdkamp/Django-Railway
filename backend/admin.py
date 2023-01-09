from django.contrib import admin
from .models import *
from django.db.models.aggregates import Count
from .functions import image_functions, playlist_generation_functions


admin.site.register(Image)
admin.site.register(UserFollow)



class UserCacheObjectAdmin(admin.ModelAdmin):
    list_display = ["key"]

admin.site.register(UserCacheObject, UserCacheObjectAdmin)

class GroupCacheObjectAdmin(admin.ModelAdmin):
    list_display = ["key", "invalidated_subcache_percentage"]
    filter_horizontal = ('valid_subcaches',)

admin.site.register(GroupCacheObject, GroupCacheObjectAdmin)

class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "identifier", "owner"]

admin.site.register(Group, GroupAdmin)


class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ["group", "user", "is_admin"]

admin.site.register(GroupMembership, GroupMembershipAdmin)


class EndsongFileAdmin(admin.ModelAdmin):
    list_display = ['__str__', "user", "cleaned", "uris_available_in_database"]


admin.site.register(EndsongFile, EndsongFileAdmin)


class AlbumContainerAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'artist']
    search_fields = ['name', 'artist__name']
    raw_id_fields = ('artist', 'master_child_album')


admin.site.register(AlbumContainer, AlbumContainerAdmin)


class SongContainerAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'artist']
    search_fields = ['name', 'artist__name']
    raw_id_fields = ('artist', 'master_child_song', 'album_container')


admin.site.register(SongContainer, SongContainerAdmin)


class RankingAdmin(admin.ModelAdmin):
    raw_id_fields = ('song', )


admin.site.register(Ranking, RankingAdmin)


class SongRecommendationAdmin(admin.ModelAdmin):
    raw_id_fields = ('song', )


admin.site.register(SongRecommendation, SongRecommendationAdmin)


class RankingInline(admin.TabularInline):
    model = Ranking
    raw_id_fields = ("song", )
    readonly_fields = ["ranking_position", "song",
                       "ranking_change_trend", "ranking_change_amount", "compatibility"]

    extra = 0  # how many rows to show


def update_playlist_songs(modeladmin, request, queryset):
    playlist_generation_functions.update_playlists(queryset, hours=0)


def remove_playlist_if_dead(modeladmin, request, queryset):
    playlist_generation_functions.remove_playlist_if_dead(queryset)


class PlaylistAdmin(admin.ModelAdmin):
    readonly_fields = ["last_update", ]

    list_display = ["name", "update", "last_update"]
    inlines = [RankingInline]
    raw_id_fields = ("image",)
    filter_horizontal = ('members',)
    actions = [update_playlist_songs, remove_playlist_if_dead]


admin.site.register(Playlist, PlaylistAdmin)

class GroupRankingInline(admin.TabularInline):
    model = GroupRanking
    raw_id_fields = ("song", )
    readonly_fields = ["ranking_position", "song",
                       "ranking_change_trend", "ranking_change_amount", "compatibility"]

    extra = 0  # how many rows to show

class GroupPlaylistAdmin(admin.ModelAdmin):
    readonly_fields = ["last_update", ]

    list_display = ["name", "group", "update", "last_update"]
    inlines = [GroupRankingInline]
    raw_id_fields = ("image",)
    actions = [update_playlist_songs, ]


admin.site.register(GroupPlaylist, GroupPlaylistAdmin)

class RecommendationPlaylistAdmin(admin.ModelAdmin):
    readonly_fields = ["last_update", "songs"]

    list_display = ["name", "update", "last_update"]
    raw_id_fields = ("image",)


admin.site.register(RecommendationPlaylist, RecommendationPlaylistAdmin)


class StreamAdmin(admin.ModelAdmin):
    raw_id_fields = ("song",)
    search_fields = ['song__name']


admin.site.register(Stream, StreamAdmin)


class GenreAdmin(admin.ModelAdmin):

    list_display = ["name", 'artist_count']
    search_fields = ['name']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(artist_count=Count('artist')
                         ).order_by('-artist_count', 'name')
        return qs

    def artist_count(self, genre_instance):
        return genre_instance.artist_count


admin.site.register(Genre, GenreAdmin)

class GenreContainerAdmin(admin.ModelAdmin):

    list_display = ["name"]
    search_fields = ['name']
    filter_horizontal = ('subgenres',)

    def artist_count(self, genre_instance):
        return genre_instance.artist_count


admin.site.register(GenreContainer, GenreContainerAdmin)


def refresh_artist_image(modeladmin, request, queryset):

    image_functions.refresh_artist_images(queryset)


def redo_artist_containers(modeladmin, request, queryset):

    object_container_functions.redo_all_containers_for_artist(queryset[0])


class ArtistAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ['name']
    filter_horizontal = ('genre',)
    raw_id_fields = ("image",)

    actions = [refresh_artist_image, redo_artist_containers]


admin.site.register(Artist, ArtistAdmin)


class SongAdmin(admin.ModelAdmin):
    list_display = ["name", "artist", "album"]
    search_fields = ['id', 'name', 'artist__name', "album__name"]
    raw_id_fields = ("artist", "album", "song_container")


admin.site.register(Song, SongAdmin)


def refresh_album_image(modeladmin, request, queryset):

    image_functions.refresh_album_images(queryset)


class AlbumAdmin(admin.ModelAdmin):
    list_display = ["name", "artist", "album_container", "album_type"]
    search_fields = ['name', 'artist__name']
    raw_id_fields = ("artist", "image", "album_container")

    list_filter = (
        ('album_container', admin.EmptyFieldListFilter),
        'album_type'
    )

    actions = [refresh_album_image, ]


admin.site.register(Album, AlbumAdmin)


class ProfileAdmin(admin.ModelAdmin):
    readonly_fields = ["last_request"]
    fields = ["user", "search_history",
              "last_request", "image", "banner_image"]
    list_display = ["get_user_id","user", "last_request"]
    raw_id_fields = ("image",)

    @admin.display(ordering='user__id', description='User ID')
    def get_user_id(self, obj):
        return obj.user.id


admin.site.register(Profile, ProfileAdmin)


class SocialDisplayAdmin(admin.ModelAdmin):
    readonly_fields = ["session_start", "last_update"]

    fields = ["user", "session_start", "last_update"]
    list_display = ["id", "user", "session_start", "last_update"]


admin.site.register(SocialDisplaySession, SocialDisplayAdmin)

admin.site.register(SocialDisplayUserLog)
