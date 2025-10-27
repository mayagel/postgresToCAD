"""
PostgreSQL to DWG Converter
Converts PostGIS table to DWG format with comparison and update detection
"""

import arcpy, json
import os
import sys
import logging
from datetime import datetime
from config import *
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def _to_2d(geom: arcpy.Geometry) -> arcpy.Geometry:
    """Return a 2D version of the geometry (drops Z and M) preserving SR."""
    j = json.loads(geom.JSON)

    # Drop Z/M flags
    j['hasZ'] = False
    j['hasM'] = False

    def strip_zm_coords(seq):
        # seq is a list of coordinates: [x,y] or [x,y,z] or [x,y,z,m]
        return [c[:2] for c in seq]

    j['rings'] = [strip_zm_coords(r) for r in j['rings']]
   
    return arcpy.AsShape(j, True)

class PostgresToDWGConverter:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.changes_found = False
        self.update_details = []
        
    def setup_logging(self):
        """Setup logging configuration"""
        # Create log directory if it doesn't exist
        os.makedirs(LOG_PATH, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"conversion_log_{timestamp}.log"
        log_filepath = os.path.join(LOG_PATH, log_filename)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filepath),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging initialized. Log file: {log_filepath}")
        
    def connect_to_postgis(self):
        """Connect to PostGIS database and return feature class path"""
        try:
            # Construct the full path to the table in SDE
            pg_layer = f"{SDE_PATH}\\{TABLE_SOURCE}"
            
            # Test if the connection works
            if not arcpy.Exists(pg_layer):
                raise Exception(f"Table {TABLE_SOURCE} not found in SDE connection")
                
            self.logger.info(f"Successfully connected to PostGIS table: {pg_layer}")
            return pg_layer
            
        except Exception as e:
            self.logger.error(f"Failed to connect to PostGIS: {str(e)}")
            raise
            
    def read_dwg_feature_classes(self, dwg_path):
        """Read all feature classes from DWG file and return structured data"""
        try:
            if not os.path.exists(dwg_path):
                self.logger.info(f"DWG file not found: {dwg_path}")
                return None
                
            self.logger.info(f"Reading DWG feature classes from: {dwg_path}")
            
            # Initialize structure to hold all feature classes
            dwg_structure = {
                'all_feature_classes': {}
            }
            
            # List all feature classes in the DWG
            try:
                arcpy.env.workspace = dwg_path
                feature_classes= arcpy.ListFeatureClasses()
                self.logger.info(f"Found {len(feature_classes)} feature classes in DWG")
                
                for fc_path in feature_classes:
                    fc_name = os.path.basename(fc_path)
                    self.logger.info(f"Processing feature class: {fc_name}")
                    
                    # Store all feature classes
                    dwg_structure['all_feature_classes'][fc_name] = fc_path
                    
                    # Categorize feature classes based on naming convention
                    if 'annotation' in fc_name.lower():
                        dwg_structure['annotation'] = fc_path
                    elif 'point' in fc_name.lower():
                        dwg_structure['point'] = fc_path
                    elif 'polygon' in fc_name.lower():
                        dwg_structure['polygon'] = fc_path
                    elif 'polyline' in fc_name.lower():
                        dwg_structure['polyline'] = fc_path
                    elif 'multipatch' in fc_name.lower():
                        dwg_structure['multipatch'] = fc_path
                    elif 'gis_nafot' in fc_name.lower() and 'polygon' not in fc_name.lower():
                        # This should be the attribute table
                        dwg_structure['attribute_table'] = fc_path
                        
            except Exception as e:
                self.logger.warning(f"Could not list feature classes from DWG: {str(e)}")
                # Fallback: try to access DWG directly
                if arcpy.Exists(dwg_path):
                    dwg_structure['all_feature_classes']['main'] = dwg_path
                    dwg_structure['attribute_table'] = dwg_path
                    
            self.logger.info(f"DWG structure: {dwg_structure}")
            return dwg_structure
            
        except Exception as e:
            self.logger.error(f"Failed to read DWG feature classes: {str(e)}")
            return None

    def compare_features(self, pg_layer, dwg_structure):
        """Compare features between PostGIS and DWG structure"""
        try:
            self.logger.info("Starting feature comparison...")
            
            # Get field names from PostGIS layer
            pg_fields = [field.name for field in arcpy.ListFields(pg_layer)]
            self.logger.info(f"PostGIS fields: {pg_fields}")
            
            # Read PostGIS data
            pg_features = {}
            with arcpy.da.SearchCursor(pg_layer, ["OID@", "SHAPE@"] + pg_fields) as cursor:
                for row in cursor:
                    oid = row[0]
                    geometry = row[1]
                    attributes = row[2:]
                    pg_features[oid] = {
                        'geometry': geometry,
                        'attributes': attributes,
                        'field_names': pg_fields
                    }
            
            self.logger.info(f"Found {len(pg_features)} features in PostGIS")
            
            if dwg_structure is None:
                self.logger.info("No DWG file found - will create new one")
                self.changes_found = True
                self.update_details.append("No existing DWG file found")
                return True
            
            # Get the attribute table from DWG structure
            dwg_attribute_table = dwg_structure.get('all_feature_classes').get('gis_nafot_GIS_NAFOT')
            if not dwg_attribute_table:
                self.logger.warning("No attribute table found in DWG structure")
                self.changes_found = True
                self.update_details.append("No attribute table found in DWG")
                return True
            
            # Read DWG attribute data
            dwg_features = {}
            try:
                dwg_attribute_table_path = os.path.join(TARGET_PATH, DWG_FILE_NAME, dwg_attribute_table)
                dwg_fields = [f.name for f in arcpy.ListFields(dwg_attribute_table_path)]
                print(dwg_fields)
                # fields = [f for f in (["OID@"] + pg_fields) if f not in ['globalid', 'objectid', 'st_area(shape)', 'st_length(shape)']]
                with arcpy.da.SearchCursor(dwg_attribute_table_path,dwg_fields) as cursor:
                    for row in cursor:
                        oid = row[-1]
                        attributes = row[1:]
                        dwg_features[oid] = {
                            'attributes': attributes
                        }
            except Exception as e:
                self.logger.warning(f"Could not read DWG attribute table: {str(e)}")
                self.changes_found = True
                self.update_details.append("Could not read DWG attribute table")
                return True
            
            self.logger.info(f"Found {len(dwg_features)} features in DWG attribute table")
            
            # Get geometry from polygon feature class if available
            dwg_geometries = {}
            dwg_attribute_table = dwg_structure.get('all_feature_classes').get('gis_nafot_GIS_NAFOT')
            polygon_fc = dwg_structure.get('all_feature_classes').get('polygon')
            if dwg_attribute_table and arcpy.Exists(dwg_attribute_table):
                try:
                    with arcpy.da.SearchCursor(dwg_attribute_table, ["OID@", "SHAPE@", "Oid_1"]) as cursor:
                        for row in cursor:
                            oid = row[2]
                            geometry = row[1]
                            dwg_geometries[oid] = geometry
                    self.logger.info(f"Found {len(dwg_geometries)} geometries in DWG polygon feature class")
                except Exception as e:
                    self.logger.warning(f"Could not read DWG geometries: {str(e)}")
            
            # Compare features
            changes_found = False
            
            # Check for new features in PostGIS
            for oid in pg_features:
                if oid not in dwg_features:
                    changes_found = True
                    self.update_details.append(f"New feature found: OID {oid}")
                    self.logger.info(f"New feature found: OID {oid}")
                    
            # Check for removed features
            for oid in dwg_features:
                if oid not in pg_features:
                    changes_found = True
                    self.update_details.append(f"Feature removed: OID {oid}")
                    self.logger.info(f"Feature removed: OID {oid}")
                    
            # Check for modified features
            for oid in pg_features:
                if oid in dwg_features:
                    pg_feature = pg_features[oid]
                    dwg_feature = dwg_features[oid]
                    
                    # Compare geometry if available in DWG
                    if oid in dwg_geometries:
                        if not (_to_2d(pg_feature['geometry'])).equals((_to_2d(dwg_geometries[oid]))):
                            changes_found = True
                            self.update_details.append(f"Geometry changed for OID {oid}")
                            self.logger.info(f"Geometry changed for OID {oid}")
                    
                    # Compare attributes (excluding filtered columns)
                    for i, field_name in enumerate(pg_feature['field_names']):
                        if field_name in COLUMNS_FILTER:
                            if field_name not in dwg_fields:
                                changes_found = True
                                self.update_details.append(f"field_name '{field_name}' not exists in dwg")
                                self.logger.info(f"field_name '{field_name}' not exists in dwg")
                            else:
                                i_for_dwg = dwg_fields.index(field_name)
                                if pg_feature['attributes'][i] != dwg_feature['attributes'][i_for_dwg - 1]:
                                    changes_found = True
                                    self.update_details.append(f"Attribute '{field_name}' changed for OID {oid}")
                                    self.logger.info(f"Attribute '{field_name}' changed for OID {oid}")
                                
            self.changes_found = changes_found
            self.logger.info(f"Comparison complete. Changes found: {changes_found}")
            return changes_found
            
        except Exception as e:
            self.logger.error(f"Error during feature comparison: {str(e)}")
            raise
            
