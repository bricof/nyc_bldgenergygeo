
# coding: utf-8

## Background

# This script combines building geometries and energy consumption information from publicly available New York City data, and then exports data to GeoJSON and TopoJSON formats for interactive visualization with d3.

# Most of the heavy lifting is done by Pandas. GeoPandas is used to help manage the geometry data. You will need both of these installed in order to run this code. If you wish to perform the GeoJSON to TopoJSON included at the very end of this script then you will also need to have TopoJSON installed (notes are included for this below).

# In[1]:

import os, re
from pandas import *
from geopandas import *
pylab.rcParams['savefig.dpi'] = 100


## Data Collection and Tidying

### Building Geometry

##### Data Source

# The data for building footprints, heights and elevations was downloaded from NYC Open Data:
# 
# https://data.cityofnewyork.us/Housing-Development/Building-Footprints/tb92-6tj8
# 
# https://data.cityofnewyork.us/download/tb92-6tj8/application/zip
# 
# 
# The zip file contains a metadata file with some explanation of the data. The data is contained in a Shapefile.

##### Cleaning and Formatting

# Note that the building_1214_metadata.htm file that makes part of the downloaded zip describes a different map projection specification (in its 'well-known-text' field) than what is found in the building_1214.prj file. The metadata looks to be correct and the .prj file incorrect - the geometry data in the shape file is in feet rather than in longitude-latitude. So the 'well-known-text' field from the metadata file must be copied into the .prj file before reading the shape file with GeoPandas (else all variety of headaches arise when trying to translate and/or export to GeoJSON, as I discovered the hard way).
# 
# The shape file is 216 MB, so be prepared to wait for the following command - it takes about 4 minutes on my mac air.

# In[2]:

shpfile = 'building_footprints_shape_webmercator_12-14/building_1214.shp'
bldgs = GeoDataFrame.from_file(shpfile)


# In[3]:

print 'number of rows:\t' + str(len(bldgs))
print 'columns:\t' + str(bldgs.columns)
print 'crs:\t\t' + str(bldgs.crs) # projection info for the geometry data


# There are 1,082,381 buildings in this dataset. Note that the geometry values are in feet, using the EPSG 2263 projection (as specified in the source metadata file).
# 
# For clarity, we revise the table to only include the columns we are interested in. Note that 'BBL' stands for 'Burough - Block - Lot number'. This column is shared with the energy data described below, and will be used as a key for merging the tables, so we make it an index here. For convenience we add a new column 'boro' (keeping with traditional NY spelling) which contains the burough as a single-character string: '1'=Manhattan, '2'=Bronx, etc.

# In[4]:

def boronum(bbl):
    return int(bbl[0])
boro = bldgs['BBL'].apply(boronum)
bldgs['boro'] = boro
bldgs = bldgs[['BBL','boro','GROUND_ELE','HEIGHT_ROO','Shape_Area','Shape_Leng','geometry']]
bldgs.set_index('BBL', inplace=True)
bldgs.sort(inplace=True)
bldgs.head()


# Although Cartesian geometry in feet is useful for many purposes, it is not great for browser-based mapping with standard js libraries which expect geometries in longitude-latitude. We thus add a new column with the geometry projected to EPSG 4326, which is the standard geo description used in browser-based mapping.

# In[5]:

bldgs['geometry_latlon'] = bldgs['geometry'].to_crs(epsg=4326)
bldgs.head()


# Note the problem here though. These first few buildings in the dataset are located on Governor's Island (just south of the island of Manhattan), and we know that the longitude and latitude of the center of the island is 40.6914° N, 74.0161° W (ref: [google search](https://www.google.com/search?q=nyc+lat+long&ie=utf-8&oe=utf-8#q=nyc+governor%27s+island+lat+long)), but our conversion notes them as approximately 48.1° N, 112.7° W. Further investigation of the graphs (below) suggests that the result is also rotated. Something is incorrect about this conversion - if I figure out what, I will post a revision to this document. But for the immediate purposes of data visualization we can use the conversion as it stands, since the resulting maps look to be generally correct, just translated and rotated (or possibly scaled improperly).

# In[27]:

