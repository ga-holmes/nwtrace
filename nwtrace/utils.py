from pathlib import Path
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
from shapely.geometry import LineString, MultiLineString, Point

def dfs(segment_lookup, node_lookup, v, visited=None, edges=None):
    """
    Perform a depth-first search on an undirected graph.

    Traverses the graph starting from node `v`, collecting all connected nodes
    and the edges that were traversed. Designed for undirected networks.

    Parameters
    ----------
    segment_lookup : dict
        Dictionary mapping segment IDs to sets of nodes they connect.
        Example: {segment_id: {node1, node2}, ...}

    node_lookup : dict
        Dictionary mapping node IDs to a set of connected segment IDs.
        Example: {node_id: {segment1, segment2, ...}, ...}

    v : hashable
        The starting node ID for the DFS traversal.

    visited : set, default empty set()
        A set of already visited node IDs. Updated in place during recursion.

    edges : set, default []
        A list of segment IDs representing edges actually traversed.
        Updated in place during recursion.

    Returns
    -------
    visited : set
        The updated set of visited nodes after the DFS traversal.

    edges : list
        The updated list of traversed segment IDs.
    """

    # Set None values
    if visited is None:
        visited = set()
    if edges is None:
        edges = set()

    stack = [v]
    while stack:

        v = stack.pop()

        if v in visited:
            continue

        visited.add(v)

        if v not in node_lookup:
            continue
    
        for e in node_lookup[v]:

            w = None

            # select the correct node
            for n in segment_lookup[e]:
                if n != v:
                    w = n
            
            # Add any traversed edge
            if e not in edges:
                edges.add(e)

            # make sure not visited (in cyclical case)
            if w != None and w not in visited:
                stack.append(w)

    return visited, edges

def dfs_directed(segment_lookup, node_lookup, v, visited=None, edges=None, downstream=False):
    """
    Perform a depth-first search on a directed graph.

    Traverses the graph starting from node `v`, following only edges that flow
    into the current node (default downstream=False) or away from the current node (downstream=True). Collects all reachable nodes and
    the edges traversed.

    Parameters
    ----------
    segment_lookup : dict
        Dictionary mapping segment IDs to their upstream and downstream nodes.
        Example: {segment_id: {"from": upstream_node, "to": downstream_node}, ...}

    node_lookup : dict
        Dictionary mapping node IDs to dictionaries of incoming and outgoing
        segments. Example:
            {node_id: {"in": [segments_in], "out": [segments_out]}, ...}

    v : hashable
        The starting node ID for the DFS traversal.

    visited : set, default None
        A set of already visited node IDs. Updated in place during recursion. Will set to an empty set if None

    edges : list, None
        A list of segment IDs representing edges actually traversed. Will set to an empty array if None
        Updated in place during recursion.

    downstream : bool, default False
        The DFS searches upstream by default unless specified 'True' here to search downstream of v

    Returns
    -------
    visited : set
        The updated set of visited nodes after the DFS traversal.

    edges : list
        The updated list of traversed segment IDs.
    """

    # Set None values
    if visited is None:
        visited = set()
    if edges is None:
        edges = set()

    stack = [v]

    while stack:

        v = stack.pop()

        if v in visited:
            continue

        visited.add(v)

        if v not in node_lookup:
            continue
        
        if downstream:
            node_dir = "out"
            seg_dir = "to"
        else:
            node_dir = "in"
            seg_dir = "from"
        
        for e in node_lookup[v][node_dir]:

            seg = segment_lookup.get(e)
            if not seg:
                continue
            
            # Add any edge that is traversed
            if e not in edges:
                edges.add(e)

            for w in seg[seg_dir]:
        
                # make sure not visited (in cyclical case)
                if w != None and w not in visited:
                    stack.append(w)

    return visited, edges
    

