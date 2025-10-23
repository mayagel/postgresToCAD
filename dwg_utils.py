"""
DWG utilities for converting between GDB and DWG formats
"""
import arcpy
import logging
import os

class DWGManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def convert_gdb_to_dwg(self, gdb_path, table_name, dwg_path):
        """
        Convert a GDB table to DWG format
        
        Args:
            gdb_path (str): Path to the source GDB
            table_name (str): Name of the table to convert
            dwg_path (str): Path to the output DWG file
        """
        try:
            # Ensure the target directory exists
            os.makedirs(os.path.dirname(dwg_path), exist_ok=True)
            
            # Set up paths
            input_fc = f"{gdb_path}\\{table_name}"
            output_dwg = dwg_path
            
            if not arcpy.Exists(input_fc):
                raise ValueError(f"Feature class {input_fc} does not exist")
            
            # Delete existing DWG file if it exists
            if os.path.exists(output_dwg):
                try:
                    os.remove(output_dwg)
                    self.logger.info(f"Deleted existing DWG file: {output_dwg}")
                except Exception as delete_error:
                    self.logger.warning(f"Could not delete existing DWG file: {delete_error}")
            
            self.logger.info(f"Converting {input_fc} to DWG: {output_dwg}")
            
            # Convert to DWG using ExportCAD (ArcGIS Pro function)
            # Parameters: in_features, Output_Type, Output_File, Ignore_FileNames, Append_To_Existing
            # Use a basic DWG format that should be widely supported
            arcpy.ExportCAD_conversion(
                input_fc,                    # in_features
                "DWG_R2000",                 # Output_Type
                output_dwg,                  # Output_File
                "Use_Filenames_in_Tables",   # Ignore_FileNames
                "Overwrite_Existing_Files"   # Append_To_Existing
            )
            
            self.logger.info(f"Successfully converted to DWG: {output_dwg}")
            
        except Exception as e:
            self.logger.error(f"Error converting GDB to DWG: {str(e)}")
            raise
            
    def convert_dwg_to_gdb(self, dwg_path, gdb_path, table_name):
        """
        Convert a DWG file to GDB format for comparison
        
        Args:
            dwg_path (str): Path to the source DWG file
            gdb_path (str): Path to the target GDB
            table_name (str): Name for the output table
        """
        try:
            if not os.path.exists(dwg_path):
                raise ValueError(f"DWG file {dwg_path} does not exist")
            
            # Create the GDB if it doesn't exist
            if not arcpy.Exists(gdb_path):
                gdb_dir = os.path.dirname(gdb_path)
                gdb_name = os.path.basename(gdb_path)
                arcpy.CreateFileGDB_management(gdb_dir, gdb_name)
            
            # Set up output path
            output_fc = f"{gdb_path}\\{table_name}"
            
            self.logger.info(f"Converting DWG {dwg_path} to GDB: {output_fc}")
            
            # Convert DWG to GDB using CADToGeodatabase (ArcGIS Pro function)
            # Parameters: input_cad_datasets, out_gdb_path, out_dataset_name, reference_scale
            arcpy.CADToGeodatabase_conversion(
                dwg_path,           # input_cad_datasets
                gdb_path,           # out_gdb_path  
                table_name,         # out_dataset_name
                "1"                 # reference_scale
            )
            
            # Rename the imported feature class to match our table name
            imported_fcs = arcpy.ListFeatureClasses(feature_dataset=None, feature_type="")
            if imported_fcs:
                # Use the first imported feature class
                imported_fc = f"{gdb_path}\\{imported_fcs[0]}"
                if imported_fc != output_fc:
                    arcpy.Rename_management(imported_fc, table_name)
            
            self.logger.info(f"Successfully converted DWG to GDB: {output_fc}")
            
        except Exception as e:
            self.logger.error(f"Error converting DWG to GDB: {str(e)}")
            raise
            
    def dwg_exists(self, dwg_path):
        """
        Check if a DWG file exists
        
        Args:
            dwg_path (str): Path to the DWG file
            
        Returns:
            bool: True if file exists, False otherwise
        """
        return os.path.exists(dwg_path)
        
    def get_dwg_info(self, dwg_path):
        """
        Get information about a DWG file
        
        Args:
            dwg_path (str): Path to the DWG file
            
        Returns:
            dict: Information about the DWG file
        """
        try:
            if not self.dwg_exists(dwg_path):
                return {"exists": False}
            
            file_info = {
                "exists": True,
                "size": os.path.getsize(dwg_path),
                "modified": os.path.getmtime(dwg_path)
            }
            
            return file_info
            
        except Exception as e:
            self.logger.error(f"Error getting DWG info: {str(e)}")
            return {"exists": False, "error": str(e)}
