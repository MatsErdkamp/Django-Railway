from django.core.management.base import BaseCommand
from ...functions import recommendation_playlist_functions


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument('-u', '--update',
                            action='store_true', help='update')
        parser.add_argument('-id', '--identity', type=int, help='user id')
        

    def handle(self, *args, **kwargs):

        update = kwargs['update']
        user_id = kwargs['identity']

        if update:
            recommendation_playlist_functions.update_recommendation_playlist_content(user_id)