def dfs_recursive(segment_lookup, node_lookup, v, visited=set(), edges=[]):
    """
    Perform a depth-first search on an undirected graph recursively.

    Traverses the graph starting from node `v`, collecting all connected nodes
    and the edges that were traversed. Designed for undirected networks.

    Note: May throw RecursionError: maximum recursion depth exceeded

    Parameters
    ----------
    segment_lookup : dict
        Dictionary mapping segment IDs to sets of nodes they connect.
        Example: {segment_id: {node1, node2}, ...}

    node_lookup : dict
        Dictionary mapping node IDs to a set of connected segment IDs.
        Example: {node_id: {segment1, segment2, ...}, ...}

    v : hashable
        The starting node ID for the DFS traversal.

    visited : set, default empty set()
        A set of already visited node IDs. Updated in place during recursion.

    edges : list, default []
        A list of segment IDs representing edges actually traversed.
        Updated in place during recursion.

    Returns
    -------
    visited : set
        The updated set of visited nodes after the DFS traversal.

    edges : list
        The updated list of traversed segment IDs.
    """
    
    visited.add(v)

    if v not in node_lookup:
        return visited, edges
    
    for e in node_lookup[v]:

        w = None

        # select the correct node
        for n in segment_lookup[e]:
            if n != v:
                w = n

        if e not in edges:
            edges.append(e)

        # make sure not visited (in cyclical case)
        if w != None and w not in visited:
            visited, edges = dfs_recursive(segment_lookup, node_lookup, w, visited, edges)

    return visited, edges


def dfs_directed_recursive(segment_lookup, node_lookup, v, visited=set(), edges=[], downstream=False):
    """
    Perform a depth-first search on a directed graph recursively.

    Traverses the graph starting from node `v`, following only edges that flow
    into the current node (default downstream=False) or away from the current node (downstream=True). Collects all reachable nodes and
    the edges traversed.

    Note: May throw RecursionError: maximum recursion depth exceeded

    Parameters
    ----------
    segment_lookup : dict
        Dictionary mapping segment IDs to their upstream and downstream nodes.
        Example: {segment_id: {"from": upstream_node, "to": downstream_node}, ...}

    node_lookup : dict
        Dictionary mapping node IDs to dictionaries of incoming and outgoing
        segments. Example:
            {node_id: {"in": [segments_in], "out": [segments_out]}, ...}

    v : hashable
        The starting node ID for the DFS traversal.

    visited : set, default empty set()
        A set of already visited node IDs. Updated in place during recursion.

    edges : list, default []
        A list of segment IDs representing edges actually traversed.
        Updated in place during recursion.

    downstream : bool, default False
        The DFS searches upstream by default unless specified 'True' here to search downstream of v

    Returns
    -------
    visited : set
        The updated set of visited nodes after the DFS traversal.

    edges : list
        The updated list of traversed segment IDs.
    """
    visited.add(v)

    if v not in node_lookup:
        return visited, edges
    
    if downstream:
        edges_to_follow = node_lookup[v]["out"]
        next_node = lambda e: segment_lookup.get(e)["to"]
    else:
        edges_to_follow = node_lookup[v]["in"]
        next_node = lambda e: segment_lookup.get(e)["from"]
    
    for e in edges_to_follow:

        w = next_node(e)

        if e not in edges:
            edges.append(e)

        # make sure not visited (in cyclical case)
        if w != None and w not in visited:
            visited, edges = dfs_directed_recursive(segment_lookup, node_lookup, w, visited, edges, downstream=downstream)

    return visited, edges

def extract_endpoints(line: LineString | MultiLineString) -> list:
    """
    Given a Shapely LineString or MultiLineString, returns a list containing all/both endpoints

    Parameters
    ----------
    line : LineString | MultiLineString
        The target line/segment geometry

    Returns
    -------
    list
        A list containing all endpoints in the geometry
    """
    
    if line is None or line.is_empty:
        return []

    if isinstance(line, LineString):
        coords = line.coords
        return [Point(coords[0]), Point(coords[-1])]

    if isinstance(line, MultiLineString):
        return [
            Point(line.geoms[0].coords[0]),
            Point(line.geoms[-1].coords[-1])
        ]

    return []

