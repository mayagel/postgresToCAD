"""
Geodatabase utilities for managing File Geodatabases
"""
import arcpy
import logging
import os

class GDBManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def create_gdb(self, gdb_path):
        """
        Create a new File Geodatabase
        
        Args:
            gdb_path (str): Path to the GDB to create
        """
        try:
            if arcpy.Exists(gdb_path):
                self.logger.warning(f"GDB {gdb_path} already exists")
                return
                
            gdb_dir = os.path.dirname(gdb_path)
            gdb_name = os.path.basename(gdb_path)
            
            arcpy.CreateFileGDB_management(gdb_dir, gdb_name)
            self.logger.info(f"Created GDB: {gdb_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating GDB {gdb_path}: {str(e)}")
            raise
            
    def delete_gdb(self, gdb_path):
        """
        Delete a File Geodatabase
        
        Args:
            gdb_path (str): Path to the GDB to delete
        """
        try:
            if arcpy.Exists(gdb_path):
                # Try to delete with a small delay to handle locking issues
                import time
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        arcpy.Delete_management(gdb_path)
                        self.logger.info(f"Deleted GDB: {gdb_path}")
                        return
                    except Exception as delete_error:
                        if attempt < max_retries - 1:
                            self.logger.warning(f"Attempt {attempt + 1} failed to delete GDB, retrying in 2 seconds...")
                            time.sleep(2)
                        else:
                            raise delete_error
            else:
                self.logger.warning(f"GDB {gdb_path} does not exist")
                
        except Exception as e:
            self.logger.error(f"Error deleting GDB {gdb_path}: {str(e)}")
            # Don't raise the exception to avoid stopping the main process
            self.logger.warning("GDB deletion failed, but continuing with the process")
            
    def add_merchav_string_column(self, gdb_path, table_name, merchav_mapping):
        """
        Add merchav_string column to the table based on merchav mapping
        
        Args:
            gdb_path (str): Path to the GDB
            table_name (str): Name of the table
            merchav_mapping (dict): Mapping of merchav codes to strings
        """
        try:
            table_path = f"{gdb_path}\\{table_name}"
            
            if not arcpy.Exists(table_path):
                raise ValueError(f"Table {table_path} does not exist")
            
            # Add the merchav_string field if it doesn't exist
            field_name = "merchav_string"
            if not self.field_exists(table_path, field_name):
                arcpy.AddField_management(table_path, field_name, "TEXT", field_length=50)
                self.logger.info(f"Added field {field_name} to {table_name}")
            
            # Start an edit session
            edit = arcpy.da.Editor(gdb_path)
            edit.startEditing(False, True)
            edit.startOperation()
            
            try:
                # Update the field values based on merchav mapping
                self.logger.info("Updating merchav_string values")
                with arcpy.da.UpdateCursor(table_path, ["merchav", "merchav_string"]) as cursor:
                    for row in cursor:
                        merchav_code = row[0]
                        if merchav_code in merchav_mapping:
                            row[1] = merchav_mapping[merchav_code]
                        else:
                            row[1] = f"Unknown_{merchav_code}"
                        cursor.updateRow(row)
                
                # Stop the operation and save edits
                edit.stopOperation()
                edit.stopEditing(True)
                
                self.logger.info("Successfully updated merchav_string values")
                
            except Exception as e:
                # If there's an error, abort the operation
                edit.stopOperation()
                edit.stopEditing(False)
                raise e
            
        except Exception as e:
            self.logger.error(f"Error adding merchav_string column: {str(e)}")
            raise
            
    def field_exists(self, table_path, field_name):
        """
        Check if a field exists in a table
        
        Args:
            table_path (str): Path to the table
            field_name (str): Name of the field to check
            
        Returns:
            bool: True if field exists, False otherwise
        """
        try:
            fields = arcpy.ListFields(table_path)
            field_names = [field.name for field in fields]
            return field_name in field_names
        except Exception as e:
            self.logger.error(f"Error checking field existence: {str(e)}")
            return False
            
    def get_feature_count(self, gdb_path, table_name):
        """
        Get the number of features in a table
        
        Args:
            gdb_path (str): Path to the GDB
            table_name (str): Name of the table
            
        Returns:
            int: Number of features
        """
        try:
            table_path = f"{gdb_path}\\{table_name}"
            if not arcpy.Exists(table_path):
                return 0
                
            count = arcpy.GetCount_management(table_path)
            return int(count.getOutput(0))
            
        except Exception as e:
            self.logger.error(f"Error getting feature count: {str(e)}")
            return 0
