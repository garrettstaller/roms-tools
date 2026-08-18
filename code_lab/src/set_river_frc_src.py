'''
set_river_frc_src.py - Garrett Staller | August 18th, 2026

Source code for 'set_river_frc.py' executable in ../exec.

'''

# Insert rivers in grid      ![

grid = Grid(filename=GRID_PATH)

# get all river info for time range
# NOTE: Built for daily data over entire year
start_time = datetime(START_YEAR,1,1)
end_time   = datetime(END_YEAR,12,31)

river_forcing = RiverForcing(
                             grid=grid,
                             start_time=start_time,
                             end_time=end_time,
                             convert_to_climatology="never",  # "never", "always", or "if_any_missing" (default)
                             source = {
                                       "name": "GLOFAS",  # NOTE: hardcoded for GLOFAS
                                       "path": GLOFAS_PATH
                                       }
                             )

#                            !]

print('\n Plotting river indices onto interactive plot for viewing...')
# Plot River Indices         ![

fig, ax = plt.subplots(figsize=(6, 6))

# Dimension Arrays
lon = river_forcing.grid.ds.lon_rho.values
lat = river_forcing.grid.ds.lat_rho.values

# Mask
ax.contourf(lon, lat, grid.ds.mask_rho.values, cmap="Grays", alpha=0.4)

# River locations
river_cells = river_forcing.ds["river_index"].values > 0
eta_rho, xi_rho = np.where(river_cells)
ax.scatter(
           lon[eta_rho, xi_rho],
           lat[eta_rho, xi_rho],
           s=6,
           marker=".",
           color="tab:red",
          )

ax.set_title(f"All GloFAS river injection cells in {GRID_NAME}")
ax.set_xlabel("longitude")
ax.set_ylabel("latitude")

plt.show(block=False)
#                            !]

if input('Would you like to save forcing? (Y/N): ')=='Y': river_forcing.save(filepath=f'{os.getcwd()}/{OUTPUT_NAME}')


