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

from apps.data_parser.classes import Informations, ErrorMsg
from apps.data_parser.management.commands._utils import printProgressBar
from apps.data_parser.models import Universe, Area, Variable, Product, Dataset, Subarea, Depth, PlotType, Stat, Plot, Kpi

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

def process_kpi_files(path, verbose):
    # TODO: validate correspondance dict
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
                                            kpi = Kpi.objects.get_or_create(what=data['id'], content=serie['data'], product=product, variable=variable[0], area=area)
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
    print(line + 'Step 1/4 \t Processing plot files...')
    process_plot_files("uploads/plot", verbose)
    print(line + 'Step 2/4 \t Adding description comment to plots...')
    add_summary_to_product('uploads/text', verbose)
    print(line + 'Step 3/4 \t Processing kpi files...')
    process_kpi_files("uploads/kpi_INSTAC", verbose)
    print(line + 'Step 4/4 \t Preload cache files...')
    cache_data()

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
        subarea = Subarea.objects.get(name=informations.subarea, area=area)
        # area, area_created = Area.objects.get_or_create(name=informations.area)
        # subarea, subarea_created = Subarea.objects.get_or_create(name=informations.subarea, area=area)
        dataset = Dataset.objects.get(name=informations.dataset)
        variable = Variable.objects.get(dataset=dataset)
        universe = Universe.objects.get(variable=variable)
        if not universe in subarea.universes.all():
            universe.subareas.add(subarea)
        product, product_created = Product.objects.get_or_create(name=informations.product)
        product.datasets.add(dataset)
        depth, depth_created = Depth.objects.get_or_create(name=informations.depth)
        depth.products.add(product)
        stat, stat_created = Stat.objects.get_or_create(name=informations.stat)
        stat.depths.add(depth)
        plot_type, plot_type_created = PlotType.objects.get_or_create(name=informations.plot_type)
        plot_type.stats.add(stat)
        plot, plot_created = Plot.objects.get_or_create(filename = filename, area = area, subarea = subarea, universe = universe, variable = variable, dataset = dataset, product = product, depth = depth, stat = stat, plot_type = plot_type)
        return informations
    except Exception as e:
        return ErrorMsg.from_result(filename, e)

###########################################################################################################################################

def group_obj_by_key(obj, key = None):
    """
        Create a key, values map from an array, group by a key (obj, key)

        :param obj: the array I want to convert
        :param key: the key I want to use
        :return: Dict. 

        :Example:

        >>> tab = [
                {'type': 'fruit', 'name': 'apple'},
                {'type': 'fruit', 'name': 'banana'},
                {'type': 'vegetable', 'name': 'carrot'},
                {'type': 'vegetable', 'name': 'potato'}
            ]
        >>> group_obj_by_key(tab, 'type')
        {
            'fruit': [
                {'type': 'fruit', 'name': 'apple'},
                {'type': 'fruit', 'name': 'banana'},
            ],
            'vegetable': [
                {'type': 'vegetable', 'name': 'carrot'},
                {'type': 'vegetable', 'name': 'potato'}
            ]
        }
    """
    res = {}
    for i, item in enumerate(obj):
        selector = item[key]
        if not selector in res:
            res[selector] = []
        res[selector].append(item)
    return res

###########################################################################################################################################
def get_universes():
    res = {}
    for item in Universe.objects.all():
        for subitem in item.subareas.all():
            if not subitem.id in res:
                res[subitem.id] = []
            res[subitem.id].append({'id':item.__dict__['id'], 'name':item.__dict__['name']})
    return res

def get_products():
    res = {}
    for item in Product.objects.all():
        for subitem in item.datasets.all():
            if not subitem.id in res:
                res[subitem.id] = []
            res[subitem.id].append({'id':item.__dict__['id'], 'name':item.__dict__['name'], 'comment':item.__dict__['comment']})
    return res

def get_depths():
    res = {}
    for item in Depth.objects.all():
        for subitem in item.products.all():
            if not subitem.id in res:
                res[subitem.id] = [] 
            res[subitem.id].append({'id':item.__dict__['id'], 'name':item.__dict__['name']})
    return res