def count_duplicates(
    elements: str | Path | pd.DataFrame | gpd.GeoDataFrame,
    id_field: str,
    minimum_count: int=1
) -> dict:
    """
    Given a GeoDataFrame or a path to a vector geometry file, will return a dictionary countaining 
    a count of how many times each value in the 'id_field' column appears more than 'minimum_count' times.

    Parameters
    ----------
    elements : str | Path | pd.DataFrame | gpd.GeoDataFrame
        A DataFrame or GeoDataFrame, or the path to one, that contains at least one column corresponding to 'id_field'
    id_field : str
        The name of the column in the DataFrame to count duplicates in
    minimum_count : int, optional
        The minimum number of appearances for the item to be added to the output dictionary, by default 1

    Returns
    -------
    dict
        A dictionary containing the contents of the 'id_field' column in the 'elements' DataFrame, 
        with a corresponding count for how many times that value appears.
    """
    
    # Verify input geometry values
    # Load geometry
    if isinstance(elements, (str, Path)):
        elements = gpd.read_file(elements )
    elif isinstance(elements, (pd.DataFrame, gpd.GeoDataFrame)):
        elements = elements
    else:
        raise ValueError(
            "'elements' must be a path to a file that can be opened by GeoPandas or Pandas, or a DataFrame or GeoDataFrame."
        )
    
    ids = elements[[id_field, "geometry"]]

    ids_dup = ids.groupby([id_field]).count()
    ids_dup = ids_dup[ids_dup["geometry"] > minimum_count]
    ids_dup = ids_dup.rename(columns={"geometry": "duplicate_count"})

    return ids_dup.to_dict()
    

def verify_network_geometry(
        lines: str | Path | gpd.GeoDataFrame,
        points: str | Path | gpd.GeoDataFrame,
        segment_lookup: dict,
        line_id_field: str,
        point_id_field: str,
        threshold: int = 0
    ) -> list:
    """
    Given two geospatial vector files that contain IDs for nodes and segments that correspond to the given lookup table, checks that connections listed in the tree are geographically connected or close. 

    Parameters
    ----------
    lines : str | Path | gpd.GeoDataFrame
        Geometry or a filepath to the geometry that corresponds to the segments in the network
    points : str | Path | gpd.GeoDataFrame
        Geometry or a filepath to the geometry that corresponds to the nodes in the network
    segment_lookup : dict
        Lookup table for segment > node connections, may be directional or non-direcitonal NOTE: For now only accepts the multi-directional segment lookup table
    line_id_field : str
        The name of the field in the 'lines' dataset that contains the ID that corresponds to the lookup table
    point_id_field : str
        The name of the field in the 'points' dataset that contains the ID that corresponds to the lookup table
    threshold : int, optional
        distance to search within when checking connections (unit is CRS-dependent based on the CRS for the input file), by default 0

    Returns
    -------
    list
        Returns a list contatining a summary of geomerty errors found, empty list if there are none
    """

    # Verify input geometry values
    # Load geometry
    if isinstance(lines, (str, Path)):
        segments = gpd.read_file(lines)
    else:
        segments = lines

    if isinstance(points, (str, Path)):
        nodes = gpd.read_file(points)
    else:
        nodes = points

    # Match CRS
    nodes = nodes.to_crs(segments.crs)

    # Pre-build lookup dictionaries
    seg_geom = dict(zip(segments[line_id_field], segments.geometry))
    node_geom = dict(zip(nodes[point_id_field], nodes.geometry))

    errors_found = []
    total_dist = 0
    checks = 0

    # Lookup table
    for seg_id, node_ids in tqdm(segment_lookup.items(), total=len(segment_lookup)):

        seg = seg_geom.get(seg_id)
        if seg is None:
            errors_found.append({
                "node_id": None,
                "segment_id": seg_id,
                "error_t": "missing segment",
                "error_msg": f"segment {seg_id} does not exist in dataset",
                "dist": -1,
                "geometry": seg
            })
            continue

        # Check each node in this segment's connection set
        for nid in node_ids:

            node = node_geom.get(nid)
            if node is None:
                errors_found.append({
                    "node_id": nid,
                    "segment_id": seg_id,
                    "error_t": "missing node",
                    "error_msg": f"node {nid} does not exist in dataset",
                    "dist": -1,
                    "geometry": seg
                })
                continue

            # Compute distance
            dist = node.distance(seg)

            total_dist += dist
            checks += 1

            if dist > threshold:
                errors_found.append({
                    "node_id": nid,
                    "segment_id": seg_id,
                    "error_t": "spatial",
                    "error_msg": f"node {nid} is more than {threshold} units from segment {seg_id}",
                    "dist": dist,
                    "geometry": seg
                })

    print(f"{len(errors_found)} Errors Found")
    print(f"Average Distance {total_dist/checks} units")
    return errors_found

