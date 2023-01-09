from django.core.management.base import BaseCommand

from ...functions import temp_import_functions



class Command(BaseCommand):
    help = 'Functions to import and clean endsong files'

    def add_arguments(self, parser):

        parser.add_argument('-cms', '--createmissingsongs', action='store_true', help='Creates the missing songs in the database')
        parser.add_argument('-is', '--importstreams', action='store_true', help='Imports the endsong file streams to db')
        parser.add_argument('-ri', '--revertimport', action='store_true', help='Revert the import operation')
        parser.add_argument('-ds', '--deactivatestreams', action='store_true', help='Deactivate streams that happened before the latest import')
        parser.add_argument('-id', '--identity', type=int, help='user id')
        parser.add_argument('-un', '--username', type=str, help='username')
        parser.add_argument('-asf', '--addsongsfirst', type=bool, help='add songs first')

    def handle(self, *args, **kwargs):

        create = kwargs['createmissingsongs']
        id = kwargs['identity']
        username = kwargs['username']
        asf = kwargs['addsongsfirst']
        imps = kwargs['importstreams']

        if imps:
            temp_import_functions.import_streams_temp(id=id, username=username)

        if create:
            temp_import_functions.genenate_streams_from_temp_import(id=id)

