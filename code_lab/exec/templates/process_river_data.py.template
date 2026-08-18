# Imports                    ![

import numpy as np
import xarray as xr
import xesmf
import sys
import copy
import warnings

import pandas as pd
import os
import tqdm
from scipy.spatial import cKDTree

ROMSTOOLS_PATH=f"{os.environ['ROMSTOOLS_ROOT']}"
import roms_tools as rt
#                            !]

'''
process_river_data.py - Garrett Staller | August, 17th 2026

For taking raw GloFAS v4.0 daily river discharge data and translating
into station-based NetCDF format that ROMS and the ROMS-tools river forcing classes can
read in.

From roms-tools Documentation:
1. Configure paths to Dai (optional reference), yearly GloFAS discharge, LDD, and upstream area
2. Identify coastal outflow points from LDD (ldd == 5 sinks adjacent to ocean)
3. Add a supplementary pass for large inland sinks near the coast (e.g. major estuaries)
4. Filter by minimum upstream area and auto-name stations
5. Extract daily discharge at those stations for each year
6. Write a Dai-compatible NetCDF (lat_mou, lon_mou, FLOW, ratio_m2s, riv_name, vol_stn)

'''

# --- Paths    --- #
GLOFAS_DIR   = "/home/projects-gstaller/sbc-nesting/DATASETS/glofas/"
LDD_FILE     = GLOFAS_DIR + "ldd_glofas_v4_0.nc"
UPAREA_FILE  = GLOFAS_DIR + "uparea_glofas_v4_0.nc"

# --- Saving   --- #
# NOTE: Saves to location script is called, so best to run where you want processed river forcing
OUTPUT_FILE = "glofas_v4_rivers.nc"

# --- Params   --- #
START_YEAR = 2020
END_YEAR   = 2020
MIN_UPAREA = 1  # m² = 10 km² — filters tiny coastal drains
MIN_UPAREA_SUPPLEMENT = 10_000e6  # 10,000 km² — only large rivers

# --- Switches --- #
warnings = True

# --- Const.   --- #
EARTH_RADIUS_KM = 6371.0


# ===== Run Source Code ===== #
exec(open(ROMSTOOLS_PATH + '/code_lab/src/process_river_data_src.py').read())