def find_nearby_nodes(
    segments: str | Path | gpd.GeoDataFrame,
    nodes: str | Path | gpd.GeoDataFrame,
    segment_id_field: str,
    distance_threshold: int = 1,
) -> gpd.GeoDataFrame:
    
    records = []
    for _, line in segments.iterrows():

        endpoints = extract_endpoints(line.geometry)
        
        for role, pt in zip(("from", "to"), endpoints):
            records.append({
                "segment_id": line[segment_id_field],
                "role": role,
                "geometry": pt
            })

    # Convert endpoint dict to a geodataframe
    endpoints_gdf = gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs=segments.crs
    )

    # Add a field with buffer geometry to each endpoint
    endpoints_gdf["geom_buffer"] = endpoints_gdf.buffer(distance_threshold)

    # create a flipped geodataframe where the main geometry is the buffer and the secondary geometry is the location of the endpoint
    seg_bufs = gpd.GeoDataFrame(
        endpoints_gdf[["segment_id", "role", "geom_buffer", "geometry"]],
        geometry="geom_buffer",
        crs=endpoints_gdf.crs
    ).rename(columns={"geometry":"endpoint"})

    # join nodes from the node dataset that fall within the buffer for each endpoint with the buffers dataset
    # This makes a geodataframe where each node (that is within a buffer) has information about nearby segment endpoints within the buffer
    nearby_nodes = gpd.sjoin(nodes, seg_bufs, predicate="intersects", how="inner")

    # calculate distance from each node to the respective endpoint
    nearby_nodes["dist"] = nearby_nodes.geometry.distance(
        nearby_nodes["endpoint"]
    )
    
    return nearby_nodes

def find_nearby_segments(
    nodes: str | Path | gpd.GeoDataFrame,
    segments: str | Path | gpd.GeoDataFrame,
    node_id_field: str,
    distance_threshold: int = 1,
) -> gpd.GeoDataFrame:
    
    nodes_copy = gpd.GeoDataFrame(
        nodes,
        geometry="geometry",
        crs=nodes.crs
    )
    # Add a field with buffer geometry to each node 
    nodes_copy["geom_buffer"] = nodes.buffer(distance_threshold)

    # create a flipped geodataframe where the main geometry is the buffer and the secondary geometry is the location of the node
    node_bufs = gpd.GeoDataFrame(
        nodes_copy[[node_id_field, "geom_buffer", "geometry"]],
        geometry="geom_buffer",
        crs=nodes.crs
    ).rename(columns={node_id_field: "node_id", "geometry":"location"})

    # This makes a geodataframe where each node (that is within a buffer) has information about nearby segment endpoints within the buffer
    nearby_segs = gpd.sjoin(segments, node_bufs, predicate="intersects", how="inner")

    # calculate distance from each node to the respective node
    nearby_segs["dist"] = nearby_segs.geometry.distance(
        nearby_segs["location"]
    )
    
    return nearby_segs

def fix_missing_nodes(
    segment_network,
    segment_id_field,
    downstream_field,
    distance_threshold = 0.1
):
    
    # get just dead end segments from the network (no downstream node)
    dead_ends = segment_network[pd.isna(segment_network[downstream_field])].reset_index()

    # get nearby segments
    nearby_segs = find_nearby_nodes(
        dead_ends, 
        segment_network, 
        segment_id_field, 
        distance_threshold=distance_threshold
    )

    nearby_segs_filtered = nearby_segs[nearby_segs["role"] == downstream_field]
    # remove segments where the closest segment is itself
    nearby_segs_filtered = nearby_segs_filtered[nearby_segs_filtered[segment_id_field] != nearby_segs_filtered["segment_id"]]
    # select the first of the closest potential connection
    best_candidates = (
            nearby_segs_filtered
            .sort_values("dist")
            .groupby(["segment_id"], as_index=False)
            .head(1)
        )
    
    # refactor candidates to represent the new segment-node connection
    repair_gdf = best_candidates[["segment_id", downstream_field]].rename(columns={"segment_id": segment_id_field})
    repair_gdf = repair_gdf.set_index(segment_id_field)

    network_indexed = segment_network.set_index(segment_id_field)

    network_indexed.update(repair_gdf)
    repaired_network = network_indexed.reset_index()

    return repaired_network

