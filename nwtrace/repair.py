from pathlib import Path
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
from shapely.geometry import LineString, MultiLineString, Point

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

def find_nearby_geometry(
    dataset_a: str | Path | gpd.GeoDataFrame,
    dataset_b: str | Path | gpd.GeoDataFrame,
    distance_threshold: float = 1.0,
) -> gpd.GeoDataFrame:
    """
    Given two datasets of georeferenced vector geometry, finds items in dataset2 that are withing 'distance_threshold' units of items in dataset1

    Parameters
    ----------
    dataset1 : str | Path | gpd.GeoDataFrame
        A georeferenced vector geometry dataset
    dataset2 : str | Path | gpd.GeoDataFrame
        A georeferenced vector geometry dataset
    distance_threshold : float, optional
        The maximum distance to search, by default 1

    Returns
    -------
    gpd.GeoDataFrame
        A set of items from dataset1 and dataset2 within distance of eachother
    """
    
    # Load datasets if paths were provided
    if not isinstance(dataset_a, gpd.GeoDataFrame):
        dataset_a = gpd.read_file(dataset_a)
    if not isinstance(dataset_b, gpd.GeoDataFrame):
        dataset_b = gpd.read_file(dataset_b)

    # match crs NOTE: maybe make optional
    dataset_b = dataset_b.to_crs(dataset_a.crs)

    # make a deep copy of dataset1
    da = dataset_a.copy()

    # Add a field with buffer geometry to each node 
    da["geom_buffer"] = dataset_a.buffer(distance_threshold)

    # create a flipped geodataframe where the main geometry is the buffer and the secondary geometry is the location of the node
    da_bufs = da.rename(columns={"geometry": "location"})
    da_bufs = da_bufs.set_geometry("geom_buffer")

    # This makes a geodataframe where each node (that is within a buffer) has information about nearby segment endpoints within the buffer
    nearby = gpd.sjoin(dataset_b, da_bufs, predicate="intersects", how="inner")

    # calculate distance from each node to the respective node
    nearby["dist"] = nearby.geometry.distance(
        nearby["location"]
    )
    
    return nearby

def split_segments(
    segments: str | Path | gpd.GeoDataFrame,
    keep_segment_geometry: bool = False,
    set_from_field: str = 'from',
    set_to_field: str = 'to',
    set_role_field: str = 'role'
) -> gpd.GeoDataFrame:
    """
    Splits the given datset of segments into single points for the first (from) and last (to) point in the linestring

    Parameters
    ----------
    segments : str | Path | gpd.GeoDataFrame
        A vector line geometry dataset
    keep_segment_geometry : bool, optional
        If true, will keep the original line geometry in the dataset under a different field/column name, by default False
    set_from_field : str, optional
        Optionally set the name of the 'from' direction, by default "from"
    set_to_field : str, optional,
        Optionally set the name of the 'from' direction, by default "to"
    set_role_field : str, optional,
        Optionally set the name of the 'role' field, by default "role"

    Returns
    -------
    gpd.GeoDataFrame
        The dataset of endpoints for each segment
    """
    
    # Create a new dataset of endpoints for each segment
    records = []
    for _,line in segments.iterrows():

        endpoints = extract_endpoints(line.geometry)
        base = line.to_dict()  # convert namedtuple → dict
        
        for role, pt in zip((set_from_field, set_to_field), endpoints):
            # Keep all original fields
            rec = base.copy()
            rec[set_role_field] = role
            if keep_segment_geometry: # keep original geometry
                rec['segment_geometry'] = rec.pop('geometry')
            rec['geometry'] = pt

            records.append(rec)

    # Convert endpoint dict to a geodataframe
    endpoints_gdf = gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs=segments.crs
    )

    return endpoints_gdf

def filter_existing_pairs(
    df: pd.DataFrame | gpd.GeoDataFrame, 
    left_key: str, 
    right_key: str
) -> pd.DataFrame | gpd.GeoDataFrame:
    """
    Given a DataFrame or a GeoDataFrame, return a subset where values the two given columns/fields are not the same.

    Parameters
    ----------
    df : pd.DataFrame | gpd.GeoDataFrame
        A pandas DataFrame or geopandas GeoDataFrame
    left_key : str
        A column/field that exists in 'df'
    right_key : str
        A different column/field that exists in 'df'

    Returns
    -------
    pd.DataFrame | gpd.GeoDataFrame
        The filtered DataFrame/GeoDataFrame
    """
    # if df is empty, just return it
    if len(df) == 0: return df

    # create list with just the two relevant columns
    idx = list(zip(df[left_key], df[right_key]))
    # mask out values that are the same
    mask = [pair[0] != pair[1] for pair in idx]

    return df[mask]

