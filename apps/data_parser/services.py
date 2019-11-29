import re
import os
import logging
import xml.etree.ElementTree as ET
import html
from bs4 import BeautifulSoup
from django.http import QueryDict

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
    add_summary_to_product()

def add_summary_to_product():
    files = os.listdir('uploads/text')
    products = Product.objects.all()
    for p in products:
        for fil in files:
            if p.name in fil:
                tree = ET.parse('uploads/text/'+fil)
                root = tree.getroot()
                body = root.find('body').text
                decoded = html.unescape(body)
                soup = BeautifulSoup(decoded, 'html.parser')
                p.comment = soup.get_text()
                p.save()

def extract_data(filename: str):
    try:
        splited = re.split('_', filename[:-4])
        informations = Informations.from_result(filename, splited)
        # Retrieve exiting univers, variable, dataset
        dataset = Dataset.objects.get(name=informations.dataset)
        variable = Variable.objects.get(dataset=dataset)
        univers = Univers.objects.get(variable=variable)
        # Retrieve or create others filter
        product, product_created = Product.objects.get_or_create(name=informations.product)
        product.datasets.add(dataset)
        depth, depth_created = Depth.objects.get_or_create(name=informations.depth)
        depth.products.add(product)
        stat, stat_created = Stat.objects.get_or_create(name=informations.stat)
        stat.depths.add(depth)
        plot_type, plot_type_created = PlotType.objects.get_or_create(name=informations.plot_type)
        plot_type.stats.add(stat)
        # Retrieve or create zone
        area, area_created = Area.objects.get_or_create(name=informations.area)
        subarea, subarea_created = Subarea.objects.get_or_create(name=informations.subarea, area=area)
        # Retrieve or create plot
        plot, plot_created = Plot.objects.get_or_create(filename = filename, area = area, subarea = subarea, univers = univers, variable = variable, dataset = dataset, product = product, depth = depth, stat = stat, plot_type = plot_type)
        # TODO: + add kpi files to corresponding table
        return informations
    except:
        return ErrorMsg.from_result(filename, 'Invalid filename')

'''
Return a object containing all hierarchical avalaible filters, so this struct:
dict = {
    areas
    |_ subareas
    univers
    |_ variables
        |_ datasets
            |_ products
                |_ depths
                    |_ stats
                        |_ plot_types
}
'''
def get_all_selectors():
    data = {}
    areas = Area.objects.all().values()
    data['areas'] = areas
    for index, a in enumerate(areas):
        subareas_by_area = Subarea.objects.filter(area = a['id']).values()
        data['areas'][index]['subareas'] = subareas_by_area
    univers = Univers.objects.all().values()
    data['univers'] = univers
    for i, u in enumerate(univers):
        variables = Variable.objects.filter(univers = u['id']).values()
        data['univers'][i]['variables'] = variables
        for j, v in enumerate(variables):
            datasets = Dataset.objects.filter(variable = v['id']).values()
            data['univers'][i]['variables'][j]['datasets'] = datasets
            for k, d in enumerate(datasets):
                products = Product.objects.filter(datasets = d['id']).values()
                data['univers'][i]['variables'][j]['datasets'][k]['products'] = products
                for l, p in enumerate(products):
                    depths = Depth.objects.filter(products = p['id']).values()
                    data['univers'][i]['variables'][j]['datasets'][k]['products'][l]['depths'] = depths
                    for m, de in enumerate(depths):
                        stats = Stat.objects.filter(depths = de['id']).values()
                        data['univers'][i]['variables'][j]['datasets'][k]['products'][l]['depths'][m]['stats'] = stats
                        for n, s in enumerate(stats):
                            plot_types = PlotType.objects.filter(stats = s['id']).values()
                            data['univers'][i]['variables'][j]['datasets'][k]['products'][l]['depths'][m]['stats'][n]['plot_types'] = plot_types
    return data


def get_id_from_name(key, criterion):
    if key == 'area':
        return Area.objects.get(name=criterion).id
    if key == 'subarea':
        return Subarea.objects.get(name=criterion).id
    if key == 'univers':
        return Univers.objects.get(name=criterion).id
    if key == 'variable':
        return Variable.objects.get(name=criterion).id
    if key == 'dataset':
        return Dataset.objects.get(name=criterion).id
    if key == 'product':
        return Product.objects.get(name=criterion).id
    if key == 'depth':
        return Depth.objects.get(name=criterion).id
    if key == 'stat':
        return Stat.objects.get(name=criterion).id
    if key == 'plot_type':
        return PlotType.objects.get(name=criterion).id

'''
Criteria should be integers (id send from frontend selectors), but through Open API it's more
convenient to use criteria names so for Open API string it is.
'''
def get_plot(criteria):
    for key, criterion in criteria.items():
        if isinstance(criterion, str):
            criteria[key] = get_id_from_name(key, criterion)
    query_dict = QueryDict('', mutable=True)
    query_dict.update(criteria)
    q = query_dict.dict()
    plot = Plot.objects.get(**query_dict.dict())
    return plot.__dict__
'''
{
    "area": "global",
    "subarea": "tropical-pacific-ocean",
    "univers": "BLUE",
    "variable": "Temperature",
    "dataset": "temperature",
    "product": "global-analysis-forecast-phy-001-024",
    "depth": "2000-5000m",
    "stat": "anomaly-correlation",
    "plot_type": "timeseries"
}
With Ids:
{
    "area": 1,
    "subarea": 29,
    "univers": 6,
    "variable": 15,
    "dataset": 92,
    "product": 242,
    "depth": 405,
    "stat": 507,
    "plot_type": 506
}
'''