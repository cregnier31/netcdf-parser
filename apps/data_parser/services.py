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
from datetime import datetime
from django.utils import timezone
from apps.data_parser.classes import Informations, ErrorMsg
from apps.data_parser.management.commands._utils import printProgressBar
from apps.data_parser.models import Universe, Area, Variable, Product, Dataset, Subarea, Depth, PlotType, Stat, Plot, KpiInsitu, KpiSat, KpiScore
from apps.data_parser.serializers import AreaSerializer, KpiInsituSerializer, KpiSatSerializer, KpiScoreSerializer, SimpleProductSerializer

###########################################################################################################################################
###########################################################################################################################################
#                               D I F F E R E N T S   F U N C T I O N S   L I N K E D   T O   C O M M A N D                               #
###########################################################################################################################################
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
    process_product_summary('uploads/text', verbose)
    print(line + 'Step 3/6 \t Processing insitu kpi files...')
    process_kpi_insitu_files("uploads/kpi/INSITU", verbose)
    print(line + 'Step 4/6 \t Processing satellite kpi files...')
    process_kpi_sat_files("uploads/kpi/SAT", verbose)
    print(line + 'Step 5/6 \t Processing skill score kpi files...')
    process_kpi_skill_score_files("uploads/kpi/SKILL_SCORE", verbose)
    print(line + 'Step 6/6 \t Preload cache files...')
    update_cache()

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

def setup_database():
    parse_json_area()
    parse_json_univers_var_dset()
    return None

###########################################################################################################################################

