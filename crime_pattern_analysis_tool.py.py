#---------------------------------------------------------------------------------------
# Name:        Assignment Four
#
# Purpose:     The purpose of this assignment is to create a custom tool that allows for
#              users to input information and determines results for a number of crime
#              types.
#
# Author:      Laniah Ohman
#
# Created:     01-07-2026
# Copyright:   (c) lania 2026
#---------------------------------------------------------------------------------------

### Initial Set-up
# Import stuff
import arcpy, os
from arcpy.sa import *

# Environment set up
#arcpy.env.workspace = r"C:\GEOS456\Assignment04_Data\City_of_Nice_Place.gdb"
#arcpy.env.overwriteOutput = True

# Check out the spatial analyst extension
arcpy.CheckOutExtension("Spatial")
print("Spatial analyst extension checked out and ready to use")

# Original geodatabase path
gdb = arcpy.GetParameterAsText(0)

# Making a copy path of the geodatabase to ensure raw data is not changed
gdb_FC = os.path.join(os.path.dirname(gdb), "Assign04.gdb")

# Delete the old geodatabase if the copy exits
if arcpy.Exists(gdb_FC):
    arcpy.management.Delete(gdb_FC)
    print("GDB deleted")

# Copy geodatabase to the new path
arcpy.management.Copy(gdb, gdb_FC)

# Resetting the environment to the copied geodatabase
gdb_path = gdb_FC
arcpy.env.workspace = gdb_path
arcpy.env.overwriteOutput = True

# Create list for shapefile in main path
fcList = arcpy.ListFeatureClasses()
print(fcList)

# Create list for crimes path
Crimes = []

#Store the crime type paths in the pre created lists
Input1 = arcpy.GetParameterAsText(1)
Input2 = arcpy.GetParameterAsText(2)
Input3 = arcpy.GetParameterAsText(3)
Crimes.append(Input1)
Crimes.append(Input2)
Crimes.append(Input3)
#Crimes.append(os.path.join(r"C:\GEOS456\Assign04\Assign04.gdb\Arsons"))
#Crimes.append(os.path.join(r"C:\GEOS456\Assign04\Assign04.gdb\Assault"))
#Crimes.append(os.path.join(r"C:\GEOS456\Assign04\Assign04.gdb\burglaries"))
fields = [f.name for f in arcpy.ListFields(os.path.join(gdb_path, "Precincts"))]
print("Fields in surf_lsd_join:", fields)
print(Crimes)

# Make precincts a layer
arcpy.management.MakeFeatureLayer (os.path.join(gdb_path, "Precincts"), "Precincts_Layer")

### Question One
# Intersecting each crime type with the precincts
for C in Crimes:
    # Creating a name for the feature layer
    Crbase = os.path.basename(C)
    Crime_path = os.path.join(gdb_path, "{0}_Precincts".format(Crbase))
    # Save the intersected feature layer
    arcpy.analysis.SpatialJoin(C, "Precincts_Layer", Crime_path, "JOIN_ONE_TO_ONE", "KEEP_ALL")
    # Creating table names
    Crime_table = os.path.join(gdb_path, "{0}_Table".format(Crbase))
    Crime_table_Ac = os.path.join(gdb_path, "{0}_Ac_Table".format(Crbase))
    # Creating a field for frequency
    Frequency = ["Precinct"]
    # Determine the frequency of crimes in precincts
    arcpy.analysis.Frequency(Crime_path, Crime_table, Frequency)
    # Sort the table by ascending frequency
    Sort = [["FREQUENCY", "ASCENDING"]]
    arcpy.management.Sort(Crime_table, Crime_table_Ac, Sort)
    arcpy.management.Delete(Crime_table)
    # 2. Automatically print the contents of the newly created table
    print(f"\n--- Results Table: {Crime_table_Ac} ---")
    print(f"{'PRECINCT':<20} | {'FREQUENCY'}")  # Column Headers
    print("-" * 35)

    # The Frequency tool always outputs a field named 'FREQUENCY'
    fields_to_print = ["Precinct", "FREQUENCY"]

    with arcpy.da.SearchCursor(Crime_table_Ac, fields_to_print) as cursor:
        for row in cursor:
            # <20 aligns text to the left with a width of 20 spaces for clean columns
            print(f"{str(row[0]):<20} | {row[1]}")

### Question Two
# How many assaults occur within 250m of a landmark
# Creating a 250m buffer around landmarks
# Defining input, output and distance
Input = os.path.join(gdb_path, "Landmarks")
Assault = os.path.join(gdb_path, "Assault")
Landmark_buffer = os.path.join(gdb_path, "Landmark_buffer")
Buffer_distance = arcpy.GetParameterAsText(4) #"250 Meters"
arcpy.analysis.Buffer(Input, Landmark_buffer, Buffer_distance)
fields1 = [f.name for f in arcpy.ListFields(Landmark_buffer)]
print("Fields in surf_lsd_join:", fields1)
# Creating path for assaults in the buffer area
Assault_path = os.path.join(gdb_path, "Assaults_Buffer")
# Save the intersected feature layer
arcpy.analysis.SpatialJoin(Landmark_buffer, Assault, Assault_path, "JOIN_ONE_TO_ONE", "KEEP_ALL", match_option = "INTERSECT")
fields2 = [f.name for f in arcpy.ListFields(Assault_path)]
print("Fields in surf_lsd_join:", fields2)
# Create a table with the join_count and landname
Landmark_Assault_Table = os.path.join(gdb_path, "Landmark_Assault_Table")
# Create table for ascending
Landmark_Assault_Ac_Table = os.path.join(gdb_path, "Landmark_Assault_Ac_Table")
# Run the export tool
arcpy.conversion.TableToTable(Assault_path, gdb_path, "Landmark_Assault_Table")
# Sort the table by ascending frequency
Sort = [["Join_Count", "ASCENDING"]]
arcpy.management.Sort(Landmark_Assault_Table, Landmark_Assault_Ac_Table, Sort)
arcpy.management.Delete(Landmark_Assault_Table)
# In the vicinity of which landmark is an assault most likely to occur
# Creating an empty max count
max_count = None
max_landmark = []
scursor = arcpy.da.SearchCursor(Assault_path,["LANDNAME", "Join_Count"])
for row in scursor:
    if max_count is None or row[1] > max_count:
        max_count = row[1]
        max_landmark = [row[0]]
    # Check if another landmark has the same number of assaults
    elif row[1] == max_count:
        max_landmark.append(row[0])
arcpy.AddMessage(f"There are {max_count} assaults in {max_landmark}")
