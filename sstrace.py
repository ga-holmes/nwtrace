import os
from trace_sewershed import *
import pandas as pd

network_path = "data/sewer_test.geojson"

multiple = True
upstream_only = True
downstream_only = False
verbose = True

outfall_file = 'data/Outfalls_ID.csv'
id_field = 'ASSET_ID'

outfalls = pd.read_csv(outfall_file)[id_field].tolist()

target_endpoints = outfalls
# target_endpoints = ["JP5428128690"]

outputname_extra = "example2_"
output_dir = f"./out"
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

result = []

if multiple == False:
    result = trace_sewershed(network_path, target_endpoints[0], upstream_only=upstream_only, downstream_only=downstream_only, verbose=verbose)
else:
    result = trace_sewersheds(network_path, target_endpoints, upstream_only=upstream_only, downstream_only=downstream_only, verbose=verbose)
    
# Convert to dataframe and output as a csv
out_df = pd.DataFrame.from_dict(result)
out_df.to_csv(f'{output_dir}/{outputname_extra}catchment_{"singledir" if upstream_only or downstream_only else "multidir"}{"_ups" if upstream_only and not downstream_only else ""}{"_dwns" if downstream_only and not upstream_only else ""}_{target_endpoints[0] if not multiple else outfall_file.replace('/', '_').replace('.', '_')}.csv')

