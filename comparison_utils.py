"""
Comparison utilities for comparing GDBs and detecting changes
"""
import arcpy
import logging
from gdb_utils import GDBManager

class ComparisonManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gdb_manager = GDBManager()
        
    def compare_gdbs(self, curr_gdb_path, prev_gdb_path, table_name):
        """
        Compare two GDBs and detect changes
        
        Args:
            curr_gdb_path (str): Path to current GDB
            prev_gdb_path (str): Path to previous GDB
            table_name (str): Name of the table to compare
            
        Returns:
            list: List of detected changes
        """
        try:
            changes = []
            
            # Check if both GDBs exist
            if not arcpy.Exists(curr_gdb_path):
                changes.append("Current GDB does not exist")
                return changes
                
            if not arcpy.Exists(prev_gdb_path):
                changes.append("Previous GDB does not exist")
                return changes
            
            curr_table = f"{curr_gdb_path}\\{table_name}"
            prev_table = f"{prev_gdb_path}\\{table_name}"
            
            # Check if tables exist in both GDBs
            if not arcpy.Exists(curr_table):
                changes.append(f"Current table {table_name} does not exist")
                return changes
                
            if not arcpy.Exists(prev_table):
                changes.append(f"Previous table {table_name} does not exist")
                return changes
            
            # Compare feature counts
            curr_count = self.gdb_manager.get_feature_count(curr_gdb_path, table_name)
            prev_count = self.gdb_manager.get_feature_count(prev_gdb_path, table_name)
            
            if curr_count != prev_count:
                changes.append(f"Feature count changed: {prev_count} -> {curr_count}")
            
            # Compare geometries and attributes
            geometry_changes = self.compare_geometries(curr_table, prev_table)
            if geometry_changes:
                changes.extend(geometry_changes)
            
            # Compare attributes
            attribute_changes = self.compare_attributes(curr_table, prev_table)
            if attribute_changes:
                changes.extend(attribute_changes)
            
            self.logger.info(f"Comparison completed. Found {len(changes)} changes")
            return changes
            
        except Exception as e:
            self.logger.error(f"Error comparing GDBs: {str(e)}")
            return [f"Error during comparison: {str(e)}"]
            
    def compare_geometries(self, curr_table, prev_table):
        """
        Compare geometries between two tables
        
        Args:
            curr_table (str): Path to current table
            prev_table (str): Path to previous table
            
        Returns:
            list: List of geometry changes
        """
        try:
            changes = []
            
            # Get geometry type - check if it's a feature class first
            curr_desc = arcpy.Describe(curr_table)
            prev_desc = arcpy.Describe(prev_table)
            
            # Check if both are feature classes
            if hasattr(curr_desc, 'shapeType') and hasattr(prev_desc, 'shapeType'):
                if curr_desc.shapeType != prev_desc.shapeType:
                    changes.append(f"Geometry type changed: {prev_desc.shapeType} -> {curr_desc.shapeType}")
                
                # Compare spatial reference
                curr_sr = curr_desc.spatialReference
                prev_sr = prev_desc.spatialReference
                
                if curr_sr and prev_sr and curr_sr.name != prev_sr.name:
                    changes.append(f"Spatial reference changed: {prev_sr.name} -> {curr_sr.name}")
            else:
                # If not feature classes, compare as tables
                changes.append("Tables compared as non-spatial data")
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Error comparing geometries: {str(e)}")
            return [f"Geometry comparison error: {str(e)}"]
            
    def compare_attributes(self, curr_table, prev_table):
        """
        Compare attributes between two tables
        
        Args:
            curr_table (str): Path to current table
            prev_table (str): Path to previous table
            
        Returns:
            list: List of attribute changes
        """
        try:
            changes = []
            
            # Get field lists with error handling
            try:
                curr_fields = [field.name for field in arcpy.ListFields(curr_table)]
            except Exception as e:
                self.logger.warning(f"Could not list fields for current table: {e}")
                curr_fields = []
            
            try:
                prev_fields = [field.name for field in arcpy.ListFields(prev_table)]
            except Exception as e:
                self.logger.warning(f"Could not list fields for previous table: {e}")
                prev_fields = []
            
            # Check for new fields
            new_fields = set(curr_fields) - set(prev_fields)
            if new_fields:
                changes.append(f"New fields added: {list(new_fields)}")
            
            # Check for removed fields
            removed_fields = set(prev_fields) - set(curr_fields)
            if removed_fields:
                changes.append(f"Fields removed: {list(removed_fields)}")
            
            # Compare common fields (simplified to avoid complex field value comparison)
            common_fields = set(curr_fields) & set(prev_fields)
            if common_fields:
                changes.append(f"Common fields found: {len(common_fields)} fields")
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Error comparing attributes: {str(e)}")
            return [f"Attribute comparison error: {str(e)}"]
            
    def compare_field_values(self, curr_table, prev_table, field_name):
        """
        Compare values in a specific field between two tables
        
        Args:
            curr_table (str): Path to current table
            prev_table (str): Path to previous table
            field_name (str): Name of the field to compare
            
        Returns:
            list: List of field value changes
        """
        try:
            changes = []
            
            # Get unique values from both tables
            curr_values = set()
            prev_values = set()
            
            with arcpy.da.SearchCursor(curr_table, [field_name]) as cursor:
                for row in cursor:
                    if row[0] is not None:
                        curr_values.add(str(row[0]))
            
            with arcpy.da.SearchCursor(prev_table, [field_name]) as cursor:
                for row in cursor:
                    if row[0] is not None:
                        prev_values.add(str(row[0]))
            
            # Find new values
            new_values = curr_values - prev_values
            if new_values:
                changes.append(f"New values in {field_name}: {list(new_values)[:10]}")  # Limit to first 10
            
            # Find removed values
            removed_values = prev_values - curr_values
            if removed_values:
                changes.append(f"Removed values in {field_name}: {list(removed_values)[:10]}")  # Limit to first 10
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Error comparing field values for {field_name}: {str(e)}")
            return [f"Field value comparison error for {field_name}: {str(e)}"]
