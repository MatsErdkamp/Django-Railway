from django.core.management.base import BaseCommand

from ...functions import color_functions



class Command(BaseCommand):
    help = 'Generates colors'

    def add_arguments(self, parser):

        parser.add_argument('-d', '--delete', action='store_true', help='Delete all colors')
        parser.add_argument('-g', '--generate', action='store_true', help='Generate all colors')

    def handle(self, *args, **kwargs):

        delete = kwargs['delete']
        generate = kwargs['generate']

        if delete:
            color_functions.delete_colors()
        elif generate:
            color_functions.generate_colors()
        else:
            print("use -g or --generate to generate colors and -d or --delete to delete all colors!")





