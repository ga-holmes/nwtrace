# Adaptive Stormwater Infrastructure (ASI) Algorithm, adapted from Choi et al. (2011) : 10.1016/j.cageo.2010.07.008
import numpy as np
from pathlib import Path
import rasterio as rio

# Defining globals here (will likely be an object later)

class ASI:

    def __init__(
        self,
        d8_flow_direction_raster: str | Path | np.ndarray | rio.io.DatasetReader,
        inlet_connections: dict,
        outfall_locations: dict,
        inlet_locations: dict,
        watershed_type: str = "OUTFALL",
        direction_map: dict = None,
        no_data_value: int = -32768

    ) -> None:
        """
        Initializes a new ASI instance that can be used to perform flow accumulation via the 'Adaptive Stormwater Infrastructure' algorithm presented in Choi et al. (2011)

        Parameters
        ----------
        d8_flow_direction_raster : str | Path | np.ndarray | rio.io.DatasetReader
            A raster that is encoded with d8 flow direction values corresponding to 'direction_map' (whiteboxtools mapping by default, defined in function). May be a filepath.
        inlet_connections : dict
            A dictionary of the form { OF_ID: [INLET_ID, ...] } representing which inlets each outfall is connected to
        outfall_locations : dict
            A dictionary of the form { (row, column): OF_ID } representing the location of each outfall in the provided d8_flow_direction raster
        inlet_locations : dict
            A dictionary of the form { INLET_ID: (row, column) } representing the location of each inlet in the provided d8_flow_direction raster
        watershed_type : str, optional
            Defines how to assign watershed classes. 
            Options: 
                - OUTFALL (Give each outfall a catchment), 
                - OUTLET (catchments for seed cells/edges only), 
                - INLET (Give each Inlet a catchment). 
            by default "OUTFALL"
        direction_map : dict, optional
            A dictionary that maps values to 'directions' that a cell can be pointing towards. 
            If none, whiteboxtools directions will be used (defined in function)
            Of the form:
                {
                    int:   (0,0),   # Sink
                    int:   (-1,1),  # NE
                    int:   (0,1),   # E
                    int:   (1,1),   # SE
                    int:   (1,0),   # S
                    int:  (1,-1),   # SW
                    int:  (0,-1),   # W
                    int:  (-1,-1),  # NW
                    int: (-1,0)     # N
                } 
            , by default None
        no_data_value: int, optional
            The NoData integer set for the supplied d8_direction raster, by default -32768

        Raises
        ------
        ValueError
            If the d8_flow_direction_raster is not a correct type and cannot be converted to a numpy array.
        """

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
        self._init_accumulation_rasters()

        # create the outfall mask that indicates the locations of outfalls in the dataset
        self.outfall_mask = np.zeros_like(self.d8_dir)
        
        # set the nodata value if included
        self.nodata_value = no_data_value

        for r,c in outfall_locations.keys():
            self.outfall_mask[r,c] = 1
    
    def _init_accumulation_rasters(self):
        """
        modular raster initialization so it can be repeated when the accumulation is re-calculated
        """
        # initialize empty arrays for watershed and accumulation
        self.d8_accum = np.zeros_like(self.d8_dir, dtype=np.int32)
        self.d8_watershed = np.zeros_like(self.d8_dir) # array of ints assigned sequentially, then realted to an ID table
        self.watershed_table = dict()
        
        # visited cells during process
        nrows, ncols = self.d8_dir.shape
        self.visited_cells = np.zeros((nrows,ncols), dtype=bool)

    # Returns cell coordinates for cells that drain into (x, y) of the D8 flow direction raster
    def _get_d8_neighbours(self, r: int, c: int) -> list:
        """
        Given an input cell in self.d8_dir, finds all surrounding cells that flow into [r, c]

        Parameters
        ----------
        r : int
            The row of the target cell in self.d8_dir
        c : int
            The column of the target cell in self.d8_dir

        Returns
        -------
        list
            A list of cells that flow into self.d8_dir[r, c]
        """

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
            
            # handle noData values
            if n == self.nodata_value:
                continue

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

    def get_seed_cells(self, d8_dir, exclude_mask = None) -> list:
        """
        Compares all sinks in d8_dir to inlet locations (or the contents of to_exclude) 
        and excludes inlets from seed cells.

        Parameters
        ----------
        d8_dir : _type_
            _description_
        exclude_mask : a , optional
            _description_, by default None

        Returns
        -------
        list
            A list of seed cells that can be iterated through and used for interative_asi() to calculate flow accumulation and watersheds.
        """
        
        if exclude_mask is not None:
            sink_mask = (d8_dir == 0) & (~exclude_mask)
        else: 
            sink_mask = (d8_dir == 0)

        sink_cells = [tuple(rc) for rc in np.argwhere(sink_mask)]

        return sink_cells


    def recursive_asi(self, r: int, c: int, id: str, o_id: str = None):
        """
        Recursively trace from accumulation from the given seed cell, 
        referencing Outfall-Inlet connections and filling in self.watershed 
        to indicate catchments based on self.watershed_type. 
        
        May run into RecursionError for moderate-large datasets. iterative_asi() is preferred for all use cases.

        Parameters
        ----------
        r : int
            Location of the row of the cell to start at.
        c : int
            Location of the row of the cell to start at.
        id : str
            The ID of the seed cell, will be propagated depending on self.watershed_type (Default "OUTFALL")
        o_id : str, optional
            If withing the context of cells draining to an outfall, indicates the ID of the outall and propagates it. 
            Set within the function, by default None. ONLY USE IF THE SEED CELL IS AN OUTFALL (end of flow)
        """
        # r and c are the locations of 'seed' cells from which to initiate the recursive process
        # These are edge cells, or inlets with the 'undefined' indicator
        # Each seed cell will need to have a unique ID

        # ------------------------
        # The DEM will need to be modified to create intentional sinks at the locations of inlets
        # These sinks will then be given an indicator for use in the procedure

        # for every neighbour of (r,c)
        for (i,j, o_id) in self._get_d8_neighbours(r, c):
            # call this function on the current cell, id is propagated for assigning the watershed
            self.recursive_asi(i,j,id,o_id)

            # at the cell, set to the current value plus the accumulated flow to cell (i,j) - +1 for the flow to this cell
            self.d8_accum[r, c] = self.d8_accum[r, c] + self.d8_accum[i, j] + 1

        # If cell (r,c) is an outfall:
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

    def iterative_asi(self, r0: int, c0: int, id: str, o_id: str = None):
        """
        Iteratively trace from accumulation from the given seed cell, 
        referencing Outfall-Inlet connections and filling in self.watershed 
        to indicate catchments based on self.watershed_type

        Parameters
        ----------
        r0 : int
            Location of the row of the cell to start at.
        c0 : int
            Location of the row of the cell to start at.
        id : str
            The ID of the seed cell, will be propagated depending on self.watershed_type (Default "OUTFALL")
        o_id : str, optional
            If withing the context of cells draining to an outfall, indicates the ID of the outall and propagates it. 
            Set within the function, by default None. ONLY USE IF THE SEED CELL IS AN OUTFALL (end of flow)
        """

        # This is called for each seed cell
        # r and c are the locations of 'seed' cells from which to initiate the recursive process
        # These are edge cells, or inlets with the 'undefined' indicator
        # Each seed cell will need to have a unique ID

        # ------------------------
        # The DEM will need to be modified to create intentional sinks at the locations of inlets
        # These sinks will then be given an indicator for use in the procedure

        # Instead of recursion, the operations are handled with a stack that acceprts arguments similarly to the function
        # Stack arguments: (row, column, watershed_id, outfall_id: may be none, ORDER (PRE=0, POST=1))
        # 'ORDER' is used to represent whether, for each cell visit, we should find children (i.e. get neighbours), or accumulate flow (flow cannot accumulate until we've reached the 'top' of the DEM)

        # if accumulation has already been computed, abort
        if self.d8_accum[r0, c0] != 0:
            print("accumulation already computed, canceling")
            return
        
        PRE = 0
        POST = 1
        
        stack = []
        # top of stack
        stack.append((r0, c0, id, o_id, PRE, None))
        
        while stack:
            r, c, id, o_id, phase, children = stack.pop()
            
            # pre visit
            if phase == PRE:
                
                # check if in visited
                if self.visited_cells[r, c]:
                    continue
                
                self.visited_cells[r,c] = True
                
                children = self._get_d8_neighbours(r, c)
                    
                # push POST phase for next iteration
                stack.append((r, c, id, o_id, POST, children))
                
                # for every neighbour of (r,c)
                for (i,j, c_o_id) in children:    
                    # Append only if not visited
                    if not self.visited_cells[i,j]:
                        stack.append((i, j, id, c_o_id, PRE, None))

                # If cell (r,c) is an outfall:
                if o_id is not None:
                    for i_id in self.inlet_connections[o_id]:

                        p, q = self.inlet_locations[i_id]

                        w_id = {
                            "OUTLET": id,
                            "OUTFALL": o_id,
                            "INLET":  i_id
                        }[self.watershed_type]

                        # Push new inlet cell to stack including new watershed id (based on above)
                        if not self.visited_cells[p,q]:
                            stack.append((p, q, w_id, None, PRE, None))
                
            # post visit
            else:
                
                # normal cell flow
                for ( i, j, _) in children:
                    if self.visited_cells[i,j]:
                        self.d8_accum[r,c] += self.d8_accum[i,j] + 1
                
                # outfall-inlet flow
                if o_id is not None:
                    for i_id in self.inlet_connections[o_id]:
                        p, q = self.inlet_locations[i_id]
                        
                        if self.visited_cells[p,q]:
                            self.d8_accum[r,c] += self.d8_accum[p,q] + 1
                                
                # if this is the first time ID is added, create new entry in table
                v = self.watershed_table.setdefault(id, len(self.watershed_table))

                # assign watershed value
                self.d8_watershed[r, c] = v
    