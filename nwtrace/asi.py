# Adaptive Stormwater Infrastructure (ASI) Algorithm, adapted from Choi et al. (2011) : 10.1016/j.cageo.2010.07.008
import numpy as np

# Defining globals here (will likely be an object later)

# A set representing outfall-inlet connections
outfall_inlet_connections = {}

# sample DEM from paper
dem = np.array([
    [98, 98, 99, 95, 94, 86, 92, 96, 99, 102],  # y = 1
    [89, 64, 62, 62, 89, 91, 89, 98, 98, 100],  # y = 2
    [85, 53, 51, 59, 80, 90, 88, 82, 92, 96],   # y = 3
    [89, 84, 72, 64, 67, 70, 80, 87, 94, 94],   # y = 4
    [84, 85, 92, 96, 94, 90, 81, 79, 81, 92],   # y = 5
    [72, 82, 87, 92, 92, 83, 78, 84, 76, 90],   # y = 6
    [64, 64, 66, 69, 79, 88, 84, 78, 84, 88],   # y = 7
    [72, 80, 77, 69, 62, 70, 83, 79, 78, 84],   # y = 8
    [71, 79, 80, 80, 77, 64, 62, 67, 70, 76],   # y = 9
    [55, 53, 61, 80, 80, 80, 70, 62, 66, 67],   # y = 10
], dtype=np.float32)

# placeholders for rasters
# D8 flow direction raster
d8_dir = np.empty()
# D8 flow accumulation raster
d8_accum = np.empty()
# Watershed assignment raster
d8_watershed = np.empty()

# set option for watershed type (Options: "OUTLET", "INLET", "OUTFALL")
watershed = "OUTFALL"

# Returns cell coordinates for cells that drain into (x, y) of the D8 flow direction raster
def get_d8_neighbours(x, y) -> list:

    # List of tuples
    neighbours = []

    # find inflow to (x,y)

    return neighbours

# Returns the cell coordinates for inlets that are connected to outfall 'id' in the connectivity table
def get_connecting_inlets(id: str) -> list:

    # List of tuples
    inlets = []

    # traverse connectivity table for connecting inlets to outfall 'id'

    return inlets

def recursive_asi(x, y, id: str, o_od: str = None):
    # x and y are the locations of 'seed' cells from which to initiate the recursive process
    # These are edge cells, or inlets with the 'undefined' indicator
    # Each seed cell will need to have a unique ID

    # ------------------------
    # The DEM will need to be modified to create intentional sinks at the locations of inlets
    # These sinks will then be given an indicator for use in the procedure

    # for every neighbour of (x,y)
    for (i,j, o_id) in get_d8_neighbours(x, y):
        # call this function on the current cell, id is propagated for assigning the watershed
        recursive_asi(i,j,id,o_id)

        # at the inlet cell, set to the current value plus the accumulated flow to cell (i,j) - +1 for the flow to this cell
        d8_accum[x, y] = d8_accum[x, y] + d8_accum[i, j] + 1

    # If cell (x,y) is an outfall:
    if o_id is not None and "OF" in o_id:
        for (p,q,i_id) in get_connecting_inlets(x,y):
            
            # placeholder for a potentially better system later
            match watershed:
                case "OUTLET":
                    w_id = id
                case "OUTFALL":
                    w_id = o_id
                case "INLET":
                    w_id = i_id

            recursive_asi(p, q, w_id)

            d8_accum[x, y] = d8_accum[x, y] + d8_accum[p, q] + 1
    
    # assign watershed value
    d8_watershed[x, y] = id