from termcolor import colored
from django.core.cache import cache
from django.core import serializers
from django.utils import timezone
from apps.data_parser.classes import Informations, ErrorMsg
from apps.data_parser.management.commands._utils import printProgressBar
from apps.data_parser.models import Universe, Area, Variable, Product, Dataset, Subarea, Depth, PlotType, Stat, Plot, KpiInsitu, KpiSat, KpiScore
from apps.data_parser.serializers import AreaSerializer, KpiInsituSerializer, KpiSatSerializer, KpiScoreSerializer, SimpleProductSerializer
import urllib, os, sys
import json
from glob import glob
import urllib.request
import requests
from bs4 import BeautifulSoup
from datetime import date
import configparser as ConfigParser
from os.path import dirname
sys.path.append(dirname(__file__))

###########################################################################################################################################
###########################################################################################################################################


def get_url_paths(url, ext='', params={}):
    response = requests.get(url, params=params)
    if response.ok:
        response_text = response.text
    else:
        return response.raise_for_status()
    soup = BeautifulSoup(response_text, 'html.parser')
    parent = [url + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]
    return parent

def response(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def get_kpi_instac(verbose, list_kpi="kpi2"):

    today = date.today()
    year = today.strftime("%Y")
    month= today.strftime("%m")
    dateval=year+month
    list_kpi=[list_kpi]
    list_reg = ["ARC", "BAL", "BS", "GLO", "IBI", "MED", "NWS"]
    product = {}
    IniRead = ConfigParser.ConfigParser()
    IniRead.read(os.path.expanduser('kpi_settings.cfg'))
    product = IniRead.get('dict', 'product')

    for kpi in list_kpi:
        for reg in list_reg:
            for list_reg in product[reg]:
                frame = 'INSITU_'+reg+list_reg+'/'+reg.lower()+'_multiparameter_nrt/'+kpi+'/'
                url = 'http://www.socib.es/users/protllan/cmems-instac-kpis/data/datasets/'\
                        +frame+dateval+'/'
                #download_path="/homelocal-px/px-116/sauvegarde/cregnier/GitHub_rep/PQD/netcdf-parser/uploads/kpi/INSITU/"+frame
                download_path="./uploads/kpi/INSITU/"+frame
                if not os.path.exists(download_path) : os.makedirs(download_path)
                ext = 'json'
                print (url)
                result = get_url_paths(url, ext)
                print ( "--- results : %s " %(result))
                for file in result:
                    name_file=os.path.basename(file)
                    print(file)
                    print (download_path+name_file)
                    try :
                        response = urllib.request.urlopen(file)
                        with open(download_path+name_file, 'wb') as out_file:
                            data = response.read() # a `bytes` object
                            out_file.write(data)
                        #urllib.urlretrieve(file, download_path+name_file)
                    except : 
                        print ("problem get file "+file)
                        sys.exit(1)
                    ## Exemple de lecture du json
                    json_file=glob(download_path+name_file)
                    if os.path.isfile(json_file[0]):
                        with open(json_file[0]) as dom_catalog:
                            dom_data = json.load(dom_catalog)
                            for key in dom_data.keys():
                                print(dom_data[key])
