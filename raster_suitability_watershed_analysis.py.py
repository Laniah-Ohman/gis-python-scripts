#---------------------------------------------------------------------------------------
# Name:        Assignment #3
#
# Purpose:     The purpose of this assignment is to apply grid statistics to analyze
#              raster datasets using high-level programming (HLP) language through
#              geographic information system (GIS) extensions.
#
# Author:      Laniah Ohman
#
# Created:     15-07-2026
# Copyright:   (c) lania 2026
# Licence:     <your licence>
#---------------------------------------------------------------------------------------

### Initial Set-up
# Import stuff
import arcpy, os
from arcpy import env
from arcpy.sa import *

# Check out the spatial analyst extension
arcpy.CheckOutExtension("Spatial")
print("Spatial analyst extension checked out and ready to use")

# Environment set up
arcpy.env.workspace = r"C:\GEOS456\Assign02\Spatial_Decisions.gdb"
arcpy.env.overwriteOutput = True

# Use get messages to print geoproccesing tool messages
def messages():
    print(arcpy.GetMessage(0))
    count = arcpy.GetMessageCount()
    print(arcpy.GetMessage(count-1))

# Original geodatabase path
gdb = r"C:\GEOS456\Assign03\Spatial_Decisions.gdb"

# Making a copy of the geodatabase to ensure raw data is not changed
gdb_FC = r"C:\GEOS456\Assign02\Assign03.gdb"

# Delete the old geodatabase if the copy exits
if arcpy.Exists(gdb_FC):
    arcpy.management.Delete(gdb_FC)
    print("GDB deleted")

arcpy.management.Copy(gdb, gdb_FC)

gdb_path = r"C:\GEOS456\Assign02\Assign03.gdb"
arcpy.env.workspace = gdb_path
arcpy.env.overwriteOutput = True

# Creating path to dem raster
dem = r"C:\GEOS456\Assign02\Assign03.gdb\dem"
# Creating path to geolgrid raster
geolgrid = r"C:\GEOS456\Assign02\Assign03.gdb\geolgrid"

# Determining the data format, cell size and coordinate system of the dem raster
dem_desc = arcpy.Describe(dem)
# Getting the spatial reference
sr = dem_desc.SpatialReference

# Printing the data format
print("The data format of the dem raster is:{0}".format(dem_desc.format)) # FGDBR => File Geodatabase Raster
print("The cell size of the dem raster is:{0} X {1}".format(dem_desc.meanCellWidth, dem_desc.meanCellHeight))
print("The coordinate system of the dem raster is:{0}".format(sr.name))

# Using the dem and geolgrid to assign the following criteria
# Create slope from dem
slope = Slope(dem)
print("Slope being created.......")
messages()
# Save the slope raster
slope.save(r"C:\GEOS456\Assign02\Assign03.gdb\Slope")
print("Slope being saved.......")
messages()

# Define dem to work with raster calculator
demR = arcpy.Raster(r"C:\GEOS456\Assign02\Assign03.gdb\dem")

# Elevation Criteria (meters)
elev_crit = ((demR >= 1000) & (demR <= 1550)) # Elevation between 1000 and 1550 meters
# Save the elevation criteria raster
elev_crit.save(r"C:\GEOS456\Assign02\Assign03.gdb\Elevation_Criteria")
print("Elevation criteria being saved.......")
messages()

# Slope Criteria (degrees)
slope_crit = (slope <= 18) # Slope lesss than or equal to 18 degrees
# Save the slope criteria raster
slope_crit.save(r"C:\GEOS456\Assign02\Assign03.gdb\Slope_Criteria")
print("Slope criteria being saved.......")
messages()

# Creating path to geolgrid raster
geolgrid_raster = arcpy.Raster(r"C:\GEOS456\Assign02\Assign03.gdb\geolgrid")
# Geology criteria
geol_crit = (geolgrid_raster == 7) # Madison Limestone (Value 7 per excel)
# Save the geology criteria raster
geol_crit.save(r"C:\GEOS456\Assign02\Assign03.gdb\Geology_Criteria")
print("Geology criteria being saved.......")
messages()

# Combine all criteria rasters
crit_rast = ((elev_crit) * (slope_crit) * (geol_crit))
# Save the combined criteria raster
crit_rast.save(r"C:\GEOS456\Assign02\Assign03.gdb\Criteria_Raster")
print("Combined criteria being saved.......")
messages()

# Allows for height and width to be parsed
crit_rast_desc = arcpy.Describe(crit_rast)

# Determine the number of cells, area in square meters and average elevation
# Define input parameter path for zonal statitsics
OutTable = r"C:\GEOS456\Assign02\Assign03.gdb\Out_Table"

