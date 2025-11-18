# script to create subset of all gravity mains that connect directly to a given outfall

import geopandas as gpd
from tqdm import tqdm
import pandas as pd
from pathlib import Path

from .utils import dfs, dfs_directed

class NWTrace:

    def __init__(
        self,
        network_path: str | Path,
        id_field: str ='Sewer Gravity Asset Identification', 
        upstream_field: str ='Sewer Gravity Upstream Maintenance Hole', 
        downstream_field: str ='Sewer Gravity Downstream Maintenance Hole',
        working_dir: str | Path = ".",
        output_dir: str | Path = "./out",
        verbose: bool = False,
    ) -> None:
        """
        Initializes a NWTrace object instance

        Parameters
        ----------
        network_path : str | Path
            Filepath to the file containing the node-line connections (must be openable by Pandas, may include spatial data)
        id_field : str, optional
            The name of the field containing line and node identifiers, by default 'Sewer Gravity Asset Identification'
        upstream_field : str, optional
            The name of the field containing the ID for upstream nodes, by default 'Sewer Gravity Upstream Maintenance Hole'
        downstream_field : str, optional
            The name of the field containing the ID for downstream nodes, by default 'Sewer Gravity Downstream Maintenance Hole'
        working_dir : str | Path, optional
            Path to a specified working directory, by default "."
        output_dir : str | Path, optional
            Path to an output directory, by default "./out"
        verbose : bool, optional
            Set to True to print progress indicators, by default False
        """

        # Set up paths, throws FileNotFoundError if issues occur
        self.network_path = Path(network_path)
        
        self.working_dir = Path(working_dir)
        Path(self.working_dir).mkdir(parents=True, exist_ok=True)
        
        self.output_dir = Path(output_dir)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)        

        self.verbose = verbose

        if self.verbose: print(f"Loading network file: `{self.network_path}`...")

        # load file using pandas
        # TODO: handle incompatible file error
        self.network_main = gpd.read_file(self.network_path)

        # TODO: verify that given fields are present in the loaded file

        self.id_field = id_field
        self.upstream_field = upstream_field
        self.downstream_field = downstream_field

        # Initialize lookup tables
        # NOTE: May change later so that tables are created at runtime (not at initialization)
        self.node_lookup, self.segment_lookup = self._create_lookup()
        self.dir_node_lookup, self.dir_segment_lookup = self._create_directional_lookup()

        

    def _create_lookup(self) -> tuple[dict, dict]:
        """
        Builds lookup tables for nodes and lines that can be traversed as a connected tree based on the object attributes.

        Returns
        -------
        node_lookup, segment_lookup: tuple[dict, dict]
            The respective lookup tables for nodes and segments
        """
        # seperate into separate upstream and downstream tables for each segment
        df_grav_ups = self.network_main[[self.id_field, self.upstream_field]].rename(columns={self.upstream_field: 'node_id', self.id_field: 'segment_id'})
        df_grav_dwns = self.network_main[[self.id_field, self.downstream_field]].rename(columns={self.downstream_field: 'node_id', self.id_field: 'segment_id'})

        # combine to a single dataframe for all segment-node connections
        df_nodes = pd.concat([df_grav_ups, df_grav_dwns], ignore_index=True)
        
        # group segments by node_id for node-segment lookup and vice-versa for segment-node lookup
        node_lookup = df_nodes.groupby('node_id')['segment_id'].apply(set).to_dict()
        segment_lookup = df_nodes.groupby('segment_id')['node_id'].apply(set).to_dict()

        return node_lookup, segment_lookup
    
    def _create_directional_lookup(
        self
    ) -> tuple[dict, dict]:
        """
        Builds directional lookup tables for nodes and lines that can be traversed as a connected tree based on the object attributes.

        Returns
        -------
        dir_node_lookup, dir_segment_lookup: tuple[dict, dict]
            The respective directional lookup tables for nodes and segments
        """
        
        # create directional lookup tables
        df_grav_dir = self.network_main.rename(columns={self.upstream_field: 'from', self.downstream_field: 'to', self.id_field: 'segment_id'})
        
        # Convert fields to lists (allows extensibility later on)
        df_grav_dir["from"] = df_grav_dir["from"].apply(lambda x: [x] if pd.notnull(x) else [])
        df_grav_dir["to"]   = df_grav_dir["to"].apply(lambda x: [x] if pd.notnull(x) else [])

        dir_segment_lookup = (df_grav_dir.set_index("segment_id")[["from", "to"]].to_dict(orient="index"))

        # create separate node tables for inflow and outflow (explodes the lists created in the previous step)
        df_node_in = df_grav_dir.explode("to")[["to", "segment_id"]].rename(columns={"to": "node_id"})
        df_node_out = df_grav_dir.explode("from")[["from", "segment_id"]].rename(columns={"from": "node_id"})

        node_in = df_node_in.groupby("node_id")["segment_id"].apply(list).to_dict()
        node_out = df_node_out.groupby("node_id")["segment_id"].apply(list).to_dict()

        # Merge all nodes and create the lookup table
        all_nodes = set(node_in.keys()) | set(node_out.keys())
        dir_node_lookup = {
            node: {"in": node_in.get(node, []), "out": node_out.get(node, [])}
            for node in all_nodes
        }

        return dir_node_lookup, dir_segment_lookup

    def trace_sewersheds(
        self,
        target_endpoints, 
        upstream_only=False,
        downstream_only=False, 
    ) -> list:
        """
        Trace all line segments in a geospatial sewer network connected to a set of target endpoints.

        Returns all segments connected to each target endpoint, optionally
        following only upstream or downstream connections. If both upstream and downstream are set to True, both directions will be traced (Same as both False).

        Parameters
        ----------
        sewer_network_path : str
            Path to the geospatial file containing sewer segments.

        target_endpoints : list
            List of node IDs representing the starting points for tracing.

        upstream_only : bool, default False
            If True, only follow upstream connections when tracing the network.
            If False, follow all connections (upstream and downstream).
            If both upstream_only and downstream_only are True, all connections will be followed (upstream and downstream)

        downstream_only : bool, default False
            If True, only follow downstream connections when tracing the network.
            If False, follow all connections (upstream and downstream).
            If both upstream_only and downstream_only are True, all connections will be followed (upstream and downstream)

        Returns
        -------
        connected_edges : list
            A list of segment IDs representing all edges connected to the specified target
            endpoints according to the traversal rules.
        """

        if self.verbose:
            print(f"Tracing Sewer Network from endpoint(s) [{target_endpoints[0]}(...)]")
            if not (upstream_only ^ downstream_only):
                print(f"\tDirection(s): all")
            elif upstream_only and not downstream_only:
                print(f"\tDirection(s): upstream")
            else:
                print(f"\tDirection(s): downstream")

        if self.verbose:
            print(f"Preparing {'' if not upstream_only else 'directional'} node connection tree...")

        all_connected = []

        # build tables
        # Directional
        if upstream_only ^ downstream_only:

            if self.dir_node_lookup == None or self.dir_segment_lookup == None:
                self._create_directional_lookup()

            node_lookup = self.dir_node_lookup
            segment_lookup = self.dir_segment_lookup

            dfs_func = dfs_directed
            dsf_kwargs = {"downstream": downstream_only}

        # Non-directional
        else:

            if self.node_lookup == None or self.segment_lookup == None:
                self._create_lookup()
            
            node_lookup = self.node_lookup
            segment_lookup = self.segment_lookup

            dfs_func = dfs
            dsf_kwargs = {}

        # run a depth-first-search of the network
        if self.verbose:
            print(f"Searching Network:")

        for o in tqdm(target_endpoints, disable=(not self.verbose)):
            visited_list, edges_list = dfs_func(segment_lookup, node_lookup, o, set(), [], **dsf_kwargs)
            
            for e in edges_list:
                all_connected.append({"segment_id": e, "exit_point": o})

            # if verbose:
            #     total_con += len(edges_list)
            #     print(f"\tfound {len(edges_list)} connections to {o}")

        if self.verbose:
            print(f"\nFound {len(edges_list)} connections overall to all {len(target_endpoints)} endpoints")
            print(f"Finished!")

        return all_connected

    def trace_sewershed(
        self,
        target_endpoint, 
        upstream_only=False,
        downstream_only=False,
    ):    
        """
        Wrapper for `trace_sewersheds` that traces segments connected to a single target endpoint.

        Converts a single node ID into a one-item list and calls `trace_sewersheds`, returning
        all connected segments.

        Parameters
        ----------
        sewer_network_path : str
            Path to the geospatial file containing sewer segments.

        target_endpoint : hashable
            Node ID representing the starting point for tracing.

        upstream_only : bool, default False
            If True, only follow upstream connections when tracing the network.
            If False, follow all connections (upstream and downstream).
            
        downstream_only : bool, default False
            If True, only follow downstream connections when tracing the network.
            If False, follow all connections (upstream and downstream).
            If both upstream_only and downstream_only are True, all connections will be followed (upstream and downstream)

        Returns
        -------
        connected_edges : list
            A list of segment IDs representing all edges connected to the specified target
            endpoint according to the traversal rules.
        """

        return self.trace_sewersheds(
            [target_endpoint], 
            upstream_only=upstream_only, 
            downstream_only=downstream_only
        )
