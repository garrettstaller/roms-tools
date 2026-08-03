# --- FUCNTIONS --- #

# GUI                        ![

# Placing of grid by user clicks on interactive plot
current_grid = {}
current_boundary = {'artists': []}
                    
# Global history of graphing params for overwriting of child
current_params   = {'ix':  None if lon is None else lon, 
                    'iy':  None if lat is None else lat, 
                    'rot': None if rot is None else rot,
                    'nx':  None, 'ny': None}

def add_grid(event,parent_grid,res):
  global ax,fig

  # MOUSE INPUTS ON PLOT #
  if (not isinstance(event,str)) and (event.inaxes == ax):  # check for posiitonal click
    print('mouse-click detected')
    # NOTE: from action, get inputs to get nearest indices
    ix, iy = ccrs.PlateCarree().transform_point(event.xdata, event.ydata, ax.projection)
    # update params
    current_params['ix'] = ix
    current_params['iy'] = iy
    print(f'\n Centering at: lon={ix:.4f}, lat={iy:.4f}')
  # TEXT BOX INPUTS #
  elif (isinstance(event,str)) and (event=='apply'):
    print('text-input detected')
    print('Updating grid...')
  elif (isinstance(event,str)) and (event=='bypass'):
    print(f'Plotting Initial Grid at {lon},{lat}')
  else:  # this return lets other clicks outside of toolbox or main figure be ignored...
    return

  # Ensure a position has been set
  if (current_params['ix'] is None) or (current_params['iy'] is None):
    print('Either click where you would like your grid, or provide both lat and lon')
    return

  # remove previous boundary lines
  for i in range(len(ax.lines) - n_lines_original):
    ax.lines[n_lines_original].remove()
  current_boundary['artists'] = []

  dx_grid,dy_grid = res,res

  grid_params = {
                 "nx":parent_grid.nx if current_params['nx'] is None else current_params['nx'],
                 "ny":parent_grid.ny if current_params['ny'] is None else current_params['ny'],
                 "size_x":int(parent_grid.nx*dx_grid) if current_params['nx'] is None else int(current_params['nx']*dx_grid),
                 "size_y":int(parent_grid.ny*dy_grid) if current_params['ny'] is None else int(current_params['ny']*dy_grid),
                 "center_lat":current_params['iy'],
                 "center_lon":current_params['ix'],
                 "rot":0 if current_params['rot'] is None else current_params['rot'],
                 "N":vertical_levels,
                 "verbose":False,
                 "close_narrow_channels":channel,
                 "hmin":min_depth
                }

  new_grid = Grid(**grid_params)

  trans = rt.plot.get_projection(new_grid.ds['lon_rho'],new_grid.ds['lat_rho'])

  rt.plot._add_boundary_to_ax(ax,
                              new_grid.ds['lon_rho'],
                              new_grid.ds['lat_rho'],
                              trans=trans,
                              with_dim_names=False)

  # capture ALL new artists added
  artists_before = set(ax.lines + ax.collections + ax.patches)
  n_lines_before = len(ax.lines)
  rt.plot._add_boundary_to_ax(ax,
                              new_grid.ds['lon_rho'],
                              new_grid.ds['lat_rho'],
                              trans=trans)
  ax.plot(current_params['ix'],current_params['iy'],transform=ccrs.PlateCarree(),color='red')
  n_lines_after = len(ax.lines)  # must come AFTER the call
  current_boundary['artists'] = ax.lines[n_lines_before:]

  fig.canvas.draw()
  fig.canvas.flush_events()

  current_grid['grid'] = new_grid
  print('Ready for more edits... (right-click when finished)')

# Store resulting grid in global dictionary
result = {}
def on_click(event):
  # updates current_grid dictionary each click
  if event.button==1:
    add_grid(event,parent_grid,res)
  # Exit click, update the result dictionary with a finished grid
  elif event.button==3:
    result['grid'] = current_grid.get('grid')
    # prevent finished grit if user has not placed one...
    if result['grid'] is None: print('You must actually plot a grid to nest... try again')
    else: plt.close()
   
def submit_text(expression,param):
  # Silently check for float-convertible input
  try:
    if float(expression)==current_params[param]: return  # ignore repeated values
    # simply update dictionary
    current_params[param] = float(expression)
    print(f'Updated {param}: {current_params[param]}')
  except:
    print('Please input a float-like value not a string')
    return

# 'apply' updates made with submit text function to plotted grid
def on_apply(event):
  add_grid('apply',parent_grid,res)


#                            !]

# --- BEGIN --- #

# Parent Grid                ![
ngrids = 0

# Read parent grd
if (start_grid_file is not None) or (ngrids!=0):
  # grab existing grid and add it to class
  grid_path = f"{path}/{start_grid_file}" if ngrids==0 else f"{path}/{new_grid_file}"
  print(f'Starting with parent grid in {grid_path}')
  parent_grid = Grid(filename=grid_path)
  parent_ready = True
# Build parent grd
else:
  print('No starting grid provided, bulding parent...')
  # Get dimensions and resoltion
  user_input = input("Desired dimensions in XI and ETA and resolution: < nx ny dx/dy>: " )
  user_input = np.fromstring(user_input,dtype=float,sep=' ')
  nx_grid,ny_grid,res = int(user_input[0]),int(user_input[1]),user_input[2]
  grid_size_x,grid_size_y = int(nx_grid*res*3),int(ny_grid*res*3)
  grid_params = {
                 "nx":nx_grid,
                 "ny":ny_grid,
                 "size_x":grid_size_x,
                 "size_y":grid_size_y,
                 # NOTE: HARDCODED ALERT!
                 "center_lat":31.5,
                 "center_lon":-123.7,
                 "rot":32,
                 "N":vertical_levels,
                 "verbose":verbose,
                 "close_narrow_channels":channel,
                 "hmin":min_depth
                }
  parent_grid = Grid(**grid_params)
  parent_ready = False  # used in nesting loop to allow for adjustments to base parent grid before nesting

