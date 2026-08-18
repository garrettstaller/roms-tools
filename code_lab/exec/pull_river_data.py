"""
Script to pull river data from EWDS Webserver containing GloFAS Datasets.
This script requires API access: https://ewds.climate.copernicus.eu/how-to-api
"""

# Modules                    ![
import os
import cdsapi
import shutil
#                            !]

# --- USER INPUTS --- #
year = None  # DEFAULT: 2020

# Area
# DEFAULT: Global dataset...
min_lat = None
max_lat = None
min_lon = None
max_lon = None

# Output Name and Location
output_name = "glofas_v4_discharge"
output_path = "/home/projects-gstaller/sbc-nesting/DATASETS/glofas/test/"
#output_path = os.getcwd()

# Preamble                   ![
# Set user inputs for input into API dictionary

default_year = 2020
if year is None:
  print(f"Loading for default year: {default_year}")
  year=default_year

# Prevent incomplete areas
if (min_lat!=None) and (max_lat!=None) and (min_lon!=None) and (max_lon!=None):
  area = [min_lat, min_lon, max_lat, max_lon]
else:
  print("Loading global domain, ensure ALL lat and lon inputs are not NONE")
  area = [90, -180, -90, 180]

# file saving
if output_path is None: output_path=os.getcwd()
data_format = "netcdf"
load_format = "zip"

api_save_name = f"{output_name}_{year}.{load_format}"

#                            !]

# API Retrieval              ![
c = cdsapi.Client(url="https://ewds.climate.copernicus.eu/api")

dataset = "cems-glofas-historical"
request = {
           "system_version":     ["version_4_0"],
           "hydrological_model": ["lisflood"],
           "product_type":       ["consolidated"],
           "timespan":           ["time_mean"],
           "variable":           ["average_river_discharge_in_the_last_24_hours"],
           "year":               year,
           # NOTE: Pull all monthly and daily values for specified year
           "month":              [f"{m:02d}" for m in range(1, 13)],
           "day":                [f"{d:02d}" for d in range(1, 32)],
           "data_format":        data_format,
           "download_format":    load_format,
           "area":               area
          }

client = cdsapi.Client()
client.retrieve(dataset, request).download(api_save_name)

# move file to output
if output_path!=os.getcwd():
  source      = f"{os.getcwd()}/{api_save_name}"
  destination = f"{output_path}"
  print(f"Moving {output_name} to {output_path}")
  shutil.copy(source,destination)
  os.remove(source)

#                            !]
