#---------------------------------------------------------------------------------------
# Name:        UWI linking python script
# Purpose:     To be used by the C# add-in. Takes the points that were clicked and
#              determines the DLS location of each one. Builds the UWI from the
#              last point selected and pulls the fields from the excel table. Based on 
#              previous script that links an excel sheet to a set of spatial data.
#
# Author:      Group 2 ====> Apram Singh, Nelson Ngajip, Laniah Ohman
#
# Created:     14-07-2026
# Copyright:   (c) lania 2026
# Licence:     <your licence>
#---------------------------------------------------------------------------------------

# Initial Set-up
# Import stuff
import arcpy, os, pandas as pd

# Environment set up
arcpy.env.workspace = r"C:\GEOS459"
arcpy.env.overwriteOutput = True

# Paths to data
# Define the path for the geodatabase
gdb_path = r"C:\GEOS459\Sticks.gdb"
# Define the path for the LSD
lsd_fc = os.path.join(gdb_path, "V4_1_LSD")
# Define path for the output excel as a table
excel_table = os.path.join(gdb_path, "Table_Info")
# Holding all fields and UWI from the last point created in a table
results_table = os.path.join(gdb_path, "Results_Table")

# Definition to determine the intersection of the point with LSD
def dls_point_location(x, y, lsd_layer):
    # Defining the spatial reference
    sr = arcpy.SpatialReference(26911)
    # Creating the point and the geometry
    point = arcpy.Point(x, y)
    point_geom = arcpy.PointGeometry(point, sr)

    # Search cursor to find the intersection
    scursor = arcpy.da.SearchCursor(lsd_layer, ["DLS"], spatial_filter = point_geom, spatial_relationship = "INTERSECTS")
    for row in scursor:
        return row[0]
    return None

# Deinition that return the excel field names
def excel_lookup(bh_dls, excel_tbl, key_field = "bh_DLS"):
    # Create a list with all excel fields
    all_fields = [f.name for f in arcpy.ListFields(excel_tbl)]
    # Creates a list of fields that are not OBEJECTID, FID, or bh_DLS
    data_fields = [f for f in all_fields if f not in ("OBJECTID", "FID", key_field)]

    # If there is a value then we remove leading and trailing whitespaces, otherwise retuen none
    target = bh_dls.strip().upper() if bh_dls else None

    # Read through the excel file
    scursor = arcpy.da.SearchCursor(excel_tbl, [key_field] + data_fields)
    for row in scursor:
        row_dls = row[0].strip().upper() if row[0] else None
        # If there is a match then all popuklated fields are pulled as is
        if row_dls == target:
            return dict(zip(data_fields, row[1:]))

    # If not match found still return every field just with null values
    return {field: None for field in data_fields}

# Definition to return the UWI for the last point
def process_points(points_xy):
    # Call the above definition using the lsd_fc as the value
    point_dls = [dls_point_location(x, y, lsd_fc) for x, y in points_xy]
    # Last clicked point => bottom hole
    bh_dls = point_dls[-1]
    arcpy.AddMessage(f"Bottom hole DLS: {bh_dls}")
    # Specifying what happens if the bottom hole is not in a LSD polygon
    if bh_dls is None:
        raise ValueError("The bottom hole is not within an LSD, recheck point placement")

    # Specifying the UWI format
    UWI = f"100/{bh_dls}/00"
    # Pulling above definition to chech for matching excel fields
    excel_fields = excel_lookup(bh_dls, excel_table)

    # Return the DLS, UWI and Excel fields
    return{"point_dls": point_dls, "UWI": UWI, "excel_fields": excel_fields}

# Definition to write the results to a table that can then be parsed in the c# add-in
def result_to_table(result, out_table):
    # Delete the table if it already exists
    if arcpy.Exists(out_table):
        arcpy.management.DeleteRows(out_table)
    else:
        # Set the workspace path
        out_workspace, out_name = os.path.split(out_table)
        # Create the table
        arcpy.management.CreateTable(out_workspace, out_name)
        # Add field to the table for UWI
        arcpy.management.AddField(out_table, "UWI", "TEXT", 100)

    # Get existing fields
    existing_fields = [f.name for f in arcpy.ListFields(out_table)]

    # Add fields for the excel table
    for field_name in result["excel_fields"]:
        field_name = field_name[:64]

        if field_name not in existing_fields:
            arcpy.management.AddField(out_table, field_name[:64], "TEXT", 254) # Takes the first 64 characters

    # Build a list of column names including the UWI and excel fields
    field_names = ["UWI"] + list(result["excel_fields"].keys())
    # Build two lists joined together with the UWI and converts all non null values in the excel table to strings and empty fields with blank strings
    row_values = [result["UWI"]] + [str(v) if v != None else "" for v in result["excel_fields"].values()]

    icursor = arcpy.da.InsertCursor(out_table, field_names)
    icursor.insertRow(row_values)
    del icursor

# Script tool entry point
def execute(points_param):
    arcpy.AddMessage("=== TOOL STARTED ===")
    arcpy.AddMessage(f"Input points: {points_param}")
    # Remove leading and trailimg white spaces and break into list at each semi colon
    pairs = points_param.strip().split(";")
    # Empy list to hold x and y coordinates
    points_xy = []
    for pair in pairs:
        x_str, y_str = pair.strip().split(" ")
        points_xy.append((float(x_str), float(y_str)))

    result = process_points(points_xy)
    result_to_table(result, results_table)
    arcpy.AddMessage(f"Writing UWI: {result['UWI']}")
    arcpy.AddMessage("=== TOOL FINISHED ===")
    return result

# Adding entry point for toolbox in arcGIS
if __name__ == "__main__":
    points_param_text = arcpy.GetParameterAsText(0)
    result = execute(points_param_text)
    arcpy.AddMessage(f"UWI resolved: {result['UWI']}")
