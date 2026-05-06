from setuptools import setup, find_packages

setup(
    name='nwtrace',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
      "geopandas",
      "pandas",
      "tqdm",
      "rasterio",
      "whitebox"
    ]
)