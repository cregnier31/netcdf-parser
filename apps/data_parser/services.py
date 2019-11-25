import re
import os
import logging

from apps.data_parser.classes import Informations, ErrorMsg
from apps.data_parser.management.commands._utils import printProgressBar
from apps.data_parser.models import Univers, Area, Variable, Product, Dataset, Subarea, Depth, PlotType, Stat, Plot

def process_files(path, verbose):
    files = os.listdir(path)
    files_in_error = []
    printProgressBar(0, len(files), prefix = 'Progress:', suffix = 'Complete', length = 50)
    for index, filename in enumerate(files):
        data = extract_data(filename)
        if type(data) == ErrorMsg:
            files_in_error.append(data.__dict__)
        display = 'Complete \t\t'+str(len(files_in_error))+' errors / '+str(index+1)+' files'
        printProgressBar(index + 1, len(files), prefix = 'Progress:', suffix = display, length = 50)
    if verbose:
        logger = logging.getLogger('django')
        for name in files_in_error:
            logger.warning(name)

def extract_data(filename: str):
    try:
        informations = Informations.from_filename(filename)
        # variable = Variable.objects.get()
        # TODO: get or create if not exist object: univers, variable, dataset, etc from informations dict and save them
        # TODO: + add kpi files to corresponding table
        return informations
    except:
        return ErrorMsg.from_result(filename, 'Invalid filename')