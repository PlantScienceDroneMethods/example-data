# Always remove outputs from layers panel before running script
# If editing things below, be careful to include the suffixes of your files (like “.tif”) and leave the quotes. Curly quotes are the default in some programs, they can make this fail, so copy and paste 
# The colon symbol in path names is problematic on Mac interface when routing file name, just use no special characters and have specific naming convention to keep dates in check
# running in chunks can help determine source of problem to make sure things run correct
# AI tools (e.g., ChatGPT) are helpful for debugging

# Define your working folder. Put all your files here, and use forward slashes only.
#Change the fields in yellow to whatever is on your own laptop
import os
import processing
folder = 'E:/drone stuff/'  #CHANGE TO YOUR PATH!



# Set your working files
ndvi_file = os.path.join(folder, '2024-09-06 limas REM_index_ndvi.tif') #CHANGE TO YOUR NDVI file!
dsm_file = os.path.join(folder, '2024-09-06 limas REM_dsm.tif') #CHANGE TO YOUR DSM file!
plot_file = os.path.join(folder, 'east plots.gpkg') #CHANGE TO YOUR plot grid file!

# Define what outputs will be named. I probably would not recommend changing these unless you feel very confident
thresh_file = os.path.join(folder, 'thresh.tif')
maskedNDVI_file = os.path.join(folder, 'maskedNDVI.tif')
cdsm_file = os.path.join(folder, 'cDSM.tif')
sdsm_file = os.path.join(folder, 'sDSM.tif')
thresh_output = os.path.join(folder, 'thresh.gpkg')
maskedNDVI_output = os.path.join(folder, 'maskedNDVI.gpkg')
cdsm_output = os.path.join(folder, 'cDSM.gpkg')
sdsm_output = os.path.join(folder, 'sDSM.gpkg')




#making a mask for soil vs. plants. A threshold of NDVI > 0.5 is used here, feel free to adjust
expression1 = f'"{os.path.splitext(os.path.basename(ndvi_file))[0]}@1" > 0.5'
#thresh
processing.run("native:rastercalc", {
         'LAYERS':[ndvi_file],
         'EXPRESSION':expression1,
         'EXTENT':None,
         'CELL_SIZE':None,
         'CRS':None,
         'OUTPUT':thresh_file
})
 
iface.addRasterLayer(thresh_file, "thresh")


#making a layer that is NDVI with soil masked out. I call this maskNDVI
expression2 = f'"{os.path.splitext(os.path.basename(ndvi_file))[0]}@1" / ("thresh@1")'

processing.run("native:rastercalc", {
'LAYERS':[ndvi_file,thresh_file],
'EXPRESSION':expression2,
'EXTENT':None,
'CELL_SIZE':None,
'CRS':None,
'OUTPUT':maskedNDVI_file
})

iface.addRasterLayer(maskedNDVI_file, "maskedNDVI")


#now time to make a canopy Digital Surface Model (only canopy pixels, soil removed) 
expression3 = f'"{os.path.splitext(os.path.basename(dsm_file))[0]}@1" / ("thresh@1")'
 
processing.run("native:rastercalc", {
'LAYERS':[dsm_file,thresh_file],
'EXPRESSION':expression3,
'EXTENT':None,
'CELL_SIZE':None,
'CRS':None,
'OUTPUT':cdsm_file
})
 
iface.addRasterLayer(cdsm_file, "cDSM")
 
#now time to make a soil Digital Surface Model (only soil pixels, canopy removed) 
expression4 = f'"{os.path.splitext(os.path.basename(dsm_file))[0]}@1" / ( "thresh@1"  <  0.5)'
 
# sDSM calculation
processing.run("native:rastercalc", {
'LAYERS': [dsm_file, thresh_file],
'EXPRESSION': expression4,
'EXTENT': None,
'CELL_SIZE': None,
'CRS': None,
'OUTPUT': sdsm_file
})
  
iface.addRasterLayer(sdsm_file, "sDSM")
 
 
##  % canopy area extraction
processing.run("native:zonalstatisticsfb", {
'INPUT':plot_file,
'INPUT_RASTER':thresh_file,
'RASTER_BAND':1,
'COLUMN_PREFIX':'canopy.proportion_',
'STATISTICS':[2]                                      
,'OUTPUT':thresh_output
})
 
 ##  % canopy area extraction
processing.run("native:zonalstatisticsfb", {
'INPUT':plot_file,
'INPUT_RASTER':maskedNDVI_file,
'RASTER_BAND':1,
'COLUMN_PREFIX':'maskedNDVI_',
'STATISTICS':[2,3,6]                                      
,'OUTPUT':maskedNDVI_output
})
 
processing.run("native:zonalstatisticsfb", {
'INPUT':plot_file,
'INPUT_RASTER':cdsm_file,
'RASTER_BAND':1,
'COLUMN_PREFIX':'_cDSM',
'STATISTICS':[2,6]
,'OUTPUT':cdsm_output
})
 
processing.run("native:zonalstatisticsfb", {
'INPUT':plot_file,
'INPUT_RASTER':sdsm_file,
'RASTER_BAND':1,
'COLUMN_PREFIX':'_sDSM',
'STATISTICS':[3]
,'OUTPUT':sdsm_output
})
 
iface.addVectorLayer(thresh_output, "thresh", "ogr")
iface.addVectorLayer(maskedNDVI_output, "maskedNDVI", "ogr")
iface.addVectorLayer(cdsm_output, "cDSM", "ogr")
iface.addVectorLayer(sdsm_output, "sDSM", "ogr")
 
 
from qgis.core import QgsVectorLayer, QgsVectorFileWriter, QgsProject
 
# Loop through only vector layers
layers = QgsProject.instance().mapLayers().values()
for lyr in layers:
    if isinstance(lyr, QgsVectorLayer):
     newName = lyr.name() + ".csv"
     save_options = QgsVectorFileWriter.SaveVectorOptions()
     save_options.driverName = "CSV"
     save_options.fileEncoding = "UTF-8"
     transform_context = QgsProject.instance().transformContext()
 
     output_path = os.path.join(folder, newName)
     ret = QgsVectorFileWriter.writeAsVectorFormatV2(lyr, output_path, transform_context, save_options)

