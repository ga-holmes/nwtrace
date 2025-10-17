# nwtrace (NetWork Trace)
This tool is designed to build connected graphs from user-input data and traverse them in order to find subsets that are connected to target nodes. 

It's designed with spatial data in mind, meaning you can import a csv or vector data with the requisite IDs and connecting node IDs and create a connected network that can be easily traversed. There are tools that allow you to input a subset of nodes and get back a list of nodes and connections that are connected to it.

The tool was made specifically to trace sewer networks and delineate sewersheds based on outfalls, maintenance holes, etc., so sever tools exist that are specific to that use-case. However, this can be expanded to work with any other utility or system that can be represented as a connected graph (lines connected by nodes).

---

This tool is a work-in-progress and therefore several features are not implemented, and the current scope of the project is small.

### Features & TODO
- [X] Create connected graphs from csv or other geospatial files
- [X] Travese networks and return subsets of connected features
- [X] Add environment tools / library requirements
- [ ] Refactor to object form
- [ ] Add tools to verify spatial geometry
- [ ] Generalize to other use-cases
- [ ] Add option to output to spatial data (apply the subnetwork to spatial data)
- [ ] Refactor to proper library form
- [ ] Add adjacent QGIS plugin

---

### Requirements
Python ~v3.13 is required. 
Required libraries are listed in the `requirements.txt` file. 

Conda is recommended as an environment manager for installing python libraries. Install [here](https://www.anaconda.com/docs/getting-started/miniconda/main).

- To create a conda environment:
`conda create --name nwtrace --file requirements.txt`

- To install directly to python using pip:
`pip install -r requirements.txt`

---

### Sample Data
Some sample files are included for testing the library yourself are provided. This includes a script (`sstrace.py`) and a notebook (`sstrace.ipynb`) that can be run as a python notebook in VSCode or software of your choice. The sample data should result in traced gravity main sewer networks from seven outfalls in the City of Toronto. A sample dataset is provided (`sewer_test.geojson`) which is a subset of the City of Toronto gravity main sewer network provided by [Open Data Toronto](https://open.toronto.ca/dataset/sewer-gravity-mains/), clipped to a subwatershed of the Humber River (Note that further analysis using this clipped data may result in errors where the traced network expands beyond the clip boundary).

The output can be visualized in a GIS software of your choice.

- To run the sample program, either use `sstrace.ipynb` in a software of your choice
**OR**
- Run `python sstrace.py` 

#### Instructions for QGIS

After the program is finished, an output `.csv` file will be generated named based on your input parameters.

- Open QGIS
- Add the sample sewer network file (`sewer_test.geojson`) to the map
- Add the output `.csv` file
- Right click on the `sewer_test` layer, select properties (or double click to open properties)
- Go to 'Joins'
- Click the '+' icon
- Select the `.csv` file as your Join Layer.
- For your fields to join on, Select 'segment_id' and 'Sewer Gravity Asset Identification'
- Click 'OK' and 'Apply'
- In the toolbar, click 'Select features by value'
- Scroll to '[csv filename].field_1
- Set selection to 'Not equal to', and type 'NULL' in the box
- Click 'Select Features'. The selected lines will represent the network as connected to the chosen outfalls!
- You can then extract this from the main file by running the 'Extract selected features' or right click the layer and export selected features.