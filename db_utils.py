"""
Database utilities for PostgreSQL connection and data export
"""
import arcpy
import logging
from config import SDE_PATH

class DatabaseManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def export_table_to_gdb(self, gdb_path, table_name):
        """
        Export PostgreSQL table to File Geodatabase
        
        Args:
            gdb_path (str): Path to the target GDB
            table_name (str): Name of the table to export
        """
        try:
            # Create the GDB if it doesn't exist
            if not arcpy.Exists(gdb_path):
                import os
                gdb_folder = os.path.dirname(gdb_path)
                gdb_name = os.path.basename(gdb_path)
                arcpy.CreateFileGDB_management(gdb_folder, gdb_name)
                self.logger.info(f"Created GDB: {gdb_path}")
            
            # Set up the input feature class path
            input_fc = f"{SDE_PATH}\\{table_name}"
            
            # Export the feature class to GDB
            output_fc = f"{gdb_path}\\{table_name}"
            
            self.logger.info(f"Exporting {input_fc} to {output_fc}")
            arcpy.CopyFeatures_management(input_fc, output_fc)
            
            self.logger.info(f"Successfully exported {table_name} to {gdb_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting table {table_name}: {str(e)}")
            raise
            
    def get_table_schema(self, table_name):
        """
        Get the schema of a PostgreSQL table
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            list: List of field names
        """
        try:
            input_fc = f"{SDE_PATH}\\{table_name}"
            fields = arcpy.ListFields(input_fc)
            field_names = [field.name for field in fields]
            
            self.logger.info(f"Table {table_name} schema: {field_names}")
            return field_names
            
        except Exception as e:
            self.logger.error(f"Error getting schema for table {table_name}: {str(e)}")
            raise