#                            !]

if parent_ready: print("Parent ready, let's Nest!")
else: print('Refine Parent Grid...')

# Nesting Loop               ![

while True:  # Infinite loop dependent on 'progress_input' at end

  # if not the first time, overwrite parent grid
  if ngrids!=0:
    grid_path = f"{path}/{new_grid_file}"
    parent_grid = Grid(filename=grid_path)
    print(f'\n Nesting into {grid_path}')

  # Get user input for resolution of next grid
  if (parent_ready) or (ngrids!=0):
    user_input = input("Desired resolution (units of km!): " )
    res = np.fromstring(user_input,dtype=float,sep=' ')[0]
  
  # set interactive text
  parent_grid.plot()
  ax = plt.gca()   # axes
  fig = plt.gcf()  # figure
  n_lines_original = len(ax.lines)

  # if positions have been declared in /exec configuration script make an initial plot
  if (ngrids==0) and ((lon is not None) and (lat is not None)):
    add_grid('bypass',parent_grid,res)
  
  # GUI Panels
  # Textboxs:
  applybox = fig.add_axes((0.1, 0.20, 0.2, 0.075))
  apply_btn = Button(applybox, 'Apply')
  # sizes
  nxbox        = fig.add_axes((0.08, 0.70, 0.2, 0.075))
  text_box_nx  = TextBox(nxbox, "nx", textalignment="center")
  nybox        = fig.add_axes((0.08 , 0.60, 0.2, 0.075))
  text_box_ny  = TextBox(nybox, "ny", textalignment="center")
  # rotation
  rotbox       = fig.add_axes((0.08, 0.50, 0.2, 0.075))
  text_box_rot = TextBox(rotbox, "Rotation", textalignment="center")
  # postitions
  lonbox       = fig.add_axes((0.08, 0.40, 0.2, 0.075))
  text_box_lon = TextBox(lonbox, "Longitude", textalignment="center")
  latbox       = fig.add_axes((0.08, 0.30, 0.2, 0.075))
  text_box_lat = TextBox(latbox, "Latitude", textalignment="center")

  # Inputs
  fig.canvas.mpl_connect('button_press_event', on_click)
  apply_btn.on_clicked(on_apply)
  text_box_nx.on_submit(lambda expr:  submit_text(expr, 'nx'))
  text_box_ny.on_submit(lambda expr:  submit_text(expr, 'ny'))
  text_box_rot.on_submit(lambda expr: submit_text(expr, 'rot'))
  text_box_lon.on_submit(lambda expr: submit_text(expr, 'ix'))
  text_box_lat.on_submit(lambda expr: submit_text(expr, 'iy'))
  plt.show()
  child_grid = result.get('grid')

  # Update topography?
  update_topo = True if input('Update topography from low-res ETOP5 Dataset? (Y/N): ')=='Y' else False
  if update_topo:
    # list all available datasets to choose from or just pick one provided
    if (os.path.isfile(topo_file)) and ('.nc' in topo_file):
      print(f'Updating topography with: {topo_file}')
      # Make copy of grid using existing params
      grid_params = {
                    "nx":child_grid.nx,
                    "ny":child_grid.ny,
                    "size_x":child_grid.size_x,
                    "size_y":child_grid.size_y,
                    "center_lat":child_grid.center_lat,
                    "center_lon":child_grid.center_lon,
                    "rot":child_grid.rot,
                    "N":child_grid.N,
                    "verbose":False,
                    "close_narrow_channels":channel,
                    "hmin":min_depth
                    }
      # and append new topo source...
      child_grid = Grid(
                        **grid_params,
                        topography_source = {"name": topo_name,
                                             "path": topo_file}
                       )   
    else: print('Cannot find NetCDF File in "topo_file" variable, ignoring topography update...')

  # Update land mask?
  update_mask = True if input('Update land mask with hi-res GSHHS? (Y/N): ')=='Y' else False
  if update_mask:
    # check file existence
    if (os.path.isfile(mask_file)) and ('.shp' in mask_file):
      print(f'Updating mask with: {mask_file}')
      child_grid.update_mask(
                             mask_shapefile=mask_file,
                             close_narrow_channels=channel,
                             verbose=False
                            )
    else: print('Cannot find NetCDF File in "mask_file" variable, ignoring mask update...')

  # Align with parent_grid
  print('Aligning parent and child grid indices...')
  child_grid = align_grids(parent_grid=parent_grid, child_grid=child_grid, verbose=verbose)

  # Saving procedure
  new_grid_file = input('Provide name of child grid output: ')
  if new_grid_file=='q': break
  if '.nc' not in new_grid_file: new_grid_file=new_grid_file+'.nc'
  child_grid.save(filepath=f"{path}/{new_grid_file}")
  
  # Exiting
  progress_input = input('Continue nesting? (Y/N): ')
  if progress_input=='N': break

  # if conitnuing, update number of grids and clear dictionaries
  ngrids+=1
  current_params   = {'ix': None, 'iy': None, 'rot': None, 'nx': None, 'ny': None}

#                            !]


