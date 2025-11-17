# Import the submodules
from .trace_sewershed import NWTrace
from .utils import (
    dfs,
    dfs_directed,
    dfs_recursive,
    dfs_directed_recursive
)

# Define the __all__ variable
__all__ = [NWTrace, utils]

version = "0.0.1"