# script to create subset of all gravity mains that connect directly to a given outfall

import sys
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
import os

def dfs_recursive(segment_lookup, node_lookup, v, visited=set(), edges=[]):
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

        # make sure not visited (in cyclical case)
        if w != None and w not in visited:
            edges.append(e)
            visited, edges = dfs_recursive(segment_lookup, node_lookup, w, visited, edges)

    return visited, edges


def dfs(segment_lookup, node_lookup, v, visited=set(), edges=[]):
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

            # make sure not visited (in cyclical case)
            if w != None and w not in visited:
                edges.append(e)
                stack.append(w)

    return visited, edges

def dfs_directed(segment_lookup, node_lookup, v, visited=set(), edges=[], downstream=False):
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

    stack = [v]

    while stack:

        v = stack.pop()

        if v in visited:
            continue

        visited.add(v)

        if v not in node_lookup:
            continue
        
        if downstream:
            edges_to_follow = node_lookup[v]["out"]
            next_node = lambda e: segment_lookup.get(e)["to"]
        else:
            edges_to_follow = node_lookup[v]["in"]
            next_node = lambda e: segment_lookup.get(e)["from"]
        
        for e in edges_to_follow:

            w = next_node(e)

            # make sure not visited (in cyclical case)
            if w != None and w not in visited:
                edges.append(e)
                stack.append(w)

    return visited, edges

def dfs_directed_recursive(segment_lookup, node_lookup, v, visited=set(), edges=[], downstream=False):
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

        # make sure not visited (in cyclical case)
        if w != None and w not in visited:
            edges.append(e)
            visited, edges = dfs_directed_recursive(segment_lookup, node_lookup, w, visited, edges, downstream=downstream)

    return visited, edges

def trace_sewersheds(
    sewer_network_path, 
    target_endpoints, 
    upstream_only=False,
    downstream_only=False, 
    sewer_id_field='Sewer Gravity Asset Identification', 
    upstream_field='Sewer Gravity Upstream Maintenance Hole', 
    downstream_field='Sewer Gravity Downstream Maintenance Hole', 
    verbose=False
):
    """
    Trace all line segments in a geospatial sewer network connected to a set of target endpoints.

    Reads a geospatial file containing line segments, where each segment has upstream and 
    downstream nodes. Returns all segments connected to each target endpoint, optionally
    following only upstream connections.

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

    sewer_id_field : str, default 'Sewer Gravity Asset Identification'
        Name of the field in the geospatial data representing the unique segment ID.

    upstream_field : str, default 'Sewer Gravity Upstream Maintenance Hole'
        Name of the field representing the upstream node for each segment.

    downstream_field : str, default 'Sewer Gravity Downstream Maintenance Hole'
        Name of the field representing the downstream node for each segment.

    verbose : bool, default False
        If True, prints progress and debugging information.

    Returns
    -------
    connected_edges : list
        A list of segment IDs representing all edges connected to the specified target
        endpoints according to the traversal rules.
    """

    if verbose:
        print(f"Tracing Sewer Network from endpoint(s) [{target_endpoints[0]}(...)]")
        if not (upstream_only ^ downstream_only):
            print(f"\tDirection(s): all")
        elif upstream_only and not downstream_only:
            print(f"\tDirection(s): upstream")
        else:
            print(f"\tDirection(s): downstream")

        print(f"Loading network file: `{sewer_network_path}`...")

    # load data
    grav_main = gpd.read_file(sewer_network_path) 

    if verbose:
        print(f"Preparing {"" if not upstream_only else "directional"} node connection tree...")

    all_connected = []

    if upstream_only ^ downstream_only:

        # create directional lookup tables
        df_grav_dir = grav_main.rename(columns={upstream_field: 'from', downstream_field: 'to', sewer_id_field: 'segment_id'})
        segment_lookup = (df_grav_dir.set_index("segment_id")[["from", "to"]].to_dict(orient="index"))

        # create separate node tables for inflow and outflow
        df_node_in = df_grav_dir[["to", "segment_id"]].rename(columns={"to": "node_id"})
        df_node_out = df_grav_dir[["from", "segment_id"]].rename(columns={"from": "node_id"})

        node_in = df_node_in.groupby("node_id")["segment_id"].apply(list).to_dict()
        node_out = df_node_out.groupby("node_id")["segment_id"].apply(list).to_dict()

        # Merge all nodes and create the lookup table
        all_nodes = set(node_in.keys()) | set(node_out.keys())
        node_lookup = {
            node: {"in": node_in.get(node, []), "out": node_out.get(node, [])}
            for node in all_nodes
        }

        if verbose:
            print(f"Searching Network:")

        for o in tqdm(target_endpoints, disable=(not verbose)):
            visited_list, edges_list = dfs_directed(segment_lookup, node_lookup, o, set(), [], downstream=downstream_only)
            
            for e in edges_list:
                all_connected.append({"segment_id": e, "exit_point": o})

        if verbose:
            print(f"Finished!")

    else:
        # seperate into separate upstream and downstream tables for each segment
        df_grav_ups = grav_main[[sewer_id_field, upstream_field]].rename(columns={upstream_field: 'node_id', sewer_id_field: 'segment_id'})
        df_grav_dwns = grav_main[[sewer_id_field, downstream_field]].rename(columns={downstream_field: 'node_id', sewer_id_field: 'segment_id'})

        # combine to a single dataframe for all segment-node connections
        df_nodes = pd.concat([df_grav_ups, df_grav_dwns], ignore_index=True)
        
        # group segments by node_id for node-segment lookup and vice-versa for segment-node lookup
        node_lookup = df_nodes.groupby('node_id')['segment_id'].apply(set).to_dict()
        segment_lookup = df_nodes.groupby('segment_id')['node_id'].apply(set).to_dict()

        # run a depth-first-search of the network

        if verbose:
            print(f"Searching Network:")

        for o in tqdm(target_endpoints, disable=(True)):
            visited_list, edges_list = dfs(segment_lookup, node_lookup, o, set(), [])
            
            for e in edges_list:
                all_connected.append({"segment_id": e, "exit_point": o})

        if verbose:
            print(f"Finished!")

    return all_connected

def trace_sewershed(
    sewer_network_path, 
    target_endpoint, 
    upstream_only=False,
    downstream_only=False,
    sewer_id_field='Sewer Gravity Asset Identification', 
    upstream_field='Sewer Gravity Upstream Maintenance Hole', 
    downstream_field='Sewer Gravity Downstream Maintenance Hole', 
    verbose=False
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

    sewer_id_field : str, default 'Sewer Gravity Asset Identification'
        Name of the field in the geospatial data representing the unique segment ID.

    upstream_field : str, default 'Sewer Gravity Upstream Maintenance Hole'
        Name of the field representing the upstream node for each segment.

    downstream_field : str, default 'Sewer Gravity Downstream Maintenance Hole'
        Name of the field representing the downstream node for each segment.

    verbose : bool, default False
        If True, prints progress and debugging information.

    Returns
    -------
    connected_edges : list
        A list of segment IDs representing all edges connected to the specified target
        endpoint according to the traversal rules.
    """

    return trace_sewersheds(sewer_network_path, [target_endpoint], sewer_id_field=sewer_id_field, upstream_field=upstream_field, downstream_field=downstream_field, upstream_only=upstream_only, downstream_only=downstream_only, verbose=verbose)
