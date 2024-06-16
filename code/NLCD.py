# This script is used for getting shared cultivated crop layer from 2016 NLCD and the 2017 CDL datasets, 
# as  NLCD 2016 has 18% less cropland when compared to the USDA census estimate (Valayamkunnath et al.,2020)
# And use the shared layer, combining with AgTile-US.tif (Valayamkunnath et al.,2020), to get potentila tile and non-tile raster area, which used for get ground truth points. 

"""
@author: WANLUWEN
"""
# Set environment settings 
import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
env.workspace = r'S:\Users\luwen\Tile_Mapping_States\CropMask'  
# set some defaults 
arcpy.env.overwriteOutput = 1
# arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("Albers Equal-Area Conic")  # Albers Equal-Area Conic  
arcpy.env.outputCoordinateSystem = 4269  
arcpy.env.compression = 'LZW'    # Lossless compression preserves all raster cell val
arcpy.env.cellsize = 30 
tile_bdy = r"S:\Users\luwen\Tile_Mapping_States\CropMask\CDL_2017_tile_bdy_01.tif"
arcpy.env.extent = tile_bdy
# arcpy.env.snapRaster = tile_bdy
arcpy.env.outputCoordinateSystem = tile_bdy


################# extract 2017 CDL #################
inRaster = r"S:\Data\GIS_Data\Downloaded\NASS_Cropland_Data_Layers\CDL_Geodatabase.gdb\CDL_all_states_2017"
inMaskData = tile_bdy
outExtractByMask = ExtractByMask(inRaster, inMaskData)
outExtractByMask.save("CDL_2017_tile_bdy.tif")


################# extract 2017 NLCD #################
inRaster = r"S:\Data\GIS_Data\Downloaded\NLCD\Landcover\NLCD_2016_Land_Cover_L48_20190424.img"
inMaskData = tile_bdy
outExtractByMask = ExtractByMask(inRaster, inMaskData)
outExtractByMask.save("NLCD_2017_tile_bdy.tif")


################# extract a layer overlaped cultivated cropland in CDL and NLCD  #################
# make a layer based on NLCD,  Cultivated Crops as 1, other land use types as 0. 
with arcpy.EnvManager(scratchWorkspace=r"S:\Users\luwen\Tile_Mapping_States\TileDrainage\TileDrainage.gdb", 
                      workspace=r"S:\Users\luwen\Tile_Mapping_States\TileDrainage\TileDrainage.gdb"):
    out_raster = arcpy.sa.Con("NLCD_2017_tile_bdy.tif", 1, 0, "Value = 82");  # 82 Cultivated Crops -areas used for the production of annual crops, such as corn, soybeans, vegetables, tobacco, and cotton, and also perennial woody crops such as orchards and vineyards. 
    out_raster.save(r"S:\Users\luwen\Tile_Mapping_States\CropMask\NLCD_2017_tile_bdy_01.tif")

# https://www.nass.usda.gov/Research_and_Science/Cropland/metadata/2017_cultivated_layer_metadata.htm
# USDA, NASS Cropland Data Layer categories considered non-cultivated: from 37 to 195
# make a layer based on CDL,  Cultivated Crops as 1, other land use types as 0. 
with arcpy.EnvManager(scratchWorkspace=r"S:\Users\luwen\Tile_Mapping_States\TileDrainage\TileDrainage.gdb",
                      workspace=r"S:\Users\luwen\Tile_Mapping_States\TileDrainage\TileDrainage.gdb"):
    out_raster = arcpy.sa.Con("CDL_2017_tile_bdy.tif", 0, 1, "Value = 37 Or Value = 59 Or Value = 60 Or Value = 63 Or Value = 64 Or Value = 65 Or Value = 81 Or Value = 82 Or Value = 83 Or Value = 87 Or Value = 88 Or Value = 92 Or Value = 111 Or Value = 112 Or Value = 121 Or Value = 122 Or Value = 123 Or Value = 124 Or Value = 131 Or Value = 141 Or Value = 142 Or Value = 143 Or Value = 152 Or Value = 176 Or Value = 190 Or Value = 195");
    out_raster.save(r"S:\Users\luwen\Tile_Mapping_States\CropMask\CDL_2017_tile_bdy_01.tif")

# Description: Multiplies the values of two rasters on a cell-by-cell basis.
# Requirements: Image Analyst Extension
# Set local variables
inRaster = Raster("CDL_2017_tile_bdy_01.tif")
inRaster2 = Raster("NLCD_2017_tile_bdy_01.tif")
outRaster = inRaster * inRaster2
outRaster.save("NLCD_times_CDL_2017_tile_bdy.tif")

################# ExtractByMask: US-AgTile by tileboundary  ######################################
##################################################################################################
inRaster = "S:/Users/luwen/Tile_Mapping_States/ExistingData/AgTile-US/TIFF/AgTile-US.tif"
outExtractByMask = ExtractByMask(inRaster, tile_bdy)
outExtractByMask.save("AgTile-US_tile_bdy.tif")


################## expand 1 cell, = 30 meter  ######################################
###################################################################################################
out_raster = arcpy.sa.Expand("AgTile-US_tile_bdy.tif", 1, [1], "MORPHOLOGICAL");
out_raster.save(r"S:\Users\luwen\Tile_Mapping_States\CropMask\AgTile-US_tile_bdy_expand30m.tif")

out_raster = arcpy.sa.Expand("AgTile-US_tile_bdy.tif", 4, [1], "MORPHOLOGICAL"); 
# 4 is the number of cells, so 120m. 
# [1] is the list of zone values to expand.The zone values must be integers. They can be in any order.
out_raster.save(r"S:\Users\luwen\Tile_Mapping_States\CropMask\AgTile-US_tile_bdy_expand120m.tif")
# Morphological —Uses a mathematical morphology method to expand the zones. This is the default.


################# Get potentila non-tile raster area  ######################################
##################################################################################################
# Description: Find areas of cultivated cropland identified by CDL and NLCD, but exclude areas identified as tiled by US-AgTile.tif 
# two different rasters are used to create the conditional raster.
inRaster1 = Raster("NLCD_times_CDL_2017_tile_bdy.tif")
inRaster2 = Raster("AgTile-US_tile_bdy_expand30m.tif")
outCon = Con(((inRaster1 == 1) & (inRaster2 == 0)), 1, 0)
outCon.save("Nontile_bdy.tif")

inRaster1 = Raster("NLCD_times_CDL_2017_tile_bdy.tif")
inRaster2 = Raster("AgTile-US_tile_bdy_expand120m.tif")
outCon = Con(((inRaster1 == 1) & (inRaster2 == 0)), 1, 0)
outCon.save("Nontile_bdy_expand120m.tif")

################# Get potentila tile raster area  ######################################
##################################################################################################
inRaster1 = Raster("NLCD_times_CDL_2017_tile_bdy.tif")
inRaster2 = Raster("AgTile-US_tile_bdy.tif")
outCon = Con(((inRaster1 == 1) & (inRaster2 == 1)), 1, 0)
outCon.save("Tile_bdy.tif")