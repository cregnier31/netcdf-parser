import re
import os
import logging

from apps.data_parser.classes import Informations, ErrorMsg
from apps.data_parser.management.commands._utils import printProgressBar

asup = {
 "BLUE": {
    "Temperature": [
      "temperature",
      "sst",
      "sst_5***",
      "sst_avhrr",
      "sst_insitu",
      "sst_ferrybox",
      "sst_metop",
      "sst_all",
      "sst_bucketship",
      "sst_cmansst",
      "sst_driftingbuoy",
      "sst_eriship",
      "sst_fixedbuoy",
      "sst_hullsensorship",
      "sst_ship",
      "sst_l3",
      "sst_l4",
      "sstl3s",
      "sst_0"
    ],
    "Salinity": [
      "salinity",
      "sss_ferrybox"
    ],
    "Sea Surface Height": [
      "sla",
      "slev_insitu",
      "sla_altimeter",
      "sla_al_al",
      "sla_c2_c2",
      "sla_h2_h2",
      "sla_j1g_j1g",
      "sla_j2_al",
      "sla_j2_c2",
      "sla_j2g_j2g",
      "sla_j2_h2",
      "sla_j2_j1g",
      "sla_j2_j2",
      "sla_j2n_j2n",
      "sla_j3_al",
      "sla_j3_c2",
      "sla_j3_j2g",
      "sla_j3_j2n",
      "sla_j3_j3",
      "sla_j3_s3a",
      "sla_s3a_s3a"
    ],
    "Current Velocity": [
      "eastward_velocity",
      "northward_velocity",
      "speed"
    ],
    "Sea Surface Wave": [
      "VHM0_platform",
      "waves",
      "swh",
      "swh_l3"
    ],
    "Wind": [
      "ascat_a_12km_asc_speed",
      "ascat_a_12km_asc_u",
      "ascat_a_12km_asc_v",
      "ascat_a_12km_des_speed",
      "ascat_a_12km_des_u",
      "ascat_a_12km_des_v",
      "ascat_a_25km_asc_speed",
      "ascat_a_25km_asc_u",
      "ascat_a_25km_asc_v",
      "ascat_a_25km_des_speed",
      "ascat_a_25km_des_u",
      "ascat_a_25km_des_v",
      "ascat_b_12km_asc_speed",
      "ascat_b_12km_asc_u",
      "ascat_b_12km_asc_v",
      "ascat_b_12km_des_speed",
      "ascat_b_12km_des_u",
      "ascat_b_12km_des_v",
      "ascat_b_25km_asc_speed",
      "ascat_b_25km_asc_u",
      "ascat_b_25km_asc_v",
      "ascat_b_25km_des_speed",
      "ascat_b_25km_des_u",
      "ascat_b_25km_des_v"
    ],
    "Mixed Layer Thickness": [
    ]
  },
 "GREEN": {
    "Plankton": [
      "chl-a_modis",
      "chla_modis",
      "chl-a",
      "chl_l3",
      "chl_l4",
      "log10_chlorophyll"
    ],
    "Oxygen": [
      "oxygen"
    ],
    "Primary Production": [
      "spm"
    ]
  },
 "WHITE": {
    "Sea Ice": [
      "seaice-concentration",
      "seaice-drift",
      "seaice-edge",
      "ice_concentration",
      "ice_coverage",
      "ice_thickness"
    ]
  }
}

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

def extract_data(text: str):
    splited = re.split('_', text[:-4])
    datasets = ['bio', 'phy']
    if len(splited)>1:
        for key in datasets:
            if key in splited[1] :
                splited.append(key)
                break
    try:
        return Informations.from_result(text, splited)
    except:
        return ErrorMsg.from_result(text, 'Invalid filename')