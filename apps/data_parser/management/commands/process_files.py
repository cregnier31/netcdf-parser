from django.core.management.base import BaseCommand, CommandError
import os
import sys
import time

from apps.data_parser.services import process_files



class Command(BaseCommand):
    help = "Process plot files into /upload/plot repository to extract data and save them into database."

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Display errors',
        )

    def handle(self, *arg, **options):
        # TODO: uncomment try / except
        # try:
        self.stdout.write("Files processing...")
        verbose=False
        if options['verbose']:
            verbose=True
        process_files("uploads/plot", verbose)
        if not verbose:
            print("Use --verbose to see files in error")
        # except Exception as e:
        #     raise CommandError("Something went wrong ==> " + str(e))