def repair_spatial_errors(
    errors: list,
    segments: str | Path | gpd.GeoDataFrame,
    nodes: str | Path | gpd.GeoDataFrame,
    segment_id_field: str,
    upstream_field: str, 
    downstream_field: str,
    distance_threshold: int = 1
) -> tuple[dict, dict]:
    
    # Extract spatial errors from the error list
    spatial_err_segs = [err["segment_id"] for err in errors if err.get("error_t") == "spatial"]

    # Select segments from the lines dataset that appear in the list of spatial errors
    err_segs = segments.loc[segments[segment_id_field].isin(spatial_err_segs)]

    # Get the endpoints of each segment with a spatial error, add to a dataset of endpoints
    nearby_nodes = find_nearby_nodes(err_segs, nodes, segment_id_field, distance_threshold=distance_threshold)
    
    # Allow easy searching of lines dataset for connecting nodes
    current_from = segments.set_index(segment_id_field)[upstream_field]
    current_to = segments.set_index(segment_id_field)[downstream_field]
    
    # returns true when a row from 'nearby_nodes' is not connected to the associated segment in the lookup table
    def not_already_connected(row):
        seg = row["segment_id"]
        role = row["role"]
        node = row[segment_id_field]  # or whatever field
        
        if role == "from":
            return node != current_from.get(seg)
        else:
            return node != current_to.get(seg)
        
    # apply the above funtion to nearby nodes (extaract all nodes that arent connected to segments in the lookup table)
    nearby_nodes = nearby_nodes[
        nearby_nodes.apply(not_already_connected, axis=1)
    ]

    # get only proposed node-segment connectioned with the minimum distance
    idx = (
        nearby_nodes
        .groupby(["segment_id", "role"])["dist"]
        .idxmin()
    )

    # get a subset of nearby nodes containing only the potential connections witht the closest endpoint-node distance
    best_candidates = nearby_nodes.loc[idx].drop_duplicates()[["FACILITYID", "segment_id", "role"]]

    best_candidates = best_candidates.pivot(
        index="segment_id",
        columns="role",
        values=segment_id_field
    )

    best_candidates = best_candidates.rename(
        columns={
            "from": upstream_field,
            "to": downstream_field
        }
    )
    
    segments_fixed = segments.set_index(segment_id_field, drop=False)
    segments_fixed.update(best_candidates)
    
    return segments_fixed
    
def repair_node_connections(
    errors: list,
    nodes: str | Path | gpd.GeoDataFrame,
    segments: str | Path | gpd.GeoDataFrame,
    node_id_field: str,
    node_connection_field: str,
    segment_id_field: str,
    upstream_field: str, 
    downstream_field: str,
    distance_threshold: int = 1
) -> tuple[dict, dict]:

    # Extract spatial errors from the error list
    spatial_err_nodes = [err["node_id"] for err in errors if err.get("error_t") == "spatial"]

    # Select segments from the lines dataset that appear in the list of spatial errors
    err_nodes = nodes.loc[nodes[node_id_field].isin(spatial_err_nodes)]

    # Get the endpoints of each segment with a spatial error, add to a dataset of endpoints
    nearby_segs = find_nearby_segments(err_nodes, segments, node_id_field, distance_threshold=distance_threshold)

        # returns true when a row from 'nearby_nodes' is not connected to the associated segment in the lookup table
    def not_already_connected(row):
        node = row["node_id"]  
        ups = row[upstream_field]
        dwns= row[downstream_field]
        
        if ups == node or dwns == node:
            return False
        else:
            return True
        
    # apply the above funtion to nearby nodes (extaract all nodes that arent connected to segments in the lookup table)
    nearby_segs = nearby_segs[
        nearby_segs.apply(not_already_connected, axis=1)
    ]

    # get only proposed node-segment connectioned with the minimum distance
    idx = (
        nearby_segs
        .groupby(["node_id"])["dist"]
        .idxmin()
    )

    # get a subset of nearby nodes containing only the potential connections witht the closest endpoint-node distance
    best_candidates = nearby_segs.loc[idx].drop_duplicates()[[segment_id_field, "node_id"]]

    best_candidates = best_candidates.rename(
        columns={
            segment_id_field: node_connection_field,
        }
    ).set_index("node_id")

    nodes_fixed = nodes.set_index(node_id_field, drop=False)
    nodes_fixed.update(best_candidates)

    return nodes_fixed

