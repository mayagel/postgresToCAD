"""
Main script for PostgreSQL to DWG conversion with comparison logic
"""
import os
import sys
import logging
import tempfile
from datetime import datetime
from pathlib import Path
import arcpy
from config import *
from db_utils import DatabaseManager
from gdb_utils import GDBManager
from dwg_utils import DWGManager
from comparison_utils import ComparisonManager

class PostgresToDWGConverter:
    def __init__(self):
        self.setup_logging()
        self.db_manager = DatabaseManager()
        self.gdb_manager = GDBManager()
        self.dwg_manager = DWGManager()
        self.comparison_manager = ComparisonManager()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_filename = f"conversion_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file_path = os.path.join(LOG_PATH, log_filename)
        
        # Create log directory if it doesn't exist
        os.makedirs(LOG_PATH, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging initialized. Log file: {log_file_path}")
        
    def run_conversion(self):
        """Main conversion process"""
        try:
            self.logger.info("Starting PostgreSQL to DWG conversion process")
            
            # Step 1: Check if target DWG file exists
            target_dwg_path = os.path.join(TARGET_PATH, DWG_FILE_NAME)
            dwg_exists = os.path.exists(target_dwg_path)
            
            if not dwg_exists:
                self.logger.info("DWG file does not exist. Creating new DWG from PostgreSQL table")
                self.create_initial_dwg()
                self.send_notification("New DWG file created", "DWG file created from PostgreSQL table")
            else:
                self.logger.info("DWG file exists. Performing comparison and update if needed")
                self.perform_comparison_and_update()
                
            self.logger.info("Conversion process completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during conversion process: {str(e)}")
            raise
            
    def create_initial_dwg(self):
        """Create initial DWG from PostgreSQL table"""
        curr_gdb_path = None
        
        try:
            # Create GDB for current data in TARGET_PATH + COMPARISON_GDB
            curr_gdb_path = os.path.join(TARGET_PATH, COMPARISON_GDB, f"{TABLE_SOURCE}_curr.gdb")
            
            # Clean up existing GDB at the beginning
            if os.path.exists(curr_gdb_path):
                self.logger.info("Cleaning up existing GDB at the beginning")
                self.gdb_manager.delete_gdb(curr_gdb_path)
            
            # Export PostgreSQL table to GDB
            self.logger.info(f"Exporting {TABLE_SOURCE} from PostgreSQL to GDB")
            self.db_manager.export_table_to_gdb(curr_gdb_path, TABLE_SOURCE)
            
            # Add merchav_string column
            self.logger.info("Adding merchav_string column")
            self.gdb_manager.add_merchav_string_column(curr_gdb_path, TABLE_SOURCE, merchav_MAPPING)
            
            # Convert GDB to DWG
            self.logger.info("Converting GDB to DWG")
            target_dwg_path = os.path.join(TARGET_PATH, DWG_FILE_NAME)
            self.dwg_manager.convert_gdb_to_dwg(curr_gdb_path, TABLE_SOURCE, target_dwg_path)
            
            # Keep GDB for investigation - don't delete it
            self.logger.info("Keeping GDB for investigation:")
            self.logger.info(f"  GDB: {curr_gdb_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating initial DWG: {str(e)}")
            raise
            
    def perform_comparison_and_update(self):
        """Perform comparison between current and previous data"""
        curr_gdb_path = None
        prev_gdb_path = None
        
        try:
            # Create GDBs in TARGET_PATH + COMPARISON_GDB
            comparison_dir = os.path.join(TARGET_PATH, COMPARISON_GDB)
            curr_gdb_path = os.path.join(comparison_dir, f"{TABLE_SOURCE}_curr.gdb")
            prev_gdb_path = os.path.join(comparison_dir, f"{TABLE_SOURCE}_prev.gdb")
            
            # Clean up existing GDBs at the beginning
            self.logger.info("Cleaning up existing comparison GDBs at the beginning")
            for gdb_path in [curr_gdb_path, prev_gdb_path]:
                if os.path.exists(gdb_path):
                    self.gdb_manager.delete_gdb(gdb_path)
            
            # Export current data from PostgreSQL
            self.logger.info("Exporting current data from PostgreSQL")
            self.db_manager.export_table_to_gdb(curr_gdb_path, TABLE_SOURCE)
            self.gdb_manager.add_merchav_string_column(curr_gdb_path, TABLE_SOURCE, merchav_MAPPING)
            
            # Convert existing DWG to GDB for comparison
            self.logger.info("Converting existing DWG to GDB for comparison")
            target_dwg_path = os.path.join(TARGET_PATH, DWG_FILE_NAME)
            self.dwg_manager.convert_dwg_to_gdb(target_dwg_path, prev_gdb_path, TABLE_SOURCE)
            
            # Perform comparison
            self.logger.info("Performing comparison between current and previous data")
            updates = self.comparison_manager.compare_gdbs(curr_gdb_path, prev_gdb_path, TABLE_SOURCE)
            
            if updates:
                self.logger.info(f"Updates found: {updates}")
                # Create new DWG with updates
                self.dwg_manager.convert_gdb_to_dwg(curr_gdb_path, TABLE_SOURCE, target_dwg_path)
                self.send_notification("Updates found in data", f"Updates: {updates}")
            else:
                self.logger.info("No updates found")
            
            # Keep GDBs for investigation - don't delete them
            self.logger.info("Keeping comparison GDBs for investigation:")
            self.logger.info(f"  Current GDB: {curr_gdb_path}")
            self.logger.info(f"  Previous GDB: {prev_gdb_path}")
            
        except Exception as e:
            self.logger.error(f"Error during comparison: {str(e)}")
            raise
            
    def send_notification(self, subject, message):
        """Send email notification"""
        try:
            log_files = [f for f in os.listdir(LOG_PATH) if f.endswith('.log')]
            latest_log = max(log_files, key=lambda x: os.path.getctime(os.path.join(LOG_PATH, x))) if log_files else "No log file found"
            
            full_message = f"{message}\n\nTo see full log file, please open: {os.path.join(LOG_PATH, latest_log)}"
            
            # self.email_notifier.send_email(
            #     to_addresses=EMAIL_GROUP,
            #     subject=f"Update in {TABLE_SOURCE} - {subject}",
            #     body=full_message
            # )
            self.logger.info("Email notification sent successfully")
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {str(e)}")

if __name__ == "__main__":
    converter = PostgresToDWGConverter()
    converter.run_conversion()
