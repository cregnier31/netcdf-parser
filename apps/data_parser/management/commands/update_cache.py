from django.core.management.base import BaseCommand, CommandError
import os
import sys
import time

from apps.data_parser.services import update_cache



class Command(BaseCommand):
    help = "Update cache files containing selectors tree (filters used in user interface)."
    
    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color, force_color=force_color)
        self.start_msg = """
╦ ╦┌─┐┌┬┐┌─┐┌┬┐┬┌┐┌┌─┐  ╔═╗┌─┐┌─┐┬ ┬┌─┐  ┌─┐┬┬  ┌─┐┌─┐   
║ ║├─┘ ││├─┤ │ │││││ ┬  ║  ├─┤│  ├─┤├┤   ├┤ ││  ├┤ └─┐   
╚═╝┴  ─┴┘┴ ┴ ┴ ┴┘└┘└─┘  ╚═╝┴ ┴└─┘┴ ┴└─┘  └  ┴┴─┘└─┘└─┘ooo
    """

    def handle(self, *arg, **options):
        try:
            print('\n\n\n'+self.start_msg+'\n\n\n')
            update_cache()
        except Exception as e:
            raise CommandError("Something went wrong ==> " + str(e))