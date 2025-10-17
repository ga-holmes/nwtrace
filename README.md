# nwtrace (NetWork Trace)
This tool is designed to build connected graphs from user-input data and traverse them in order to find subsets that are connected to target nodes. 

### Information

It's designed with spatial data in mind, meaning you can import a csv or vector data with the requisite IDs and connecting node IDs and create a connected network that can be easily traversed. There are tools that allow you to input a subset of nodes and get back a list of nodes and connections that are connected to it.

The tool was made specifically to trace sewer networks and delineate sewersheds based on outfalls, maintenance holes, etc., so sever tools exist that are specific to that use-case. However, this can be expanded to work with any other utility or system that can be represented as a connected graph (lines connected by nodes).

---

This tool is a work-in-progress and therefore several features are not implemented, and the current scope of the project is small.

### Features & TODO
- [x] Create connected graphs from csv or other geospatial files
- [x] Travese networks and return subsets of connected features
- [] Add tools to verify spatial geometry
- [] Generalize to other use-cases
- [] refactor to proper library form