#     def add_merchav_mapping(self, pg_layer):
#         """Add merchav_string column with mapping using CalculateField"""
#         try:
#             self.logger.info("Adding merchav_string column...")
            
#             # Check if merchav column exists
#             fields = [field.name for field in arcpy.ListFields(pg_layer)]
#             if 'merchav' not in fields:
#                 self.logger.warning("'merchav' column not found in source table")
#                 return pg_layer
                
#             # Create a temporary feature class with the new column
#             comparison_dir = os.path.join(TARGET_PATH, COMPARISON_GDB)
#             os.makedirs(comparison_dir, exist_ok=True)
#             temp_gdb = os.path.join(comparison_dir, "temp_with_merchav.gdb")
            
#             # Delete existing GDB if it exists
#             if arcpy.Exists(temp_gdb):
#                 arcpy.management.Delete(temp_gdb)
            
#             # Create new GDB
#             arcpy.management.CreateFileGDB(comparison_dir, "temp_with_merchav.gdb")
            
#             temp_fc = os.path.join(temp_gdb, "temp_layer")
            
#             # Copy the original layer
#             arcpy.management.CopyFeatures(pg_layer, temp_fc)
            
#             # Add the new field
#             arcpy.management.AddField(temp_fc, "merchav_string", "TEXT", field_length=50)
            