def get_stats():
    res = {}
    for item in Stat.objects.all():
        for subitem in item.depths.all():
            if not subitem.id in res:
                res[subitem.id] = [] 
            res[subitem.id].append({'id':item.__dict__['id'], 'name':item.__dict__['name']})
    return res

def get_plot_types():
    res = {}
    for item in PlotType.objects.all():
        for subitem in item.stats.all():
            if not subitem.id in res:
                res[subitem.id] = [] 
            res[subitem.id].append({'id':item.__dict__['id'], 'name':item.__dict__['name']})
    return res

###########################################################################################################################################
def update_cache():
    cache.delete('my_data')
    data = jsons.dump(get_all_selectors())
    cache.set('my_data', data, None )
    return data

def get_cached_data():
    data = cache.get('my_data')
    if data == None:
        data = update_cache()
    return data

def get_all_selectors():
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

        To optimize time to constuct dict, I limit queries using a map reduce concept,
        creating a map for each kind of object. Keys of each map is object parents id

        :return: Dict. 
    """
    # Request all data
    areas = Area.objects.all().values()
    subareas = group_obj_by_key(Subarea.objects.all().values(), 'area_id')
    universes = get_universes()
    variables = group_obj_by_key(Variable.objects.all().values(), 'universe_id')
    datasets = group_obj_by_key(Dataset.objects.all().values(), 'variable_id')
    products = get_products()
    depths = get_depths()
    stats = get_stats()
    plot_types = get_plot_types()
    # Add areas
    for i_a, area in enumerate(areas):
        areas[i_a]['subareas'] = []
        id_a = area['id']
        # Add subareas
        if area['id'] in subareas:
            areas[i_a]['subareas'] = subareas[id_a]
            # Add universe
            for i_sub, subarea in enumerate(areas[i_a]['subareas']):
                areas[i_a]['subareas'][i_sub]['universes'] = []
                id_sub = subarea['id']
                if id_sub in universes:
                    areas[i_a]['subareas'][i_sub]['universes'] = universes[id_sub]
                    # Add variables
                    for i_u, univer in enumerate(areas[i_a]['subareas'][i_sub]['universes']):
                        areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'] = []
                        id_u = univer['id']
                        if id_u in variables:
                            areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'] = variables[id_u]
                            # Add datasets
                            for i_v, variable in enumerate(areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables']):
                                areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'] = []
                                id_v = variable['id']
                                if id_v in datasets:
                                    areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'] = datasets[id_v]
                                    # Add products
                                    for i_d, dataset in enumerate(areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets']):
                                        areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'][i_d]['products'] = []
                                        id_d = dataset['id']
                                        if id_d in products:
                                            areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'][i_d]['products'] = products[id_d]
                                            # Add depths
                                            for i_p, product in enumerate(areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'][i_d]['products']):
                                                areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'][i_d]['products'][i_p]['depths'] = []
                                                id_de = product['id']
                                                if id_de in depths:
                                                    areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'][i_d]['products'][i_p]['depths'] = depths[id_de]
                                                    # Add stats
                                                    for i_de, depth in enumerate(areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'][i_d]['products'][i_p]['depths']):
                                                        areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'][i_d]['products'][i_p]['depths'][i_de]['stats'] = []
                                                        id_s = depth['id']
                                                        if id_s in stats:
                                                            areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'][i_d]['products'][i_p]['depths'][i_de]['stats'] = stats[id_s]
                                                            # Add plot_types
                                                            for i_s, stat in enumerate(areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'][i_d]['products'][i_p]['depths'][i_de]['stats']):
                                                                areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'][i_d]['products'][i_p]['depths'][i_de]['stats'][i_s]['plot_types'] = []
                                                                id_pt = stat['id']
                                                                if id_pt in plot_types:
                                                                    areas[i_a]['subareas'][i_sub]['universes'][i_u]['variables'][i_v]['datasets'][i_d]['products'][i_p]['depths'][i_de]['stats'][i_s]['plot_types'] = plot_types[id_pt]
    data = {} 
    data['areas'] = areas
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
    plot = Plot.objects.get(**query_dict.dict()) 
    return plot.__dict__

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