from django.core.management.base import BaseCommand

from ...functions import spotify_post_functions


class Command(BaseCommand):
    help = 'Generates playlists'

    def add_arguments(self, parser):

        parser.add_argument('-g', '--generate',
                            action='store_true', help='Generate Playlist')

    def handle(self, *args, **kwargs):

        generate = kwargs['generate']

        if generate:
            spotify_post_functions.post_user_playlist()

    