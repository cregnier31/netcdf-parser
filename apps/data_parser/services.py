import re
import os
import logging
import xml.etree.ElementTree as ET
import html
from bs4 import BeautifulSoup
from django.http import QueryDict
import jsons,json
from termcolor import colored
from django.core.cache import cache
from django.core import serializers

from apps.data_parser.classes import Informations, ErrorMsg
from apps.data_parser.management.commands._utils import printProgressBar
from apps.data_parser.models import Universe, Area, Variable, Product, Dataset, Subarea, Depth, PlotType, Stat, Plot, Kpi
from apps.data_parser.serializers import AreaSerializer

###########################################################################################################################################

def process_plot_files(path, verbose):
    """
        Look for each files into folder to register plot into database (path, verbose)

        :param path: the path to folder you want to look in
        :param verbose: an optionnal parameter to display untreated files
        :return: None. Nothing to return, the service only display a progress bar
    """
    files = os.listdir(path)
    files_in_error = []
    printProgressBar(0, len(files), prefix = 'Progress:', suffix = 'Complete', length = 50)
    existing_plots_filenames = Plot.objects.all().values_list('filename', flat=True)
    for index, filename in enumerate(files):
        if not filename in existing_plots_filenames:
          data = extract_data(filename)
          if type(data) == ErrorMsg:
              files_in_error.append(data.__dict__)
        display = 'Complete '+str(len(files_in_error))+' errors / '+str(index+1)+' files'
        printProgressBar(index + 1, len(files), prefix = 'Progress:', suffix = display, length = 50)
    if verbose:
        logger = logging.getLogger('django')
        for wrong in files_in_error:
            error = colored(str(wrong['msg']), 'red')
            filename = wrong['filename']
            logger.warning(error + " : " + filename)

###########################################################################################################################################

def process_kpi_files(path, kind, verbose):
    """
        Look for kpi files into designated folder and save them to database (path)

        :param path: the folder to look in
        :return: None.
    """
    folder_name_to_area = {
        '_ARC_': 'arctic',
        '_BAL_': 'balticsea',
        '_BS_': 'blacksea',
        '_GLO_': 'global',
        '_IBI_': 'ibi',
        '_MED_': 'medsea',
        '_NWS_': 'nws',
    }
    series_name_to_variables = {
        'Temperature': 'Temperature',
        'Salinity': 'Salinity',
        'Sea level': 'Sea Surface Height',
    }
    total_files = sum([len(files) for r, d, files in os.walk(path)])
    counter_files = 0
    printProgressBar(0, total_files, prefix = 'Progress:', suffix = 'Complete', length = 50)
    # Loop over folders
    for dirpath, dirnames, files in os.walk(path):
        if files:
            for filename in files:
                counter_files = counter_files + 1
                display = 'Complete '+str(counter_files)+'/'+str(total_files)+' files'
                if '.json' in filename: 
                    with open(dirpath+'/'+filename) as json_file:
                        data = json.load(json_file)
                        for area_shortname in folder_name_to_area:
                            if area_shortname in data['product']:
                                area_name = folder_name_to_area[area_shortname]
                                area = Area.objects.get(name=area_name)
                                for serie in data['series']:
                                    if serie['name'] in series_name_to_variables:
                                        variable_name = series_name_to_variables[serie['name']]
                                        variable = Variable.objects.filter(name=variable_name)
                                        if variable:
                                            product = data['product']
                                            kpi = Kpi.objects.get_or_create(what=data['id'], kind=kind, content=serie['data'], product=product, variable=variable[0], area=area)
                printProgressBar(counter_files, total_files, prefix = 'Progress:', suffix = display, length = 50)
    return None

###########################################################################################################################################

