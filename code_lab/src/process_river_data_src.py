'''
process_river_data_src.py - Garrett Staller | August, 17th 2026

Source code to set_river_frc.py. Code has been taken from [C]Worthy documentation pages
Notebook example for taking raw GloFAS v4.0 daily river discharge data and translating
into station-based NetCDF format that ROMS and the ROMS-tools river forcing classes can
read in.

User inputs are done via the complementary executable script in /exec

From roms-tools Documentation:

Workflow
1. Configure paths to Dai (optional reference), yearly GloFAS discharge, LDD, and upstream area
2. Identify coastal outflow points from LDD (ldd == 5 sinks adjacent to ocean)
3. Add a supplementary pass for large inland sinks near the coast (e.g. major estuaries)
4. Filter by minimum upstream area and auto-name stations
5. Extract daily discharge at those stations for each year
6. Write a Dai-compatible NetCDF (lat_mou, lon_mou, FLOW, ratio_m2s, riv_name, vol_stn)

'''
if not warnings: warnings.filterwarnings("ignore")

# Functions                  ![

# --- Base --- #
def haversine_km(lon1, lat1, lon2, lat2):
    """Great circle distance in km. Inputs in degrees. Vectorized."""
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def make_default_name(lat, lon):
    """Coordinate-based river name for unmatched outflow points."""
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"GloFAS_{abs(lat):.2f}{ns}_{abs(lon):.2f}{ew}"

LDD_DIRECTION = {
                 1:(+1,-1), 2:(+1, 0), 3:(+1,+1),
                 4:( 0,-1), 5:( 0, 0), 6:( 0,+1),
                 7:(-1,-1), 8:(-1, 0), 9:(-1,+1),
                }

# --- Step 1 --- #
def update_stencil_sum(ocean_mask):
    """3x3 stencil sum — Fan's exact implementation."""
    stencil = np.zeros(ocean_mask.shape)
    for nlat in range(3):
        ilat_last = -(2 - nlat) if (2 - nlat) != 0 else None
        for nlon in range(3):
            ilon_last = -(2 - nlon) if (2 - nlon) != 0 else None
            stencil[1:-1, 1:-1] += ocean_mask[nlat:ilat_last, nlon:ilon_last]
    return stencil

#                            !]

# STEP 1: Find Coastal Outflow Points from LDD
# NOTE: ldd==5; therefore, if a sink sits on water after expansion of ocean-land
#       mask it is converted to ocean. Neighboring cells are iteratively promoted
#       to land cells until sink sits on the land-ocean interface.
# EXPAND                     ![
print("Loading GloFAS LDD...")
ds_ldd  = xr.open_dataset(LDD_FILE)
ldd_var = next((v for v in ds_ldd.data_vars if 'ldd' in v.lower()), None)
ldd     = ds_ldd[ldd_var].values
lats    = ds_ldd['lat'].values if 'lat' in ds_ldd.coords else ds_ldd['latitude'].values
lons    = ds_ldd['lon'].values if 'lon' in ds_ldd.coords else ds_ldd['longitude'].values
ds_ldd.close()
print(f"LDD: {ldd.shape}")

print("Finding outflow points")
ocean_mask = np.isnan(ldd)
n_updates  = 1
iterations = 0
while n_updates > 0:
    n_updates   = 0
    stencil_sum = update_stencil_sum(ocean_mask)
    for jj in range(len(lats)):
        for ii in range(len(lons)):
            if (ldd[jj,ii]==5) and (not ocean_mask[jj,ii]) and (stencil_sum[jj,ii]>0):
                ocean_mask[jj,ii] = True
                n_updates += 1
    iterations += 1

outflow_mask = (ldd == 5) & (stencil_sum > 0)
j_idx, i_idx = np.where(outflow_mask)
print(f"Found {len(j_idx):,} outflow points after {iterations} iterations")


#                            !]

# Step 2: Supplementary Pass for Large near-coast sinks
# NOTE: The specification of MIN_AREA_SUPPLEMENT controls the area near the coast
#       that large upstream-area sinks are retained.
# EXPAND                     ![
ds_up   = xr.open_dataset(UPAREA_FILE)
up_var  = next((v for v in ds_up.data_vars if 'uparea' in v.lower() or 'area' in v.lower()), None)
uparea  = ds_up[up_var].values

