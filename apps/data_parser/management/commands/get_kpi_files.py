from django.core.management.base import BaseCommand, CommandError
import os
import sys
import time

from apps.data_parser.download_files import get_kpi_instac


class Command(BaseCommand):
    help = "Download kpi files into upload folder"
    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color, force_color=force_color)
        self.start_msg = """
        START DOWNLOADING KPI files
    """

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Display errors',
        )

    def handle(self, *arg, **options):
        try:
            print('\n\n\n'+self.start_msg+'\n\n\n')
            verbose=False
            if options['verbose']: 
                verbose=True
            get_kpi_instac(verbose)
            if not verbose:
                print("\nUse --verbose to see files in error\n")
        except Exception as e:
            raise CommandError("Something went wrong ==> " + str(e))
