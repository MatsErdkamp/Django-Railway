from django.core.management.base import BaseCommand

from ...functions import throwaway_functions



class Command(BaseCommand):


    def add_arguments(self, parser):

        parser.add_argument('-ex', '--execute', action='store_true', help='execute function')

    def handle(self, *args, **kwargs):

        ex = kwargs['execute']

        if ex:
            throwaway_functions.throwaway()

