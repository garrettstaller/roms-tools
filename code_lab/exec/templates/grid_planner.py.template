# Initialization  ![
# system
import os
import sys
import glob
# data
import xarray as xr
import numpy as np
# plotting
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
from matplotlib.widgets import Button
import cartopy.crs as ccrs
# ROMS-Tools ([C]Worthy)
ROMSTOOLS_PATH=f"{os.environ['ROMSTOOLS_ROOT']}"
import roms_tools as rt
from roms_tools import Grid, align_grids, make_nesting_info
from roms_tools import plot_nesting
#                 !]

path = os.getcwd()
start_grid_file = None

mask_file = f"{ROMSTOOLS_PATH}/roms-tools/data/grids/GSHHS/GSHHS_shp/f/GSHHS_f_L1.shp"
topo_file = f"{ROMSTOOLS_PATH}/roms-tools/data/grids/SRTM15_V2.7.nc"
topo_name = 'SRTM15'

verbose = True
channel = True # if True, narrow (1-pixel wide) channels will be closed on mask

min_depth       = 2   # units: meters
vertical_levels = 60  # number of sigma-rho levels

# Presets to trigger generation
lon = None
lat = None
rot = None

# Run src code:
exec(open(ROMSTOOLS_PATH + '/code_lab/src/grid_planner_src.py').read())
