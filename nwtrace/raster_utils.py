
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import rasterio as rio

class conversions():

    whitebox_to_general = {
        0:   "SNK",   # Sink
        1:   "NE",
        2:   "E",
        4:   "SE",
        8:   "S",
        16:  "SW",
        32:  "W",
        64:  "NW",
        128: "N"
    }

    general_to_saga = {
        "SNK": -1,
        "NE":   1,
        "E":    2,
        "SE":   3,
        "S":    4,
        "SW":   5,
        "W":    6,
        "NW":   7,
        "N":    0
    }

    whitebox_to_saga = {
        0:   -1,   # Sink
        1:   1,   # NE
        2:   2,   # E
        4:   3,   # SE
        8:   4,   # S
        16:  5,   # SW
        32:  6,   # W
        64:  7,   # NW
        128: 0    # N
    }

    saga_to_whitebox = {
        -1:   0,   # Sink
        1:   1,   # NE
        2:   2,   # E
        3:   4,   # SE
        4:   8,   # S
        5:  16,   # SW
        6:  32,   # W
        7:  64,   # NW
        0: 128    # N
    }
    
    saga_to_vector = {
        -1:   (0,0),   # Sink
        1:   (-1,1),   # NE
        2:   (0,1),   # E
        3:   (1,1),   # SE
        4:   (1,0),   # S
        5:  (1,-1),   # SW
        6:  (0,-1),   # W
        7:  (-1,-1),   # NW
        0: (-1,0)    # N
    }
    
    whitebox_to_vector = {
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

# raster display (for example rasters, will not look nice on very large files)

def display_raster(ras, cmap="viridis", label_table=None):
    
    if isinstance(ras, (str, Path)):

        with rio.open(ras) as src:
            ras = src.read(1)
    
    plt.imshow(ras, cmap=cmap)

    nrows = np.shape(ras)[0]
    ncols = np.shape(ras)[1]

    for r in range(nrows):
        for c in range(ncols):
            if label_table is None:
                plt.text(c,r,f"{ras[r,c]:.0f}", ha="center", va="center", color="black")
            else:
                plt.text(c,r,f"{label_table[ras[r,c]]}", ha="center", va="center", color="black")

    plt.gca().set_xticks(np.arange(-0.5, ncols, 1))
    plt.gca().set_yticks(np.arange(-0.5, nrows, 1))

    plt.gca().get_xaxis().set_ticklabels([])
    plt.gca().get_yaxis().set_ticklabels([])

    plt.grid(color="k", linewidth=0.5)
    plt.colorbar()

    plt.show()

# uses arrows to show cell direction given a D8 raster
def display_raster_direction(dir_ras, base_ras=None, cmap="viridis", d8_vector_conversion=conversions.whitebox_to_vector):
    
    if isinstance(dir_ras, (str, Path)):

        with rio.open(dir_ras) as src:
            dir_ras = src.read(1)
    
    nrows = np.shape(dir_ras)[0]
    ncols = np.shape(dir_ras)[1]

    if not isinstance(base_ras, (np.ndarray)):
        plt.imshow(dir_ras, cmap=cmap)
    else:
        plt.imshow(base_ras)

    U = np.zeros_like(dir_ras)
    V = np.zeros_like(dir_ras)

    for r in range(nrows):
        for c in range(ncols):
            code = int(dir_ras[r,c])

            dr, dc = d8_vector_conversion[code]

            V[r,c] = dr
            U[r,c] = dc

    plt.quiver(
        np.arange(ncols),
        np.arange(nrows),
        U, -V,
        pivot="middle",
        color="white",
        scale=2,
        scale_units="xy"
    )

    plt.gca().set_xticks(np.arange(-0.5, ncols, 1))
    plt.gca().set_yticks(np.arange(-0.5, nrows, 1))
    plt.grid()

    plt.gca().get_xaxis().set_ticklabels([])
    plt.gca().get_yaxis().set_ticklabels([])

    plt.show()