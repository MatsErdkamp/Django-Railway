from django.core.management.base import BaseCommand
from django.forms import model_to_dict
from ...functions import model_functions, spotify_get_functions


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument('-rd', '--removeduplicates',
                            action='store_true', help='Remove duplicates')
        parser.add_argument('-sd', '--scandatabase', action='store_true',
                            help='Scan Database for wrong entries')
        parser.add_argument('-sa', '--scanalbums', action='store_true',
                            help='Scan for albums not returned in api call')
        parser.add_argument('-dedo', '--deleteempty', action='store_true',
                            help='delete empty database objects')
        parser.add_argument('-rege', '--refreshgenres', action='store_true',
                            help='refresh genres')
        parser.add_argument('-demo', '--demomyms', action='store_true',
                            help='scan for demomyms')
        parser.add_argument('-sat', '--setalbumtypes', action='store_true',
                            help='set the album types')
        parser.add_argument('-ard', '--addreleasedate',
                            action='store_true', help='add the release date to albums')
        parser.add_argument('-o', '--offset', type=int, help='looping offset')
        parser.add_argument('-l', '--limit', type=int, help='query limit')
        parser.add_argument('-raf', '--refreshaudiofeatures', action='store_true',
                            help='refreshes audio features of songs')

    def handle(self, *args, **kwargs):

        rd = kwargs['removeduplicates']
        sd = kwargs['scandatabase']
        sa = kwargs['scanalbums']
        dedo = kwargs['deleteempty']
        rege = kwargs['refreshgenres']
        demo = kwargs['demomyms']
        offset = kwargs['offset']
        limit = kwargs['limit']
        ard = kwargs['addreleasedate']
        raf = kwargs['refreshaudiofeatures']
        sat = kwargs['setalbumtypes']

        if isinstance(offset, int) == False:
            offset = 0
        if isinstance(offset, int) == False:
            limit = 1000

        if rd:
            model_functions.remove_db_duplicates()

        if sd:
            model_functions.fix_song_album_relation()

        if sa:
            model_functions.scan_for_hidden_albums(artistOffset=offset)

        if dedo:
            model_functions.delete_empty_db_objects()

        if rege:
            spotify_get_functions.refresh_artist_genres()

        if demo:
            model_functions.scan_for_demomyms()

        if ard:
            model_functions.add_release_year(limit=limit)

        if raf:
            model_functions.refresh_audio_features()

        if sat:
            model_functions.set_correct_album_types_all_albums()

