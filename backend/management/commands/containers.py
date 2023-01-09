from django.core.management.base import BaseCommand

from ...functions import object_container_functions


class Command(BaseCommand):
    help = 'creates containers'

    def add_arguments(self, parser):

        parser.add_argument('-cac', '--createalbumcontainers',
                            action='store_true', help='Create the album containers for all artists')
        parser.add_argument('-csc', '--createsongcontainers',
                            action='store_true', help='Create an albums song containers')
        parser.add_argument('-smc', '--setmasterchild',
                            action='store_true', help='set the master child for all albums')
        parser.add_argument('-id', '--identity', type=int, help='user id')
        parser.add_argument('-o', '--offset', type=int, help='offset')

    def handle(self, *args, **kwargs):

        create_album_containers = kwargs['createalbumcontainers']
        create_song_containers = kwargs['createsongcontainers']
        set_master_child = kwargs['setmasterchild']
        id = kwargs['identity']
        offset = kwargs['offset']

        if offset == None:
            offset = 0

        if create_album_containers:
            object_container_functions.create_all_album_containers()

        if create_song_containers:
            object_container_functions.create_all_song_containers(delete_existing=False, offset=offset)

        if set_master_child:
            object_container_functions.set_container_master_child_albums()