def process_files(verbose):
    """
        Look into uploads directory to proccess files (path, verbose)

        :param verbose: an optionnal parameter to display untreated files
        :return: None
    """
    line = '_________________________________________________________________________________________________________\n'
    print(line + 'Step 1/6 \t Processing plot files...')
    process_plot_files("uploads/plot", verbose)
    print(line + 'Step 2/6 \t Adding description comment to plots...')
    add_summary_to_product('uploads/text', verbose)
    print(line + 'Step 3/6 \t Processing insitu kpi files...')
    process_kpi_files("uploads/kpi/INSITU", 'INSITU', verbose)
    print(line + 'Step 4/6 \t Processing satellite kpi files...')
    process_kpi_files("uploads/kpi/SAT", 'SAT', verbose)
    print(line + 'Step 5/6 \t Processing skill score kpi files...')
    process_kpi_files("uploads/kpi/SKILL_SCORE", 'SKILL_SCORE', verbose)
    print(line + 'Step 6/6 \t Preload cache files...')
    update_cache()

###########################################################################################################################################

def add_summary_to_product(path, verbose):
    """
        Look for each files into uploads/text and add their content into database as plot comment ()

        :return: None.
    """
    files = os.listdir(path)
    products = Product.objects.all()
    counter = 0
    files_in_error = []
    printProgressBar(counter, len(files), prefix = 'Progress:', suffix = 'Complete', length = 50)
    
    for fil in files:
        has_summary = False
        for p in products:
            if p.name in fil:
                tree = ET.parse('uploads/text/'+fil)
                root = tree.getroot()
                body = root.find('body').text
                decoded = html.unescape(body)
                soup = BeautifulSoup(decoded, 'html.parser')
                p.comment = soup.get_text()
                p.save()
                has_summary = True
        if not has_summary:
            files_in_error.append(fil)
        counter = counter + 1
        display = 'Complete '+str(len(files_in_error))+' errors / '+str(counter)+' files'
        printProgressBar(counter, len(files), prefix = 'Progress:', suffix = display, length = 50)
    if verbose:
        logger = logging.getLogger('django')
        for wrong in files_in_error:
            error = colored('No matching product', 'red')
            filename = wrong
            logger.warning(error + " : " + filename)

###########################################################################################################################################

def extract_data(filename: str):
    """
        Parse informations about plot file from filename (filename)

        Note that universe and variable are provided by fixtures and not present
        into filename datas. So I can only get those from dataset inforamation.
        Return type can be Informations class if succeed or ErrorMsg class if not.

        :param filename: filename that will be parsed
        :return: class. Object exposing parsing results
    """
    try:
        splited = re.split('_', filename[:-4])
        informations = Informations.from_result(filename, splited)
        area = Area.objects.get(name=informations.area)
        dataset = Dataset.objects.get(name=informations.dataset)
        variable = Variable.objects.get(datasets=dataset)
        universe = Universe.objects.get(variables=variable)
        if not universe in area.universes.all():
            universe.areas.add(area)
        catalogue_link = "http://marine.copernicus.eu/services-portfolio/access-to-products/?option=com_csw&view=details&product_id="+informations.product
        product, product_created = Product.objects.get_or_create(name=informations.product, catalogue_url=catalogue_link)
        if not product in dataset.products.all():
            product.datasets.add(dataset)
        subarea, subarea_created = Subarea.objects.get_or_create(name=informations.subarea, product=product)
        depth, depth_created = Depth.objects.get_or_create(name=informations.depth)
        if not depth in subarea.depths.all():
            depth.subareas.add(subarea)
        stat, stat_created = Stat.objects.get_or_create(name=informations.stat)
        if not stat in depth.stats.all():
            stat.depths.add(depth)
        plot_type, plot_type_created = PlotType.objects.get_or_create(name=informations.plot_type)
        if not plot_type in stat.plot_types.all():
            plot_type.stats.add(stat)
        plot, plot_created = Plot.objects.get_or_create(filename = filename, area = area, subarea = subarea, universe = universe, variable = variable, dataset = dataset, product = product, depth = depth, stat = stat, plot_type = plot_type)
        return informations
    except Exception as e:
        return ErrorMsg.from_result(filename, e)

###########################################################################################################################################
def update_cache():
    """
        Return a object containing all hierarchical avalaible filters ()
        
        Here is its struct:
        dict = {
            areas
            |_ subareas
                |_ universe
                    |_ variables
                        |_ datasets
                            |_ products
                                |_ depths
                                    |_ stats
                                        |_ plot_types
        :return: Json. 
    """
    cache.delete('my_data')
    areas = Area.objects.all()
    serializer = AreaSerializer(instance=areas, many=True)
    data = {'areas':serializer.data}
    cache.set('my_data', data, None )
    return data