# NOTE: Remove?
def repair_network(
    errors: list,
    lines: str | Path | gpd.GeoDataFrame,
    points: str | Path | gpd.GeoDataFrame,
    segment_lookup: dict,
    node_lookup: dict,
    line_id_field: str,
    point_id_field: str,
    distance_threshold: int = 0
) -> tuple[dict, dict]:
    """
    Given network geometry and an error table output by 'utils.verify_network_geometry()', repairs the given lookup tables based on a set of rules and the given geometry.
    NOTE: Does not alter geometry or save to any files, on adjusts the lookup tables by creating new connections where necessary.
    NOTE: ^ Maybe this is necessary to fix missing node/segment connections? The connections already exist in the table after all...

    Parameters
    ----------
    errors : list
        A list containing errors and info output by 'utils.verify_network_geometry()'
    lines : str | Path | gpd.GeoDataFrame
        Geometry or a filepath to the geometry that corresponds to the segments in the network
    points : str | Path | gpd.GeoDataFrame
        Geometry or a filepath to the geometry that corresponds to the nodes in the network
    segment_lookup : dict
        Lookup table for segment > node connections that will be repaired, 
        may be directional or non-direcitonal NOTE: For now only accepts the multi-directional segment lookup table
    node_lookup : dict
        Lookup table for node > segment connections that will be repaired, 
        may be directional or non-direcitonal NOTE: For now only accepts the multi-directional segment lookup table
    line_id_field : str
        The name of the field in the 'lines' dataset that contains the ID that corresponds to the lookup table
    point_id_field : str
        The name of the field in the 'points' dataset that contains the ID that corresponds to the lookup table
    distance_threshold : int, optional
        minimum distance to repair a spatial error connection (unit is CRS-dependent based on the CRS for the input file), by default 0

    Returns
    -------
    dir_node_lookup, dir_segment_lookup: tuple[dict, dict]
        The respective repaired lookup tables for nodes and segments
    """
        
    # Verify input geometry values
    # Load geometry
    if isinstance(lines, (str, Path)):
        segments = gpd.read_file(lines)
    else:
        segments = lines

    if isinstance(points, (str, Path)):
        nodes = gpd.read_file(points)
    else:
        nodes = points

    # Match CRS
    nodes = nodes.to_crs(segments.crs)
    
    # Get all spatial error segments
    spatial_err_segs = [err["segment_id"] for err in errors if err.get("error_t") == "spatial"]
    segments = lines.loc[lines[line_id_field].isin(spatial_err_segs)].squeeze()
    
    segment_bufs = segments.buffer(distance_threshold)
    
    # Error handling:
    for err in errors:
        
        s_id = err["segment_id"]
        
        # Remove missing item errors (Maybe not necessary for table-only fixes? Only need these to repair actual geometry dataset)
        if err["error_t"] == "missing node" or err["error_t"] == "missing segment":
            continue

            # Remove errors where node_id and seg_id appear only once
            
            # Where node_id appears more than once, create additional node conneciton based on the necessary ID
            
            # above but for segments(?)
        
        # Repair misapplied connections
        else:
            
            segment = lines.loc[lines[line_id_field] == s_id].squeeze()
            seg_buf = segment.buffer(distance_threshold)
            
            nearby_nodes = gpd.sjoin(points, seg_buf, predicate="intersects")
                # Find nearest node in-data that is not connected already to the segment
                    # How to do this without massive search time? Would need to check the distance of every node in the dataset
                    
                    # Buffer by threshold -> return list of nodes
                    
                    # For each node, calculate distance
                    
                        # Ignore if already connected
                
                # Need a way to make sure that the nearest node isn't a nearby connection that is not actually connected (only connect within threshold distance from endpoint)
                
                # Set the incorrect node_id to the correct node_id
    
    return node_lookup, segment_lookup