# notes for further investigation of the conversion issue: 
#  GeoPandas uses pyproj; the code below provides an initial suggestion that something might be amiss with the units handling
#
#import pyproj
#x1 = -8239895.129312261
#y1 = 4966979.423426831
#wgs84 = pyproj.Proj("+init=EPSG:4326") # LatLon with WGS84 datum used by GPS units and Google Earth
#epsg2263 = pyproj.Proj("+init=EPSG:2263",preserve_units=True) # local NYC coordinate system
#print pyproj.transform(epsg2263, wgs84, x1, y1)
#conv = 0.3048
#print pyproj.transform(epsg2263, wgs84, x1*conv, y1*conv)
#
# outputs:
# (-112.67577507532987, 48.093410208201874)
# (-87.23011424552195, 43.594327921961934)


##### Quick Verification

# A couple of quick graphs to ensure that the data format is roughly as expected.

# In[7]:

bldgs.head(500).plot()


# In[8]:

bldgs[bldgs.boro == 1].plot()


#### Energy Consumption Data

##### Data Source

# Energy consumption data is available for a subset of the buildings via NYC Open Data, and was downloaded in csv form:
# 
# https://data.cityofnewyork.us/Environment/Energy-and-Water-Data-Disclosure-for-Local-Law-84-/5gde-fmj3
# 
# 
# This dataset contains annual energy and water consumption data for buildings in New York City that have greater than 50,000 square feet of floor area, as per the disclosure specifications in [NYC Local Law 84](http://www.nyc.gov/html/gbee/html/plan/ll84_about.shtml).

##### Cleaning and Formatting

# The csv file presents one major challenge before it can be read by Pandas. The last data column in the csv occasionally has newline characters within it - in these cases, the data entry is held within double quotes. In this cleaning script, these intra-entry newline characters are replaced by single space (' ') characters. The script also removes some unnecessary white space from the csv. A new 'cleaned' csv file is produced.

# In[9]:

filename = 'Energy_and_Water_Data_Disclosure_for_Local_Law_84__2012_.csv'
cleanedcsv = ''
multilinekeeper = ''
with open(filename,'rU') as f:
    for line in f:
        line = re.sub(' +',' ',line)
        line = re.sub(', ',',',line)
        if multilinekeeper == '':
            if len(re.findall('"',line)) == 1:
                multilinekeeper = line.strip()
            else:
                cleanedcsv += line
        else:
            if '"' in line:
                cleanedcsv += multilinekeeper + line
                multilinekeeper = ''
            else:
                multilinekeeper += ' ' + line.strip()
                
with open('cleaned_' + filename,'w') as f:
    f.write(cleanedcsv)


# The cleaned csv can now be read into a dataframe by Pandas.

# In[10]:

energy = read_csv('cleaned_' + filename)
print 'number of rows:\t' + str(len(energy))
print 'columns:'
print energy.columns


# Note that the number of entries in this table (14,112) is much smaller than the number of entries in the buildings table (1,082,381), since it only contains entries for buildings with more than 50,000 ft2 of floor area.
# 
# The BBL column was read in as integers, but want it to be strings in order to to compare with the bldgs BBL key. For clarity, we also take only the subset of data columns we are interested in, and we set the 'BBL' column to be the index.

# In[11]:

energy['BBL'] = energy['BBL'].astype(str)
energy = energy.ix[:,[0,1,2,7,8,11,12,13,14,15]]
energy.set_index('BBL', inplace=True)
energy.sort(inplace=True)
energy.head()


##### Quick Verification

# In[12]:

energy.plot(x=2,y=5,kind='scatter')


#### Merging Data Tables

# An outer merge brings the two data tables together. For convenience, we add two new columns to denote which original tables had which entries (which will let us subset data when desired, akin to taking an inner merge but without duplication). Note that the merge results in a Pandas DataFrame object, rather than a GeoPandas GeoDataFrame object.

# In[13]:

bldgsenergy = merge(bldgs, energy, left_index=True, right_index=True, how='outer')


# In[14]:

print 'number of rows:\t' + str(len(bldgsenergy))
print 'columns:'
print bldgsenergy.columns
bldgsenergy.ix[:,['HEIGHT_ROO','geometry','geometry_latlon','Site EUI(kBtu/ft2)','Total GHG Emissions(MtCO2e)',
                  'Number of Buildings']].head()


# In[15]:

def inbldgs(i):
    return i in bldgs.index
def inenergy(i):
    return i in energy.index