# Creating a zonal statistics table with all fields
OutZoneTable = ZonalStatisticsAsTable(crit_rast, "VALUE", demR, OutTable, "DATA", "ALL")
print("Zonal statistcs processing.......")
messages()

# Use a search cursor to read the statistics table
scursor = arcpy.da.SearchCursor(OutTable, ["VALUE", "COUNT", "AREA", "MEAN"])
for row in scursor:
    if row[0] == 1:
        cell_count = row[1]
        area = row[2]
        avg_elevation = row[3]

# Printing the number of cells
print("The total number of cells is:{0}".format(cell_count))
print("The area in meters squared is:{0}".format(cell_count*(crit_rast_desc.meanCellWidth*crit_rast_desc.meanCellHeight)))
print("The average elevation is:{0}".format(avg_elevation))

# Define path
watershed = r"C:\GEOS456\Assign02\Assign03.gdb\wshds2c"
# Create it as a layer
watershed_lyr = "watershed_lyr"
arcpy.management.MakeFeatureLayer(watershed, watershed_lyr)
print("Feature layer creating.......")
messages()
# Create layers for the 3 ID fields in wshds2c

# Watershed 291
# Select by the layer
arcpy.management.SelectLayerByAttribute(watershed_lyr, "NEW_SELECTION", "WSHDS2C_ID = 291")
print("Layer selecting.......")
messages()
# Save the layer as a feature class
arcpy.conversion.FeatureClassToFeatureClass(watershed_lyr, gdb_path, "Water_Shed")
print("Feature class creating.......")
messages()
# Build path
ws_291 = r"C:\GEOS456\Assign02\Assign03.gdb\Water_Shed"
# Define input parameter path for zonal statitsics
OutTable_291 = r"C:\GEOS456\Assign02\Assign03.gdb\Out_Table_291"
# Creating a zonal statistics table with all fields
OutZoneTable = ZonalStatisticsAsTable(ws_291, "WSHDS2C_ID", slope, OutTable_291, "DATA", "ALL")
print("Zonal statistcs processing.......")
messages()
# Use a search cursor to read the statistics table
scursor = arcpy.da.SearchCursor(OutTable_291, ["MEAN"])
for row in scursor:
    avg_slope = row[0]
print("The average slope for watershed 291 is:{0}".format(avg_slope))

# Watershed 313
# Select by the layer
arcpy.management.SelectLayerByAttribute(watershed_lyr, "NEW_SELECTION", "WSHDS2C_ID = 313")
print("Layer selecting.......")
messages()
# Save the layer as a feature class
arcpy.conversion.FeatureClassToFeatureClass(watershed_lyr, gdb_path, "Water_Shed")
print("Feature class creating.......")
messages()
# Build path
ws_313 = r"C:\GEOS456\Assign02\Assign03.gdb\Water_Shed"
# Define input parameter path for zonal statitsics
OutTable_313 = r"C:\GEOS456\Assign02\Assign03.gdb\Out_Table_313"
# Creating a zonal statistics table with all fields
OutZoneTable = ZonalStatisticsAsTable(ws_313, "WSHDS2C_ID", slope, OutTable_313, "DATA", "ALL")
print("Zonal statistcs processing.......")
messages()
# Use a search cursor to read the statistics table
scursor = arcpy.da.SearchCursor(OutTable_313, ["MEAN"])
for row in scursor:
    avg_slope = row[0]
print("The average slope for watershed 313 is:{0}".format(avg_slope))

# Watershed 525
# Select by the layer
arcpy.management.SelectLayerByAttribute(watershed_lyr, "NEW_SELECTION", "WSHDS2C_ID = 525")
print("Layer selecting.......")
messages()
# Save the layer as a feature class
arcpy.conversion.FeatureClassToFeatureClass(watershed_lyr, gdb_path, "Water_Shed")
print("Feature class creating.......")
messages()
# Build path
ws_525 = r"C:\GEOS456\Assign02\Assign03.gdb\Water_Shed"
# Define input parameter path for zonal statitsics
OutTable_525 = r"C:\GEOS456\Assign02\Assign03.gdb\Out_Table_525"
# Creating a zonal statistics table with all fields
OutZoneTable = ZonalStatisticsAsTable(ws_525, "WSHDS2C_ID", slope, OutTable_525, "DATA", "ALL")
print("Zonal statistcs processing.......")
messages()
# Use a search cursor to read the statistics table
scursor = arcpy.da.SearchCursor(OutTable_525

, ["MEAN"])
for row in scursor:
    avg_slope = row[0]
print("The average slope for watershed 313 is:{0}".format(avg_slope))