print("\nSupplementary pass: finding large rivers missed by ocean-adjacency filter...")

# All ldd==5 sinks with large upstream area not already captured
all_sink_j, all_sink_i = np.where((ldd == 5) & ~outflow_mask)
sink_upareas = np.array([uparea[j, i] for j, i in zip(all_sink_j, all_sink_i)])
large_mask = sink_upareas >= MIN_UPAREA_SUPPLEMENT
all_sink_j = all_sink_j[large_mask]
all_sink_i = all_sink_i[large_mask]
print(f"  {len(all_sink_j):,} large sinks not captured by primary method")

# Build cKDTree on ocean cell coordinates

ocean_j, ocean_i = np.where(np.isnan(ldd))
ocean_lats_deg = lats[ocean_j]
ocean_lons_deg = lons[ocean_i]
ocean_coords = np.column_stack([np.radians(ocean_lats_deg), np.radians(ocean_lons_deg)])
tree = cKDTree(ocean_coords)

# Query distance to nearest ocean cell for each large sink
sink_lats_deg = lats[all_sink_j]
sink_lons_deg = lons[all_sink_i]
sink_coords = np.column_stack([np.radians(sink_lats_deg), np.radians(sink_lons_deg)])
dists_chord, _ = tree.query(sink_coords)
dists_km = 2 * 6371.0 * np.arcsin(np.clip(dists_chord / 2, 0, 1))

within_100km = dists_km <= 100.0
supp_j = all_sink_j[within_100km]
supp_i = all_sink_i[within_100km]
print(f"  {len(supp_j):,} large rivers within 100km of coast added")
for k in range(len(supp_j)):
    print(f"    {make_default_name(lats[supp_j[k]], lons[supp_i[k]])}  "
          f"uparea={uparea[supp_j[k], supp_i[k]]/1e6:.0f} km²  "
          f"dist={dists_km[within_100km][k]:.1f} km")

# Merge with primary outflow points
j_idx = np.concatenate([j_idx, supp_j])
i_idx = np.concatenate([i_idx, supp_i])
print(f"Total outflow points after supplement: {len(j_idx):,}")


#                            !]

# Step 3: Filter by Upstream Area and Name Stations
# NOTE: Application of MIN_UPAREA and storing of results as vol_stn for sorting
#       by river size
# EXPAND                     ![
print("\nLoading upstream area...")

up_lats = ds_up['latitude'].values if 'latitude' in ds_up.coords else ds_up['lat'].values
up_lons = ds_up['longitude'].values if 'longitude' in ds_up.coords else ds_up['lon'].values
ds_up.close()
print(f"Upstream area: {uparea.shape}  max={np.nanmax(uparea)/1e6:.0f} km²")

# Get upstream area at each outflow point
uparea_at_outflows = np.array([
    uparea[j_idx[k], i_idx[k]]
    if not np.isnan(uparea[j_idx[k], i_idx[k]]) else 0.0
    for k in range(len(j_idx))
])

# Filter by minimum upstream area, currently no filter
keep_mask    = uparea_at_outflows >= MIN_UPAREA
outflow_lats = lats[j_idx][keep_mask]
outflow_lons = lons[i_idx][keep_mask]
uparea_out   = uparea_at_outflows[keep_mask]

print(f"After MIN_UPAREA={MIN_UPAREA/1e6:.0f} km² filter: "
      f"{len(outflow_lats):,} outflow points")

# Auto-name all outflow points by coordinates
names = np.array([make_default_name(lat, lon)
                  for lat, lon in zip(outflow_lats, outflow_lons)])


#                            !]

# Step 4: Extract Daily Discharge at Outflow Points
# NOTE: Records 24 hour discharge averages for each of the located rivers
# EXPAND                     ![
jj = np.array([np.argmin(np.abs(lats - lat)) for lat in outflow_lats])
ii = np.array([np.argmin(np.abs(lons - lon)) for lon in outflow_lons])

