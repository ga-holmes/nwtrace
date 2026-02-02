from pathlib import Path
import geopandas as gpd
import pandas as pd
from tqdm import tqdm

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
        lookup_table: dict,
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
    lookup_table : dict
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
    for seg_id, node_ids in tqdm(lookup_table.items(), total=len(lookup_table)):

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