def filter_minimum_value(
    df: pd.DataFrame | gpd.GeoDataFrame, 
    target_key: str, 
    group_keys: list
) -> pd.DataFrame | gpd.GeoDataFrame:
    """
    Returns only one of each 'group_key' rows where 'target_key' has the lowest value

    Parameters
    ----------
    df : pd.DataFrame | gpd.GeoDataFrame
        A pandas DataFrame or geopandas GeoDataFrame
    target_key : str
        The target field/column with a numeric value
    group_keys : list
        A list of field/column names to return only one each of - ex. ['segment_id', 'node_id']

    Returns
    -------
    pd.DataFrame | gpd.GeoDataFrame
        The filtered data structure
    """

    # Resets index in case of duplicate index values
    temp = df.reset_index(drop=True)
    
    # get only proposed group_key pair with the minimum
    pos = (
        temp
        .groupby(group_keys)[target_key]
        .idxmin()
    )

    # get a subset containing only the pairs with the lowest value
    return df.iloc[pos.values].drop_duplicates()

# mid level wrappers

def find_nearby_nodes(
    segments: str | Path | gpd.GeoDataFrame,
    nodes: str | Path | gpd.GeoDataFrame,
    distance_threshold: float = 1.0,
    set_from_field: str = 'from',
    set_to_field: str = 'to',
    set_role_field: str = 'role'
) -> gpd.GeoDataFrame:
    """
    Splits a segment dataset into first and last endpoints and searches for geometry in the nodes dataset within 'distance_threshold' of each endpoint.

    Parameters
    ----------
    segments : str | Path | gpd.GeoDataFrame
        A georeferenced line geometry dataset.
    nodes : str | Path | gpd.GeoDataFrame
        A georeferenced vector geometry dataset with items close to 'segments' items.
    distance_threshold : float, optional
        Maximum distance to search from each endpoint, by default 1
    set_from_field : str, optional
        Optionally set the name of the 'from' direction, by default "from"
    set_to_field : str, optional,
        Optionally set the name of the 'from' direction, by default "to"
    set_role_field : str, optional,
        Optionally set the name of the 'role' field, by default "role"

    Returns
    -------
    gpd.GeoDataFrame
        A dataset of nodes that are within distance to each segment endpoint.
    """
    
    # get endpoints for each segment
    endpoints_gdf = split_segments(segments, keep_segment_geometry=False, set_from_field=set_from_field, set_to_field=set_to_field, set_role_field=set_role_field)

    # Get nodes nearby to endpoints
    nearby_nodes = find_nearby_geometry(
        dataset_a=endpoints_gdf,
        dataset_b=nodes,
        distance_threshold=distance_threshold
    )

    return nearby_nodes

def repair_connections(
    primary_dataset: str | Path | gpd.GeoDataFrame,
    reference_dataset: str | Path | gpd.GeoDataFrame,
    primary_id_field: str,
    reference_id_field: str,
    connection_field: str,
    reference_connection_fields: list = [],
    distance_threshold: int = 1,
    reset_index: bool = True
) -> gpd.GeoDataFrame:
    """
    Compares connections listed in the 'connection_field' of the 'primary_dataset' to the 'reference_dataset' 
    to the actual proximity of the respective geometry, then corrects invalid connections based on 'distance_threshold'.

    Parameters
    ----------
    primary_dataset : str | Path | gpd.GeoDataFrame
        The main dataset that contains a column/field indicating a connection to items in the reference dataset
    reference_dataset : str | Path | gpd.GeoDataFrame
        The dataset with unique IDs corresponding to entries in the primary dataset
    primary_id_field : str
        The column/field name indicating the unique ID of items in the primary dataset
    reference_id_field : str
        The column/field name indicating the unique ID of items in the primary dataset
    connection_field : str
        The column/field name indicating the connections to items from the reference_dataset to the primary dataset
    reference_connection_fields : list, optional
        Additional fields in the reference dataset to check for connections against the primary dataset, by default an empty list
    distance_threshold : int, optional
        The maximum distance to search for a geometric connection, by default 1
    reset_index : bool, optional
        Reset the index back to a column on return, by default True

    Returns
    -------
    gpd.GeoDataFrame
        A copy of the primary dataset with updated connections in the 'connection_field' 
    """

    # Get the endpoints of each segment with a spatial error, add to a dataset of endpoints
    nearby_geometry = find_nearby_geometry(primary_dataset, reference_dataset, distance_threshold=distance_threshold)

    # filter out items where the geometries are already connected
    filtered_geometries = filter_existing_pairs(nearby_geometry, reference_id_field, connection_field)

    # filter out additional connections
    for field_name in reference_connection_fields:
        filtered_geometries = filter_existing_pairs(nearby_geometry, primary_id_field, field_name)

    # filter items where the connecting item is the same as itself
    filtered_geometries = filter_existing_pairs(filtered_geometries, primary_id_field, reference_id_field)

    # For each geometry, get only the connection with the minimum distance value
    filtered_geometries = filter_minimum_value(filtered_geometries, 'dist', [primary_id_field])

    best_candidates = filtered_geometries[[primary_id_field, reference_id_field]]

    # rename colums to prepare for updating
    best_candidates = best_candidates.rename(
        columns={
            reference_id_field: connection_field,
        }
    ).set_index(primary_id_field, drop=False)

    # update the primary dataset with the new values
    primary_fixed = primary_dataset.set_index(primary_id_field, drop=False)
    primary_fixed.update(best_candidates)

    if reset_index:
        primary_fixed = primary_fixed.reset_index(drop=True)

    return primary_fixed