times_list = []
flow_list  = []

for yr in range(START_YEAR, END_YEAR + 1):
    fpath = os.path.join(GLOFAS_DIR, f"glofas_v4_discharge_{yr}.nc")

    ds = xr.open_dataset(fpath)
    if 'latitude' in ds.dims: ds = ds.rename({'latitude':'lat','longitude':'lon'})
    if 'valid_time' in ds.dims: ds = ds.rename({'valid_time':'time'})

    # Read entire year into memory at once — avoids per-timestep disk reads
    dis_np = ds['avg_dis'].values          # (n_days, lat, lon)
    t_vals = ds['time'].values           # (n_days,)
    ds.close()

    # Extract all outflow points for all days at once
    flow_yr = np.maximum(dis_np[:, jj, ii], 0.0)  # (n_days, n_stations)

    times_list.append(t_vals)
    flow_list.append(flow_yr)

    if yr % 5 == 0:
        print(f"  {yr}")

times = np.concatenate(times_list)                 # (n_days_total,)
flow  = np.concatenate(flow_list, axis=0)          # (n_days_total, n_stations)
print(f"Output: {len(times)} days x {flow.shape[1]:,} stations")

#                            !]

# Step 5: Write to NetCDF
# NOTE: Output follows station names laid out by Dai & Trenbeth
# EXPAND                     ![
print(f"\nWriting {OUTPUT_FILE}...")

ds_out = xr.Dataset({
    'lat_mou':   ('station', outflow_lats.astype('f4')),
    'lon_mou':   ('station', outflow_lons.astype('f4')),
    'FLOW':      (['time', 'station'], flow.astype('f4')),
    'ratio_m2s': ('station', np.ones(len(outflow_lats), dtype='f4')),
    'vol_stn':   ('station', uparea_out.astype('f4')),
    'riv_name':  ('station', names),
    'time':      ('time', times),  # native datetime64 — CF compliant
})

encoding = {
    'FLOW': {'zlib': True, 'complevel': 4, 'dtype': 'float32'},
    'time': {'units': 'days since 1979-01-01', 'calendar': 'gregorian'},
}

ds_out['lat_mou'].attrs   = {'units': 'degrees_north',
                              'long_name': 'river mouth latitude'}
ds_out['lon_mou'].attrs   = {'units': 'degrees_east',
                              'long_name': 'river mouth longitude'}
ds_out['FLOW'].attrs      = {'units': 'm3 s-1',
                              'long_name': 'river discharge',
                              'missing_value': 1e+20}
ds_out['ratio_m2s'].attrs = {'units': '1',
                              'long_name': 'spatial ratio (set to 1.0)'}
ds_out['vol_stn'].attrs   = {'units': 'm2',
                              'long_name': 'upstream drainage area',
                              'comment': 'used for sorting rivers by size'}
ds_out['time'].attrs      = {'long_name':
                              'time '}
ds_out.attrs = {
    'title':  'GloFAS v4.0 river discharge in Dai & Trenberth station format',
    'source': ('GloFAS v4.0: Harrigan S et al. (2020) ESSD '
               'doi:10.5194/essd-12-2043-2020; '
               'Grimaldi S et al. (2022) JRC Technical Report JRC131349.'),
    'method': ('Outflow points identified using iterative ocean mask '
               'expansion from GloFAS LDD (ldd==5, adjacent to ocean NaN); Following method from Fan Yang'
               f'Min upstream area: {MIN_UPAREA/1e6:.0f} km². '
               'All stations auto-named by coordinates GloFAS_LAT_LON. '
               'vol_stn = upstream drainage area (m²) used for sorting.'),
}

#OUTPUT_FILE = '/anvil/projects/x-ees250129/Datasets/Rivers/glofas_v4_rivers_daily.nc'

ds_out.to_netcdf(OUTPUT_FILE)
print(f"Done. {len(outflow_lats):,} stations -> {OUTPUT_FILE}")
print(f'\nUsage in roms-tools:')
print(f'  source = {{"name": "GLOFAS", "path": "{OUTPUT_FILE}"}}')


#                            !]
