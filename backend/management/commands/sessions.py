from django.core.management.base import BaseCommand

from ...functions import session_log_export_functions



class Command(BaseCommand):
    help = 'Functions to import and clean endsong files'

    def add_arguments(self, parser):

        parser.add_argument('-ex', '--export', action='store_true', help='export a session file')
        parser.add_argument('-id', '--identity', type=int, help='session id')



    def handle(self, *args, **kwargs):

        export = kwargs['export']
        id = kwargs['identity']


        if export:
            session_log_export_functions.export_social_display_session_data(id)
