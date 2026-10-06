# this facilitates lazy-loading rasterio
# a known conflict occurs on some windows devices where software that uses GDAL is installed, in which DLLs are loaded from outside the scope of the conda environment.
# in this case, a special launcher is provided that fixes this issue, which must be used when using rasterio on the device.

_rio = None

def get_rasterio():
    global _rio

    if _rio is not None:
        return _rio

    try:
        import rasterio
        _rio = rasterio
        return _rio

    except ImportError as e:
        raise ImportError(
            "NWTrace could not import Rasterio. "
            "This may be caused by a known DLL conflict with "
            "PCI Geomatics CATALYST Professional. "
            "Try launching Python/Jupyter using the NWTrace launcher."
        ) from e