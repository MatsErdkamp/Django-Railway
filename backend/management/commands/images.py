from django.core.management.base import BaseCommand

from ...functions import image_functions


class Command(BaseCommand):
    help = 'Generates colors'

    def add_arguments(self, parser):

        parser.add_argument('-rartist', '--refreshartist',
                            action='store_true', help='Refresh artist images')
        parser.add_argument('-ralbum', '--refreshalbum',
                            action='store_true', help='Refresh album images')
        parser.add_argument('-rprofile', '--refreshprofile',
                            action='store_true', help='Refresh profile images')
        parser.add_argument('-s', '--save', action='store_true',
                            help='save to db')

    def handle(self, *args, **kwargs):

        refresh_artist = kwargs['refreshartist']
        refresh_album = kwargs['refreshalbum']
        refresh_profile = kwargs['refreshprofile']
        save= kwargs['save']

        if refresh_artist:
            image_functions.refresh_artist_images()

        if refresh_album:
            image_functions.refresh_album_images(save_to_db=save)

        if refresh_profile:
            image_functions.refresh_profile_images(save_to_db=save)