# NOTE: add verbose mode?
def network_from_geometry(
    segments: str | Path | gpd.GeoDataFrame,
    nodes: str | Path | gpd.GeoDataFrame,
    segment_id_field: str,
    node_id_field: str,
    distance_threshold: int = 1
) -> gpd.GeoDataFrame:
    """
    Given a dataset containing segments and nodes that connect segments, 
    generates a new GeoDataFrame with the segment geometry that includes columns indicating upstream and downstream node connections.

    Parameters
    ----------
    segments : str | Path | gpd.GeoDataFrame
        The dataset of segments that are connected by nodes.
    nodes : str | Path | gpd.GeoDataFrame
        The dataset of nodes that connect the segments.
    segment_id_field : str
        The column name for the unique identifier for segments.
    node_id_field : str
        The column name for the unique identifier for nodes.
    distance_threshold : int, optional
        The maximum distance between geometries to search for connecitons, by default 1

    Returns
    -------
    gpd.GeoDataFrame
        The segment geometry including node connection information.
    """
    # Create to/from node connection entries in the given line/segment vector dataset based on appropriate point/nodes in the respective dataset

    # Verify input geometry values
    # Load geometry
    if isinstance(segments, (str, Path)):
        segs_gdf = gpd.read_file(segments)
    else:
        segs_gdf = segments

    if isinstance(nodes, (str, Path)):
        nodes_gdf = gpd.read_file(nodes)
    else:
        nodes_gdf = nodes

    # get nearby nodes
    nearby_nodes = find_nearby_nodes(
        segs_gdf,
        nodes_gdf,
        segment_id_field,
        distance_threshold
    )

    # get only proposed node-segment connectioned with the minimum distance
    best_candidates = (
        nearby_nodes
        .sort_values("dist")
        .groupby(["segment_id", "role"], as_index=False)
        .head(1)
    )

    # get distances for verification
    distances = best_candidates.pivot(index="segment_id", columns="role", values="dist")

    best_candidates = best_candidates.pivot(
        index="segment_id",
        columns="role",
        values=node_id_field
    )

    geo_network = best_candidates.join(distances, lsuffix="", rsuffix="_dist").reset_index().rename(columns={"segment_id": segment_id_field})
    
    return geo_network

def verify_flow_directionality(
    segments: str | Path | gpd.GeoDataFrame,
    nodes: str | Path | gpd.GeoDataFrame,
    segment_id_field: str,
    elevation_field: str,
    upstream_field: str = "from",
    downstream_field: str = "to",
    repair_errors: bool = True
):
    nodes_idx = nodes.set_index(segment_id_field)

    records = []

    # map elevation from nodes dataset
    segments["from_height"] = segments[upstream_field].map(nodes_idx[elevation_field])
    segments["to_height"]   = segments[downstream_field].map(nodes_idx[elevation_field])

    # Filter out invalid rows before looping
    valid = segments.dropna(subset=[upstream_field, downstream_field, "from_height", "to_height"])

    records = []
    for seg_id, seg in valid.iterrows():
        if seg["to_height"] > seg["from_height"]:
            records.append({
                segment_id_field: seg_id,
                upstream_field: seg[downstream_field],
                downstream_field: seg[upstream_field],
                "from_height": seg.get("to_height"),
                "to_height": seg.get("from_height"),
                "from_dist": seg.get("to_dist"),
                "to_dist": seg.get("from_dist")
            })

    # NOTE: repair here? or no? option?
    if repair_errors:
        repaired_errs = pd.DataFrame(records).set_index(segment_id_field)
        network = segments.copy(deep=True)
        network.update(repaired_errs)

        # NOTE: either return here, or return error count no matter what, and allow the funciton to alter 'segments' explicitly
        return network