def update_cache():
    """
        Return a object containing all hierarchical avalaible filters ()
        
        Here is its struct:
        dict = {
            areas
            |_ universe
                |_ variables
                    |_ datasets
                        |_ products
                            |_ subareas
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

###########################################################################################################################################
###########################################################################################################################################
#                               D I F F E R E N T S   F I L E S   P R O C E S S I N G   O P E R A T I O N S                               #
###########################################################################################################################################
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
          data = extract_plot(filename)
          if type(data) == ErrorMsg:
              files_in_error.append(data.__dict__)
        display = 'Complete '+str(len(files_in_error))+' errors / '+str(index+1)+' files'
        printProgressBar(index + 1, len(files), prefix = 'Progress:', suffix = display, length = 50)
    display_errors(verbose, files_in_error)

###########################################################################################################################################

def process_product_summary(path, verbose):
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

def process_kpi_insitu_files(path, verbose):
    """
        Look for kpi files into designated folder and save them to database (path)

        :param path: the folder to look in
        :return: None.
    """
    
    total_files = sum([len(files) for r, d, files in os.walk(path)])
    if(total_files):
        counter = 0
        files_in_error = []
        printProgressBar(0, total_files, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for dirpath, dirnames, files in os.walk(path):
            if files:
                for filename in files:
                    counter = counter + 1
                    data = extract_kpi_insitu(dirpath, filename)
                    if type(data) == ErrorMsg:
                        files_in_error.append(data.__dict__)
                    display = 'Complete '+str(len(files_in_error))+' errors / '+ str(counter) +' files'
                    printProgressBar(counter, len(files), prefix = 'Progress:', suffix = display, length = 50)
        display_errors(verbose, files_in_error)

###########################################################################################################################################

def process_kpi_sat_files(path, verbose):
    """
        Look for kpi files into designated folder and save them to database (path)

        :param path: the folder to look in
        :return: None.
    """
    files = os.listdir(path)
    if(len(files)):
        files_in_error = []
        printProgressBar(0, len(files), prefix = 'Progress:', suffix = 'Complete', length = 50)
        for index, filename in enumerate(files):
            data = extract_kpi_sat(path, filename)
            if type(data) == ErrorMsg:
                files_in_error.append(data.__dict__)
            display = 'Complete '+str(len(files_in_error))+' errors / '+str(index+1)+' files'
            printProgressBar(index + 1, len(files), prefix = 'Progress:', suffix = display, length = 50)
        display_errors(verbose, files_in_error)

###########################################################################################################################################

def process_kpi_skill_score_files(path, verbose):
    """
        Look for kpi files into designated folder and save them to database (path)

        :param path: the folder to look in
        :return: None.
    """
    files = os.listdir(path)
    if(len(files)):
        files_in_error = []
        printProgressBar(0, len(files), prefix = 'Progress:', suffix = 'Complete', length = 50)
        for index, filename in enumerate(files):
            data = extract_kpi_score(path, filename)
            if type(data) == ErrorMsg:
                files_in_error.append(data.__dict__)
            display = 'Complete '+str(len(files_in_error))+' errors / '+str(index+1)+' files'
            printProgressBar(index + 1, len(files), prefix = 'Progress:', suffix = display, length = 50)
        display_errors(verbose, files_in_error)

###########################################################################################################################################
###########################################################################################################################################
#                                       D I F F E R E N T S   D A T A   E X T R A C T O R S                                               #
###########################################################################################################################################
###########################################################################################################################################

def extract_plot(filename: str):
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
        product, product_created = Product.objects.get_or_create(area=area, name=informations.product, catalogue_url=catalogue_link)
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

def extract_kpi_insitu(dirpath, filename):
    try:
        folder_name_to_area = {'_ARC_': 'arctic', '_BAL_': 'balticsea', '_BS_': 'blacksea', '_GLO_': 'global', '_IBI_': 'ibi', '_MED_': 'medsea', '_NWS_': 'nws'}
        series_name_to_variables = {'Temperature': 'Temperature', 'Salinity': 'Salinity', 'Sea level': 'Sea Surface Height'}
        with open(dirpath + '/' + filename) as json_file:
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
                                content = transform_kpi_content(serie['data'], 1000)
                                period = get_serie_period_infos(content)
                                kpi = KpiInsitu.objects.get_or_create(
                                    what=data['id'], 
                                    content=content, 
                                    product=product, 
                                    variable=variable[0], 
                                    area=area, 
                                    start=period['start'], 
                                    end=period['end'], 
                                    month=period['month'], 
                                    year=period['year']
                                )
            os.remove(dirpath + '/' + filename)
            return None
    except Exception as e:
        return ErrorMsg.from_result(filename, e)

###########################################################################################################################################

def extract_kpi_sat(dirpath, filename):
    try:
        with open(dirpath + '/' + filename) as json_file:
            area = Area.objects.get(name=filename[:-5])
            data = json.load(json_file)
            for i, sat_name in enumerate(data):
                sat_values = data[sat_name]
                content = transform_kpi_content(sat_values, 1000000000)
                period = get_serie_period_infos(content)
                kpi = KpiSat.objects.get_or_create(
                    area=area, 
                    sat=sat_name, 
                    content=content,
                    start=period['start'], 
                    end=period['end'], 
                    month=period['month'], 
                    year=period['year']
                )
            os.remove(dirpath + '/' + filename)
            return None
    except Exception as e:
        return ErrorMsg.from_result(filename, e)

###########################################################################################################################################

def extract_kpi_score(dirpath, filename):
    logger = logging.getLogger('django')
    try:
        with open(dirpath + '/' + filename) as json_file:
            data = json.load(json_file)
            month = int(filename[11:-5])
            year = int(filename[7:-7])
            series_name_to_variables = {'Temperature': 'Temperature', 'Salinity': 'Salinity', 'Sea level': 'Sea Surface Height'}
            for i_a, area_shortname in enumerate(data):
                try:
                    area = Area.objects.get(name__iexact=area_shortname)
                    for i_v, variable_name in enumerate(data[area_shortname]):
                        try:
                            variable = Variable.objects.get(name__iexact=variable_name)
                            for i_d, dataset_name in enumerate(data[area_shortname][variable_name]):
                                try:
                                    dataset = Dataset.objects.get(name__iexact=dataset_name)
                                    for i_p, product_name in enumerate(data[area_shortname][variable_name][dataset_name]):
                                        try:
                                            product = Product.objects.get(name__iexact=product_name)
                                            values = data[area_shortname][variable_name][dataset_name][product_name]
                                            kpi = KpiScore.objects.get_or_create(
                                                month=month,
                                                year=year,
                                                area=area,
                                                variable=variable,
                                                dataset=dataset,
                                                product=product,
                                                MSD_FCST12=values['MSD']['FCST12'],
                                                MSD_HDCT=values['MSD']['HDCT'],
                                                MS_OBS=values['MS_OBS'],
                                                MEAN_OBS=values['MEAN_OBS'],
                                                NB_OBS=values['NB_OBS'],
                                                MSD_CLIM=values['MSD']['CLIM']
                                            )
                                        except Product.DoesNotExist:
                                            error = colored('No matching product', 'red')
                                            logger.warning(error + " : " + product_name)
                                except Dataset.DoesNotExist:
                                            error = colored('No matching dataset', 'red')
                                            logger.warning(error + " : " + dataset_name)
                        except Variable.DoesNotExist:
                            error = colored('No matching variable', 'red')
                            logger.warning(error + " : " + variable_name)
                except Area.DoesNotExist:
                    error = colored('No matching area', 'red')
                    logger.warning(error + " : " + area_shortname_to_name[area_shortname])
            os.remove(dirpath + '/' + filename)
            return None
    except Exception as e:
        return ErrorMsg.from_result(filename, e)

###########################################################################################################################################
###########################################################################################################################################
#                                                   K I N D   O F   U T I L S                                                             #
###########################################################################################################################################
###########################################################################################################################################

def get_query_dict(criteria):
    for key, criterion in criteria.items():
        if isinstance(criterion, str) and key not in ["what", "month"]:
            criteria[key] = get_id_from_name(key, criterion, criteria)
    query_dict = QueryDict('', mutable=True)
    query_dict.update(criteria)
    return query_dict.dict()

###########################################################################################################################################

def parse_json_area():
    with open('area.json') as json_file:
        data = json.load(json_file)
        for a in data:
            area, area_created = Area.objects.get_or_create(name=a['name'], fullname=a['fullname']) 
    return None 

###########################################################################################################################################

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

###########################################################################################################################################

def display_errors(verbose, files_in_error):
    if verbose:
        logger = logging.getLogger('django')
        for wrong in files_in_error:
            error = colored(str(wrong['msg']), 'red')
            filename = wrong['filename']
            logger.warning(error + " : " + filename)

###########################################################################################################################################

def transform_kpi_content(content, input_timestamp_decimal_error):
    """
        Transform array to serie

        [ [timestamp, value], ... ] => [ {x: YYY-mm-dd, y: value} ]

        :param content: a 2 dimensions array
        :param input_timestamp_decimal_error: custom timestamp divider to get some valid timestamp
        :return: serie.
    """
    obj_array = []
    for i_raw, raw in enumerate(content):
        dt_object = datetime.fromtimestamp(raw[0]/input_timestamp_decimal_error)
        obj_array.append({
            'x': dt_object.strftime("%Y-%m-%d"), 
            'y': raw[1]
        })
    return obj_array

###########################################################################################################################################

def get_serie_period_infos(content):
    nb_data = len(content)
    start_dt_object = datetime.strptime(content[0]['x'], "%Y-%m-%d")
    end_dt_object = datetime.strptime(content[nb_data-1]['x'], "%Y-%m-%d")
    month = int(end_dt_object.strftime("%m"))
    year = int(end_dt_object.strftime("%Y"))
    return {
        'start': start_dt_object,
        'end': end_dt_object,
        'month': month,
        'year': year
    }

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
    if key == 'universe':
        return Universe.objects.get(name=criterion).id
    if key == 'variable':
        return Variable.objects.get(name=criterion).id
    if key == 'dataset':
        return Dataset.objects.get(name=criterion).id
    if key == 'product':
        return Product.objects.get(name=criterion).id
    if key == 'subarea':
        product_id = None
        if isinstance(criteria['product'], str):
            product_id = get_id_from_name('product', criteria['product'], criteria)
        else:
            product_id = criteria['product']
        return Subarea.objects.get(name=criterion, product_id=product_id).id
    if key == 'depth':
        return Depth.objects.get(name=criterion).id
    if key == 'stat':
        return Stat.objects.get(name=criterion).id
    if key == 'plot_type':
        return PlotType.objects.get(name=criterion).id

###########################################################################################################################################
###########################################################################################################################################
#                           D I F F E R E N T S   F U N C T I O N S   L I N K E D   T O   V I E W S                                       #
###########################################################################################################################################
###########################################################################################################################################

def get_cached_data():
    data = cache.get('my_data')
    if data == None:
        data = update_cache()
    return data

###########################################################################################################################################

def get_plot(criteria):
    """
        Get plot matching criteria (criteria)

        Criteria should be integers (id send from frontend selectors), but through Open API it's more
        convenient to use criteria names so for Open API string it is.

        :param criteria: some criteria
        :return: Plot.
    """
    q = get_query_dict(criteria)
    try:
        plot = Plot.objects.get(**q) 
        return plot.__dict__
    except:
        return {}

###########################################################################################################################################

def get_product(name):
    """
        Get product matching name

        :param criteria: some criteria
        :return: Plot.
    """
    try:
        rs = Product.objects.get(name__iexact=name) 
        serializer = SimpleProductSerializer(instance=rs, many=False)
        return serializer.data
    except Exception as e:
        return ErrorMsg.from_result(name, e)

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

def get_kpi_insitu(criteria):
    """
        Get Kpi insitu matching criteria (criteria)

        Criteria should be integers (id send from frontend selectors), but through Open API it's more
        convenient to use criteria names so for Open API string it is.

        :param criteria: some criteria
        :return: Kpi.
    """
    try:
        q = get_query_dict(criteria)
        rs = KpiInsitu.objects.filter(**q)
        serializer = KpiInsituSerializer(instance=rs, many=True)
        return serializer.data
    except Exception as e:
        return e

###########################################################################################################################################

def get_kpi_sat(criteria):
    """
        Get Kpi sat matching criteria (criteria)

        Criteria should be integers (id send from frontend selectors), but through Open API it's more
        convenient to use criteria names so for Open API string it is.

        :param criteria: some criteria
        :return: Kpi.
    """
    try:
        q = get_query_dict(criteria)
        rs = KpiSat.objects.filter(**q)
        serializer = KpiSatSerializer(instance=rs, many=True)
        return serializer.data
    except Exception as e:
        return e

###########################################################################################################################################

def get_kpi_score(criteria):
    """
        Get Kpi score matching criteria (criteria)

        Criteria should be integers (id send from frontend selectors), but through Open API it's more
        convenient to use criteria names so for Open API string it is.

        :param criteria: some criteria
        :return: Kpi.
    """
    try:
        q = get_query_dict(criteria)
        rs = KpiScore.objects.filter(**q)
        serializer = KpiScoreSerializer(instance=rs, many=True)
        return serializer.data
    except Exception as e:
        return e

###########################################################################################################################################

def get_scores(criteria):
    """
        Get skill score matching criteria (criteria)

        :param criteria: some criteria
        :return: float.
    """
    try:
        q = get_query_dict(criteria)
        kpis = KpiScore.objects.filter(**q).values()
        return {
            'skill_score': calcul_skill_score(kpis),
            'scatter_index': calcul_scatter_index(kpis),
            'explained_variance': calcul_explained_variance(kpis),
        }
    except Exception as e:
        return e

###########################################################################################################################################
###########################################################################################################################################
#                                                      K P I   S C O R E S   C A L C U L A T I O N S                                      #
###########################################################################################################################################
###########################################################################################################################################
import math  

def calcul_skill_score(kpis):
    try:
        sum_MSD_FCST12_x_NB_OBS = 0
        sum_MSD_CLIM_x_NB_OBS = 0
        sum_NB_OBS = 0
        for i_k, kpi in enumerate(kpis):
            sum_MSD_FCST12_x_NB_OBS = sum_MSD_FCST12_x_NB_OBS + (float(kpi['MSD_FCST12']) * int(kpi['NB_OBS']))
            sum_MSD_CLIM_x_NB_OBS = sum_MSD_CLIM_x_NB_OBS + (float(kpi['MSD_CLIM']) * int(kpi['NB_OBS']))
            sum_NB_OBS = sum_NB_OBS + int(kpi['NB_OBS'])
        return math.sqrt(sum_MSD_FCST12_x_NB_OBS / sum_NB_OBS) / math.sqrt(sum_MSD_CLIM_x_NB_OBS / sum_NB_OBS)
    except Exception as e:
        return {'error': e}

def calcul_scatter_index(kpis):
    try:
        sum_MSD_FCST12_x_NB_OBS = 0
        sum_MS_OBS_x_NB_OBS = 0
        sum_NB_OBS = 0
        for i_k, kpi in enumerate(kpis):
            sum_MSD_FCST12_x_NB_OBS = sum_MSD_FCST12_x_NB_OBS + (float(kpi['MSD_FCST12']) * int(kpi['NB_OBS']))
            sum_MS_OBS_x_NB_OBS = sum_MS_OBS_x_NB_OBS + (float(kpi['MS_OBS']) * int(kpi['NB_OBS']))
            sum_NB_OBS = sum_NB_OBS + int(kpi['NB_OBS'])
        return math.sqrt(sum_MSD_FCST12_x_NB_OBS / sum_NB_OBS) / math.sqrt(sum_MS_OBS_x_NB_OBS / sum_NB_OBS)
    except Exception as e:
        return {'error': e}

def calcul_explained_variance(kpis):
    try:
        sum_MSD_FCST12_x_NB_OBS = 0
        sum__MS_OBS_less_MEAN_OBS_SQR__x_NB_OBS = 0
        sum_NB_OBS = 0
        for i_k, kpi in enumerate(kpis):
            sum_MSD_FCST12_x_NB_OBS = sum_MSD_FCST12_x_NB_OBS + (float(kpi['MSD_FCST12']) * int(kpi['NB_OBS']))
            sum__MS_OBS_less_MEAN_OBS_SQR__x_NB_OBS = sum__MS_OBS_less_MEAN_OBS_SQR__x_NB_OBS + ( (float(kpi['MS_OBS'])-math.pow(float(kpi['MEAN_OBS']),2))  * int(kpi['NB_OBS']))
            sum_NB_OBS = sum_NB_OBS + int(kpi['NB_OBS'])
        return math.sqrt(sum_MSD_FCST12_x_NB_OBS / sum_NB_OBS) / math.sqrt(sum__MS_OBS_less_MEAN_OBS_SQR__x_NB_OBS / sum_NB_OBS)
    except Exception as e:
        return {'error': e}