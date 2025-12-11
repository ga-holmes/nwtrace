# Adaptive Stormwater Infrastructure (ASI) Algorithm, adapted from Choi et al. (2011) : 10.1016/j.cageo.2010.07.008
import numpy as np

# Defining globals here (will likely be an object later)

# A set representing outfall-inlet connections
inlet_connections = {
    "OF1": ["IN1"]
}

outfall_locations = {
    (8,1): "OF1"
}

inlet_locations = {
    "IN1": (2,2)
}

# d8 direction to vector map for whitebox tools encoding
direction_map = {
    0:   (0,0),   # Sink
    1:   (-1,1),  # NE
    2:   (0,1),   # E
    4:   (1,1),    # SE
    8:   (1,0),     # S
    16:  (1,-1),    # SW
    32:  (0,-1),     # W
    64:  (-1,-1),    # NW
    128: (-1,0)      # N
}

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

# create the outfall mask that indicates the locations of outfalls in the dataset
outfall_mask = np.zeros_like(dem)

for r,c in outfall_locations.keys():
    outfall_mask[r,c] = 1

# create an inlet mask that indicates the locations of inlets in the dataset so they can be excluded from the list of seed cells
inlet_mask = np.zeros_like(dem)

for r,c in inlet_locations.keys():
    inlet_mask[r,c] = 1

# placeholders for rasters
# D8 flow direction raster
d8_dir = np.empty()
# D8 flow accumulation raster
d8_accum = np.empty()
# Watershed assignment raster
d8_watershed = np.empty()

# set option for watershed type (Options: "OUTLET", "INLET", "OUTFALL")
watershed = "OUTFALL"

# global raster extent maximums
max_rows = np.max(dem,axis=0)
max_cols = np.max(dem,axis=1)

# Returns cell coordinates for cells that drain into (x, y) of the D8 flow direction raster
def get_d8_neighbours(r, c) -> list:

    # List of tuples
    neighbours = []

    # this is a static list, i.e. always the same
    all_neighbours = [
        (-1,-1), (-1,0), (-1,1),
        (0,-1),          (0,1),
        (1,-1),  (1,0),  (1,1)
    ]

    # for all cells
    for dr, dc in all_neighbours:

        nr = r + dr
        nc = c + dc

        # Skip cells outside raster
        if nr < 0 or nc < 0 or nr or nr > max_rows or nr > max_cols:
            continue

        n = d8_dir[nr, nc]

        # get the vector value for the d8 number at n
        dn = direction_map[n]

        # check for inflow to (x,y)
        if dn == ((-1 * dr), (-1 * dc)):
            
            o_id = None
            # check if it's an outfall, if yes, assign outfall ID
            if outfall_mask[dn] == 1:
                o_id = outfall_locations[dn]

            neighbours.append((nr, nc, o_id))

    return neighbours

def get_seed_cells(d8_dir, to_exclude = None):
    
    if to_exclude != None:
        sink_mask = (d8_dir == 0) & (~to_exclude)
    else: 
        sink_mask = (d8_dir == 0)

    sink_cells = [tuple(rc) for rc in np.argwhere(sink_mask)]

    return sink_cells


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
    if o_id is not None:
        for i_id in inlet_connections[o_id]:

            p, q = inlet_locations[i_id]

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

# testing the whole thing