def get_cached_data():
    data = cache.get('my_data')
    if data == None:
        data = update_cache()
    return data

###########################################################################################################################################

def get_id_from_name(key, criterion, criteria):
    """
        Get data from database, matching name (key, criterion)

        :param key: the object type to request
        :param criterion: the object names
        :return: Object.
    """
    if key == 'area':
        return Area.objects.get(name=criterion).id
    if key == 'subarea':
        return Subarea.objects.get(name=criterion, area=criteria['area']).id
    if key == 'universe':
        return Universe.objects.get(name=criterion).id
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

###########################################################################################################################################

def get_plot(criteria):
    """
        Get plot matching criteria (criteria)

        Criteria should be integers (id send from frontend selectors), but through Open API it's more
        convenient to use criteria names so for Open API string it is.

        :param criteria: some criteria
        :return: Plot.
    """
    for key, criterion in criteria.items():
        if isinstance(criterion, str):
            criteria[key] = get_id_from_name(key, criterion, criteria)
    query_dict = QueryDict('', mutable=True)
    query_dict.update(criteria)
    q = query_dict.dict() 
    try:
        plot = Plot.objects.get(**query_dict.dict()) 
        return plot.__dict__
    except:
        return {}

###########################################################################################################################################

def autocomplete(slug):
    """
        Look for object which name contains string (slug)

        This method look for objects of type Variable, Dataset and Product only
        and need at least 3 characters.

        :param slug: the string to look for
        :return: Collection.
    """
    res = {}
    if len(slug)>=3:
        products = Product.objects.filter(name__icontains = slug).values('id', 'name')
        if len(products):
            res['products'] = products
        variables = Variable.objects.filter(name__icontains = slug).values('id', 'name')
        if len(variables):
            res['variables'] = variables
        datasets = Dataset.objects.filter(name__icontains = slug).values('id', 'name')
        if len(datasets):
            res['datasets'] = datasets
    return res

###########################################################################################################################################

def flush_data():
    """
        Flush database tables used by data_parser ()

        Some table are flushed uing cascade on delete.

        :return: None.
    """
    Area.objects.all().delete()
    Universe.objects.all().delete()
    Product.objects.all().delete()
    Depth.objects.all().delete()
    Stat.objects.all().delete()
    PlotType.objects.all().delete()

###########################################################################################################################################

def get_kpi(criteria):
    """
        Get Kpi matching criteria (criteria)

        Criteria should be integers (id send from frontend selectors), but through Open API it's more
        convenient to use criteria names so for Open API string it is.

        :param criteria: some criteria
        :return: Kpi.
    """
    for key, criterion in criteria.items():
        if isinstance(criterion, str) and key not in ["what", "kind"]:
            criteria[key] = get_id_from_name(key, criterion, criteria)
    query_dict = QueryDict('', mutable=True)
    query_dict.update(criteria)
    q = query_dict.dict()
    try:
        rs = Kpi.objects.filter(**query_dict.dict()).values()
        kpis = {}
        for key, item in enumerate(rs):
            print(item)
            if not item['kind'] in kpis:
                kpis[item['kind']] = []
            kpis[item['kind']].append(item)
        return kpis
    except:
        return {}

###########################################################################################################################################
def setup_database():
    parse_json_area()
    parse_json_univers_var_dset()
    return None

def parse_json_area():
    with open('area.json') as json_file:
        data = json.load(json_file)
        for a in data:
            area, area_created = Area.objects.get_or_create(name=a['name'], fullname=a['fullname']) 
    return None 

def parse_json_univers_var_dset():
    with open('universe_var_dtset.json') as json_file:
        data = json.load(json_file)
        for u in data:
            universe, universe_created = Universe.objects.get_or_create(name=u) 
            for v in data[u]:
                variable, variable_created = Variable.objects.get_or_create(name=v, universe=universe)
                for d in data[u][v]:
                    dataset, dataset_created = Dataset.objects.get_or_create(name=d, variable=variable)
    return None 