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
    # Retrieve filename of all existing Plots
    existing_plots_filenames = Plot.objects.all().values_list('filename', flat=True)
    for index, filename in enumerate(files):
        # If Plot already exists, there is no need to process the filename again
        if not filename in existing_plots_filenames:
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
        splited = re.split('_', filename[:-4])
        informations = Informations.from_result(filename, splited)
        # Retrieve exiting univers, variable, dataset
        dataset = Dataset.objects.get(name=informations.dataset)
        variable = Variable.objects.get(dataset=dataset)
        univers = Univers.objects.get(variable=variable)
        # Retrieve or create others filter
        product, product_created = Product.objects.get_or_create(name=informations.product, dataset=dataset)
        depth, depth_created = Depth.objects.get_or_create(name=informations.depth, product=product)
        stat, stat_created = Stat.objects.get_or_create(name=informations.stat, depth=depth)
        plot_type, plot_type_created = PlotType.objects.get_or_create(name=informations.plot_type, stat=stat)
        # Retrieve or create zone
        area, area_created = Area.objects.get_or_create(name=informations.area)
        subarea, subarea_created = Subarea.objects.get_or_create(name=informations.subarea, area=area)
        # Retrieve or create plot
        plot, plot_created = Plot.objects.get_or_create(
          filename = filename,
          area = area,
          subarea = subarea,
          univers = univers,
          variable = variable,
          dataset = dataset,
          product = product,
          depth = depth,
          stat = stat,
          plot_type = plot_type
        )
        # TODO: + add kpi files to corresponding table
        return informations
    except:
        return ErrorMsg.from_result(filename, 'Invalid filename')