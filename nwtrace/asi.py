# Adaptive Stormwater Infrastructure (ASI) Algorithm, adapted from Choi et al. (2011) : 10.1016/j.cageo.2010.07.008
import numpy as np
from pathlib import Path
import rasterio as rio

# Defining globals here (will likely be an object later)

class ASI:

    def __init__(
        self,
        d8_flow_direction_raster,
        inlet_connections,
        outfall_locations,
        inlet_locations,
        watershed_type = "OUTFALL",
        direction_map = None

    ) -> None:

        # load d8 file using rasterio or assign
        if isinstance(d8_flow_direction_raster, (str, Path)):
            with rio.open(d8_flow_direction_raster) as src:
                self.d8_dir = src.read(1)
        elif isinstance(d8_flow_direction_raster, np.ndarray):
            self.d8_dir = d8_flow_direction_raster
        elif isinstance(d8_flow_direction_raster, (rio.io.DatasetReader)):
            self.d8_dir = d8_flow_direction_raster.read(1)
        else:
            raise ValueError(
                "'d8_flow_direction_raster' must be a valid file path or a numpy array or a rasterio DatasetReader."
            )

        # TODO: May update this to a better system that gets all this info from a single array or table such as in the Choi paper
        self.inlet_connections = inlet_connections
        self.outfall_locations = outfall_locations
        self.inlet_locations = inlet_locations

        self.watershed_type = watershed_type
        
        if direction_map == None:
            # d8 direction to vector map for whitebox tools encoding
            self.direction_map = {
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

        self.max_rows = np.shape(self.d8_dir)[0]
        self.max_cols = np.shape(self.d8_dir)[1]

        # initialize empty arrays for watershed and accumulation
        self.d8_accum = np.zeros_like(self.d8_dir)
        self.d8_watershed = np.zeros_like(self.d8_dir) # array of ints assigned sequentially, then realted to an ID table
        self.watershed_table = dict()

        # create the outfall mask that indicates the locations of outfalls in the dataset
        self.outfall_mask = np.zeros_like(self.d8_dir)

        for r,c in outfall_locations.keys():
            self.outfall_mask[r,c] = 1
        

    # Returns cell coordinates for cells that drain into (x, y) of the D8 flow direction raster
    def get_d8_neighbours(self, r, c) -> list:

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

            # Skip cells outside raster extent
            if nr < 0 or nr >= self.max_rows or nc < 0 or nc >= self.max_cols:
                continue

            n = self.d8_dir[nr, nc]

            # get the vector value for the d8 number at n
            dn = self.direction_map[n]

            # check for inflow to (x,y)
            if dn == ((-1 * dr), (-1 * dc)):
                
                o_id = None
                # check if it's an outfall, if yes, assign outfall ID
                if self.outfall_mask[nr, nc] == 1:
                    o_id = self.outfall_locations[(nr, nc)]

                neighbours.append((nr, nc, o_id))

        return neighbours

    def get_seed_cells(self, d8_dir, to_exclude = None):
        
        if to_exclude is not None:
            sink_mask = (d8_dir == 0) & (~to_exclude)
        else: 
            sink_mask = (d8_dir == 0)

        sink_cells = [tuple(rc) for rc in np.argwhere(sink_mask)]

        return sink_cells


    def recursive_asi(self, r: int, c: int, id: str, o_id: str = None):
        # x and y are the locations of 'seed' cells from which to initiate the recursive process
        # These are edge cells, or inlets with the 'undefined' indicator
        # Each seed cell will need to have a unique ID

        # ------------------------
        # The DEM will need to be modified to create intentional sinks at the locations of inlets
        # These sinks will then be given an indicator for use in the procedure

        # for every neighbour of (x,y)
        for (i,j, o_id) in self.get_d8_neighbours(r, c):
            # call this function on the current cell, id is propagated for assigning the watershed
            self.recursive_asi(i,j,id,o_id)

            # at the inlet cell, set to the current value plus the accumulated flow to cell (i,j) - +1 for the flow to this cell
            self.d8_accum[r, c] = self.d8_accum[r, c] + self.d8_accum[i, j] + 1

        # If cell (x,y) is an outfall:
        if o_id is not None:
            for i_id in self.inlet_connections[o_id]:

                p, q = self.inlet_locations[i_id]

                # placeholder for a potentially better system later
                match self.watershed_type:
                    case "OUTLET":
                        w_id = id
                    case "OUTFALL":
                        w_id = o_id
                    case "INLET":
                        w_id = i_id

                self.recursive_asi(p, q, w_id)

                self.d8_accum[r, c] = self.d8_accum[r, c] + self.d8_accum[p, q] + 1
        
        # if this is the first time ID is added, create new entry in table
        if id not in self.watershed_table:
            v = len(self.watershed_table)
            self.watershed_table[id] = v
        else:
            v = self.watershed_table[id]

        # assign watershed value
        self.d8_watershed[r, c] = v