#             # Build a code block with the mapping logic
#             code_block = f"""
# def get_merchav_string(merchav):
#     mapping = {merchav_MAPPING}
#     if merchav in mapping:
#         return mapping[merchav]
#     elif merchav is not None:
#         return f'Unknown_{{merchav}}'
#     else:
#         return None
# """
            
#             # Use CalculateField with code block - this works without where_clause
#             arcpy.management.CalculateField(
#                 in_table=temp_fc,
#                 field="merchav_string",
#                 expression="get_merchav_string(!merchav!)",
#                 expression_type="PYTHON3",
#                 code_block=code_block
#             )
                    
#             self.logger.info("Successfully added merchav_string column")
#             return temp_fc
            
#         except Exception as e:
#             self.logger.error(f"Error adding merchav mapping: {str(e)}")
#             return pg_layer
        
    def add_merchav_mapping(self, pg_layer):
        """Add merchav_string and Oid_1 columns using CalculateField"""
        try:
            self.logger.info("Adding merchav_string and Oid_1 columns...")

            # Check if merchav column exists
            fields = [field.name for field in arcpy.ListFields(pg_layer)]
            if 'merchav' not in fields:
                self.logger.warning("'merchav' column not found in source table")
                return pg_layer

            # Create a temporary feature class with the new columns
            comparison_dir = os.path.join(TARGET_PATH, COMPARISON_GDB)
            os.makedirs(comparison_dir, exist_ok=True)
            temp_gdb = os.path.join(comparison_dir, "temp_with_merchav.gdb")

            # Delete existing GDB if it exists
            if arcpy.Exists(temp_gdb):
                arcpy.management.Delete(temp_gdb)

            # Create new GDB
            arcpy.management.CreateFileGDB(comparison_dir, "temp_with_merchav.gdb")

            temp_fc = os.path.join(temp_gdb, "temp_layer")

            # Copy the original layer
            arcpy.management.CopyFeatures(pg_layer, temp_fc)

            # Add the new fields
            arcpy.management.AddField(temp_fc, "merchav_string", "TEXT", field_length=50)
            arcpy.management.AddField(temp_fc, "Oid_1", "LONG")

            # Build a code block with the mapping logic
            code_block = f"""
def get_merchav_string(merchav):
    mapping = {merchav_MAPPING}
    if merchav in mapping:
        return mapping[merchav]
    elif merchav is not None:
        return f'Unknown_{{merchav}}'
    else:
        return None
"""

            # Calculate merchav_string field
            arcpy.management.CalculateField(
                in_table=temp_fc,
                field="merchav_string",
                expression="get_merchav_string(!merchav!)",
                expression_type="PYTHON3",
                code_block=code_block
            )

            # Calculate Oid_1 field with the original OID
            # oid_field = arcpy.Describe(pg_layer).OIDFieldName
            # arcpy.management.CalculateField(
            #     in_table=temp_fc,
            #     field="Oid_1",
            #     expression=f"!{oid_field}!",
            #     expression_type="PYTHON3"
            # )

            
            # Get original OID values
            original_oid_field = arcpy.Describe(pg_layer).OIDFieldName
            original_oid_map = {}

            with arcpy.da.SearchCursor(pg_layer, ["SHAPE@", original_oid_field]) as cursor:
                for row in cursor:
                    original_oid_map[row[0].WKT] = row[1]  # Using WKT as a simple geometry key


            
            workspace = temp_gdb  # The GDB where temp_layer resides
            editor = arcpy.da.Editor(workspace)

            # Start edit session and operation
            editor.startEditing(False, True)
            editor.startOperation()

            try:
                # Update the copied layer
                with arcpy.da.UpdateCursor(temp_fc, ["SHAPE@", "Oid_1"]) as cursor:
                    for row in cursor:
                        geom_wkt = row[0].WKT
                        if geom_wkt in original_oid_map:
                            row[1] = original_oid_map[geom_wkt]
                            cursor.updateRow(row)
            finally:   
            # Stop operation and edit session
                editor.stopOperation()
                editor.stopEditing(True)



            self.logger.info("Successfully added merchav_string and Oid_1 columns")
            return temp_fc

        except Exception as e:
            self.logger.error(f"Error adding merchav mapping and OID_1: {str(e)}")
            return pg_layer
            
    def export_to_dwg(self, source_layer, output_path):
        """Export feature class to DWG format with proper feature class structure"""
        try:
            self.logger.info(f"Exporting to DWG with proper structure: {output_path}")
            
            # Ensure target directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create a temporary GDB to prepare the data with proper structure
            # Use TARGET_PATH + COMPARISON_GDB instead of scratch
            comparison_dir = os.path.join(TARGET_PATH, COMPARISON_GDB)
            os.makedirs(comparison_dir, exist_ok=True)
            
            temp_gdb_name = "temp_dwg_export"
            temp_gdb = os.path.join(comparison_dir, f"{temp_gdb_name}.gdb")
            
            # Delete existing GDB if it exists
            if arcpy.Exists(temp_gdb):
                arcpy.management.Delete(temp_gdb)
            
            # Create new GDB
            arcpy.management.CreateFileGDB(comparison_dir, f"{temp_gdb_name}.gdb")
            
            # Copy source layer to temp GDB
            temp_fc = os.path.join(temp_gdb, TABLE_SOURCE)
            arcpy.management.CopyFeatures(source_layer, temp_fc)
            
            # Create separate feature classes for different geometry types
            # This ensures the DWG will have the proper structure
            
            # 1. Create the main polygon feature class (primary geometry)
            polygon_fc = os.path.join(temp_gdb, f"{TABLE_SOURCE}_Polygon")
            arcpy.management.CopyFeatures(temp_fc, polygon_fc)
            
            # 2. Create polyline feature class (extract boundaries)
            polyline_fc = os.path.join(temp_gdb, f"{TABLE_SOURCE}_Polyline")
            try:
                # Convert polygon boundaries to polylines
                arcpy.management.FeatureToLine(polygon_fc, polyline_fc)
            except Exception as e:
                self.logger.warning(f"Could not create polyline feature class: {str(e)}")
                # Create empty polyline feature class
                arcpy.management.CreateFeatureclass(temp_gdb, f"{TABLE_SOURCE}_Polyline", "POLYLINE")
            
            # 3. Create annotation feature class (empty for now)
            annotation_fc = os.path.join(temp_gdb, f"{TABLE_SOURCE}_Annotation")
            arcpy.management.CreateFeatureclass(temp_gdb, f"{TABLE_SOURCE}_Annotation", "POINT")
            
            # 4. Create multipatch feature class (empty for now)
            multipatch_fc = os.path.join(temp_gdb, f"{TABLE_SOURCE}_Multipatch")
            arcpy.management.CreateFeatureclass(temp_gdb, f"{TABLE_SOURCE}_Multipatch", "MULTIPATCH")
            
            # 5. Create the attribute table (copy of original with all attributes)
            attribute_fc = os.path.join(temp_gdb, f"{TABLE_SOURCE}_GIS_NAFOT")
            arcpy.management.CopyFeatures(temp_fc, attribute_fc)
            
            # Export all feature classes to DWG
            feature_classes_to_export = [
                # polygon_fc,
                # polyline_fc,
                # annotation_fc,
                # multipatch_fc,
                attribute_fc
            ]
            
            # Filter out non-existent feature classes
            existing_fcs = [fc for fc in feature_classes_to_export if arcpy.Exists(fc)]
            
            self.logger.info(f"Exporting {len(existing_fcs)} feature classes to DWG")
            
            # Export to DWG using ExportCAD
            # Use the full path including directory and filename
            output_dwg_file = output_path
            
            arcpy.conversion.ExportCAD(
                in_features=existing_fcs,
                Output_Type="DWG_R2018",
                Output_File=output_dwg_file
            )
            
            # Clean up temporary GDB
            try:
                arcpy.management.Delete(temp_gdb)
            except Exception as e:
                self.logger.warning(f"Could not clean up temporary GDB: {str(e)}")
            
            self.logger.info(f"Successfully exported DWG with proper structure to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to DWG: {str(e)}")
            raise
            
    def send_notification_email(self):
        """Send email notification about updates"""
        try:
            if not self.changes_found:
                self.logger.info("No changes found - no email notification needed")
                return
                
            # Create email content
            subject = f"Update in {TABLE_SOURCE} - New DWG file created"
            
            update_summary = "\n".join(self.update_details) if self.update_details else "Changes detected in geometry or attributes"
            
            body = f"""
Update in {TABLE_SOURCE} was found. {update_summary}

Creating new DWG file in {TARGET_PATH}

To see full log file please open {LOG_PATH}\\{os.path.basename(logging.getLogger().handlers[0].baseFilename)}
            """
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = SMTP_USER
            msg['To'] = ", ".join(EMAIL_GROUP)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            if ENVIRONMENT == "production":
                self.logger.info("Production environment - email settings are placeholders")
                self.logger.info(f"Would send email to: {EMAIL_GROUP}")
                self.logger.info(f"Subject: {subject}")
                self.logger.info(f"Body: {body}")
            else:
                # For test environment, just log the email
                self.logger.info(f"Test environment - email would be sent to: {EMAIL_GROUP}")
                self.logger.info(f"Subject: {subject}")
                self.logger.info(f"Body: {body}")
                
        except Exception as e:
            self.logger.error(f"Error sending email notification: {str(e)}")
            
    def run_conversion(self):
        """Main conversion process"""
        try:
            self.logger.info("Starting PostgreSQL to DWG conversion process...")
            
            # Step 1: Connect to PostGIS
            pg_layer = self.connect_to_postgis()
            
            # Step 2: Check if DWG file exists and read its structure
            dwg_path = os.path.join(TARGET_PATH, DWG_FILE_NAME)
            dwg_structure = self.read_dwg_feature_classes(dwg_path)
            
            # Step 3: Compare features
            changes_found = self.compare_features(pg_layer, dwg_structure)
            
            # Step 4: If changes found or no DWG exists, create new DWG
            if changes_found or dwg_structure is None:
                self.logger.info("Changes detected or no existing DWG - creating new DWG file")
                
                # Add merchav mapping
                enhanced_layer = self.add_merchav_mapping(pg_layer)
                
                # Export to DWG
                self.export_to_dwg(enhanced_layer, dwg_path)
                
                # Send notification email ONLY if changes were found (not for first run without existing DWG)
                if changes_found:
                    self.send_notification_email()
                else:
                    self.logger.info("First run - DWG created but no email sent")
                
                self.logger.info("Conversion process completed successfully")
            else:
                self.logger.info("No changes detected - no action needed")
                
        except Exception as e:
            self.logger.error(f"Conversion process failed: {str(e)}")
            raise
        finally:
            # Cleanup temporary files
            try:
                if 'enhanced_layer' in locals():
                    arcpy.management.Delete(enhanced_layer)
            except:
                pass


def main():
    """Main function"""
    try:
        # Set ArcGIS environment
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = arcpy.env.scratchGDB
        
        # Create converter instance and run
        converter = PostgresToDWGConverter()
        converter.run_conversion()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

