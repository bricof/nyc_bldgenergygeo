# Mapping NYC Building Footprints and Energy Data

The [notebook](https://github.com/bricof/nyc_bldgenergygeo/blob/master/nyc_bldgenergygeo.ipynb) combines building geometries and energy consumption information from publicly available New York City data, and then exports data to GeoJSON and TopoJSON formats for interactive visualization with d3 (see the index.html and graph.js files).

Most of the heavy lifting is done by Pandas. GeoPandas is used to help manage the geometry data. You will need both of these installed in order to run this code. To perform the GeoJSON to TopoJSON conversion at the very end of the notebook then you will also need to have TopoJSON installed.