bldgsenergy['geometry_avail'] = Series(bldgsenergy.index,index=bldgsenergy.index).apply(inbldgs)
bldgsenergy['energy_avail'] = Series(bldgsenergy.index,index=bldgsenergy.index).apply(inenergy)
bldgsenergy.ix[:,['geometry_avail','energy_avail','HEIGHT_ROO','geometry','geometry_latlon','Site EUI(kBtu/ft2)',
                  'Total GHG Emissions(MtCO2e)','Number of Buildings']].head()


# In[16]:

print 'number of rows in bldgs:\t\t\t\t\t' + str(len(bldgs))
print 'number of rows in energy:\t\t\t\t\t' + str(len(energy))
print 'number of rows in bldgsenergy:\t\t\t\t\t' + str(len(bldgsenergy))
print 'number of rows in bldgsenergy with geometry:\t\t\t' + str(len(bldgsenergy[bldgsenergy['geometry_avail']]))
print 'number of rows in bldgsenergy with energy:\t\t\t' + str(len(bldgsenergy[bldgsenergy['energy_avail']]))
print 'number of rows in bldgsenergy with both gometry and energy:\t' +                             str(len(bldgsenergy[bldgsenergy['energy_avail'] & bldgsenergy['geometry_avail']]))


##### Summary and Notes

# We now have a tidy data table in the variable 'bldgsenergy'. A note for further investigation later, if this data is to be used for further analysis: there look to be a lot of buildings that share a BBL identifier, which will likely cause some hassles.

## GeoJSON Export and TopoJSON Conversion

# For the d3 visualization, we will use just a small section of the city, and will only consider those buildings for which we have both geometry data and energy data.

# In[17]:

bldgsenergygeo = GeoDataFrame(bldgsenergy[bldgsenergy['geometry_avail'] & bldgsenergy['energy_avail']])


# In[18]:

bldgsenergygeo.head(500).plot()


# For the GeoJSON export, we will use the latitude and longitude as the geometry.

# In[19]:

bldgsenergygeo.rename(columns={'geometry':'geometryfeet'}, inplace=True)
bldgsenergygeo.rename(columns={'geometry_latlon':'geometry'}, inplace=True)


# In[20]:

bldgsenergygeo.head(500).plot()


# In the interactive graph, we want to have the address variables reformatted to a single column of strings.

# In[21]:

bldgsenergygeo['Address'] = bldgsenergygeo['Street Number'] + ' ' + bldgsenergygeo['Street Name']


# We want to keep the file size to a minimum in order to keep the graph interaction smooth, so we will only include the columns we will use.

# In[22]:

bldgsenergygeo.columns


# In[23]:

bldgsenergygeo = bldgsenergygeo.ix[:,[0,2,6,9,10,11,12,13,14,18]]
bldgsenergygeo.head()


# For the graph, we are only interested in a region roughly correlated with Midtown in Manhattan - we will select only those rows for which boro = 1 and they have points between 48.117 and 48.129 degrees latitude (noting that these are not the proper latitude numbers, given our earlier problem).

# In[24]:

bldgsenergygeomidtown = bldgsenergygeo[(bldgsenergygeo.boro == 1) & 
                                       (bldgsenergygeo.geometry.bounds['miny'] < 48.129) & 
                                       (bldgsenergygeo.geometry.bounds['maxy'] > 48.117) ]
print len(bldgsenergygeomidtown)
bldgsenergygeomidtown.head()


# In[25]:

with open('bldgsenergygeo.json','w') as f:
    f.write(bldgsenergygeomidtown.to_json())


# This writes a GeoJSON file for Manhattan to 'bldgsenergygeo.json' that can be used for browser-based mapping. For the d3.js interactive graph, the TopoJSON format is used because it is a smaller file format and thus allows for faster uploading and interaction. Converting between the GeoJSON file and the TopoJSON file is carried out using [this js library](https://github.com/mbostock/topojson), which requires node.js and is installed via 'sudo npm install topojson'. The conversion is carried out with the following command line call. The resulting file 'bldgsenergytopo.json' is 1.2 MB, compared with the 2.9 MB GeoJSON file.

# In[26]:

os.system('topojson -p -o bldgsenergytopo.json bldgsenergygeo.json')


# The html and js code for the graph is included in this [github repo](https://github.com/bricof/nyc_bldgenergygeo), and the graph can be viewed in this [blog post](http://briancoffey.ca/blogpost2.html).
