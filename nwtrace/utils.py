
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
        A list of segment IDs representing edges actually traversed. Will set to an empty array in None
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
        edges = []

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

            for w in seg[seg_dir]:
        
                # make sure not visited (in cyclical case)
                if w != None and w not in visited:
                    edges.append(e)
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

        # make sure not visited (in cyclical case)
        if w != None and w not in visited:
            edges.append(e)
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

        # make sure not visited (in cyclical case)
        if w != None and w not in visited:
            edges.append(e)
            visited, edges = dfs_directed_recursive(segment_lookup, node_lookup, w, visited, edges, downstream=downstream)

    return visited, edges