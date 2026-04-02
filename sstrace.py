import os
from nwtrace import NWTrace
import pandas as pd
import geopandas as gpd

network_path = "data/sewer_test.geojson"

multiple = True
upstream_only = True
downstream_only = False
verbose = True

sewer_id_field = 'Sewer Gravity Asset Identification'
upstream_field = 'Sewer Gravity Upstream Maintenance Hole'
downstream_field = 'Sewer Gravity Downstream Maintenance Hole'

outfall_file = 'data/Outfalls_ID.csv'
id_field = 'ASSET_ID'

outfalls = pd.read_csv(outfall_file)[id_field].tolist()

target_endpoints = outfalls
# target_endpoints = ["JP5428128690"]

outputname_extra = "TEST_"
output_dir = f"./out"
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

result = []

# Initialize the object
sewershed = NWTrace(
    network=network_path,
    id_field=sewer_id_field,
    upstream_field = upstream_field,
    downstream_field = downstream_field,
    verbose=verbose,
    output_dir=output_dir,
)

# additional connections
fittings = gpd.read_file("data/additional_node.geojson")
nodes_up = (fittings[["FACILITYID", "TO_FIXED"]]
            .dropna(subset=["FACILITYID", "TO_FIXED"]) # remove rows with None values
            .rename(columns={"FACILITYID": 'node_id', "TO_FIXED": 'segment_id'})
            .set_index('node_id').to_dict(orient="index"))

sewershed.add_upstream_nodes(nodes_up)

catchbasin_leads = gpd.read_file("data/additional_segment.geojson")
new_segs = (catchbasin_leads[["FACILITYID", "UP_ASSET_ID", "DN_ASSET_ID"]]
            .rename(columns={"FACILITYID": 'segment_id', "UP_ASSET_ID": 'from', "DN_ASSET_ID": 'to'})
            .set_index('segment_id').to_dict(orient="index"))

sewershed.add_segments(new_segs)

if multiple == False:
    result = sewershed.trace_sewershed(
        target_endpoints[0], 
        upstream_only=upstream_only, 
        downstream_only=downstream_only
    )
else:
    result = sewershed.trace_sewersheds(
        target_endpoints, 
        upstream_only=upstream_only, 
        downstream_only=downstream_only, 
    )

# Convert to dataframe and output as a csv
out_df = pd.DataFrame.from_dict(result)
out_df.to_csv(
    f'{output_dir}/{outputname_extra}catchment_'
    f'{"singledir" if upstream_only or downstream_only else "multidir"}'
    f'{"_ups" if upstream_only and not downstream_only else ""}'
    f'{"_dwns" if downstream_only and not upstream_only else ""}_'
    f'{target_endpoints[0] if not multiple else outfall_file.replace("/", "_").replace(".", "_")}.csv'
)