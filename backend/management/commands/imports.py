from django.core.management.base import BaseCommand

from ...functions import stream_import_functions



class Command(BaseCommand):
    help = 'Functions to import and clean endsong files'

    def add_arguments(self, parser):

        parser.add_argument('-cuf', '--cleanuserfiles', action='store_true', help='Cleans a user endsong files')
        parser.add_argument('-cms', '--createmissingsongs', action='store_true', help='Creates the missing songs in the database')
        parser.add_argument('-is', '--importstreams', action='store_true', help='Imports the endsong file streams to db')
        parser.add_argument('-ri', '--revertimport', action='store_true', help='Revert the import operation')
        parser.add_argument('-ds', '--deactivatestreams', action='store_true', help='Deactivate streams that happened before the latest import')
        parser.add_argument('-id', '--identity', type=int, help='user id')

    def handle(self, *args, **kwargs):

        clean = kwargs['cleanuserfiles']
        create = kwargs['createmissingsongs']
        import_streams = kwargs['importstreams']
        revert_import = kwargs['revertimport']
        deactivate_streams = kwargs['deactivatestreams']
        id = kwargs['identity']



        if create:
            stream_import_functions.create_missing_songs(id=id)

        if clean:
            stream_import_functions.clean_user_endsong_files(id=id)

        if import_streams:
            stream_import_functions.import_all_user_endsong_files(id=id)

        if revert_import:
            stream_import_functions.revert_user_stream_import(id=id)

        if deactivate_streams:
            stream_import_functions.deactivate_streams_before_last_import(id=id)