# high level wrappers

def repair_segment_connections(
    segments: str | Path | gpd.GeoDataFrame,
    nodes: str | Path | gpd.GeoDataFrame,
    segment_id_field: str,
    node_id_field: str,
    upstream_field: str, 
    downstream_field: str,
    distance_threshold: int = 1
) -> gpd.GeoDataFrame:
    """
    Given a georeferenced line dataset and a georeferenced point dataset, 
    compares existing 'upstream' and 'downstream' connections in the table from lines to points with geometric proximity,
    then updates the table if a connection in the table is mismatched from the geometry connections.

    Parameters
    ----------
    segments : str | Path | gpd.GeoDataFrame
        A GeoDataFrame dataset with LineString or MultiLineString geometry that also contains 'connections' to an existing point dataset.
    nodes : str | Path | gpd.GeoDataFrame
        A GeoDataFrame dataset with unique IDs that correspond to connections in the segment dataset.
    segment_id_field : str
        The field/column name for the unique identifier for segments
    node_id_field : str
        The field/column name for the unique identifier for nodes
    upstream_field : str
        The field/column name for the upstream node connections
    downstream_field : str
        The field/column name for the downstream node connections
    distance_threshold : int, optional
        The maximum distance to search for nearby points, by default 1

    Returns
    -------
    gpd.GeoDataFrame
        The repaired segment dataset with updated geometry-based node connections
    """

    if segment_id_field == node_id_field:
        # NOTE: If we don't want to exit out, might be possible to temporarily rename the fields here, and just let the user know in verbose mode
        raise ValueError("The segment ID field has the same name as the node ID field. When the two datasets are joined, the columns will be renamed to '{`node_id_field`}_left' and '{`segment_id_field`}_right respectively'.")

    # get endpoints for each segment
    endpoints_gdf = split_segments(segments, keep_segment_geometry=False, set_from_field='from', set_to_field='to', set_role_field='role')

    # split into two tables with 'from' and 'to' roles respectively
    from_nodes = endpoints_gdf[endpoints_gdf['role'] == 'from']
    to_nodes = endpoints_gdf[endpoints_gdf['role'] == 'to']

    # repair 'from' connections
    repair_segments_a = repair_connections(
        primary_dataset=from_nodes,
        reference_dataset=nodes,
        primary_id_field=segment_id_field,
        reference_id_field=node_id_field,
        connection_field=upstream_field,
        distance_threshold=distance_threshold,
        reset_index=False
    )

    repair_segments_a = repair_segments_a[[segment_id_field, upstream_field]]

    # repair 'to' connections
    repair_segments_b = repair_connections(
        primary_dataset=to_nodes,
        reference_dataset=nodes,
        primary_id_field=segment_id_field,
        reference_id_field=node_id_field,
        connection_field=downstream_field,
        distance_threshold=distance_threshold,
        reset_index=False
    )

    repair_segments_b = repair_segments_b[[segment_id_field, downstream_field]]

    # update the original dataset with both repaired dataframes
    repaired_segments = segments.set_index(segment_id_field, drop=False)

    # update the input dataset
    repaired_segments.update(repair_segments_a)
    repaired_segments.update(repair_segments_b)

    return repaired_segments.reset_index(drop=True)

# Old version that also checks the upstream and downstream connections
# def repair_node_connections(
#     nodes: str | Path | gpd.GeoDataFrame,
#     segments: str | Path | gpd.GeoDataFrame,
#     node_id_field: str,
#     segment_id_field: str,
#     connection_field: str,
#     upstream_field: str, 
#     downstream_field: str,
#     distance_threshold: int = 1
# ) -> gpd.GeoDataFrame:

#     # Get the endpoints of each segment with a spatial error, add to a dataset of endpoints
#     nearby_segs = find_nearby_geometry(nodes, segments, distance_threshold=distance_threshold)

#     # filter out items where the node and segment are already connected
#     filtered_segs = filter_existing_pairs(nearby_segs, node_id_field, upstream_field)
#     filtered_segs = filter_existing_pairs(filtered_segs, node_id_field, downstream_field)

#     # filter items where node_id and segment_id are the same
#     filtered_segs = filter_existing_pairs(filtered_segs, segment_id_field, node_id_field)

#     # For each 'node' - 'role' pair, get only the one with the minimum value
#     best_candidates = filter_minimum_value(filtered_segs, 'dist', [node_id_field])

#     # rename colums to prepare for updating
#     best_candidates = best_candidates.rename(
#         columns={
#             segment_id_field: connection_field,
#         }
#     ).set_index(node_id_field)

#     nodes_fixed = nodes.set_index(node_id_field, drop=False)
#     nodes_fixed.update(best_candidates)

#     return nodes_fixed