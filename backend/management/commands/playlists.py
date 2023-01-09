from django.core.management.base import BaseCommand
from ...functions import playlist_generation_functions


class Command(BaseCommand):
    

    def add_arguments(self, parser):

        parser.add_argument('-u', '--update',
                            action='store_true', help='update')
        
        parser.add_argument('-rmx', '--remix',
                            action='store_true', help='remix')

    def handle(self, *args, **kwargs):

        update = kwargs['update']
        remix = kwargs['remix']


        if update:
            playlist_generation_functions.update_playlists()
        if remix:
            playlist_generation_functions.remix_playlist()