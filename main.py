"""
Main script for PostgreSQL to DWG conversion with enhanced feature class handling
"""
import os
import sys
import logging
from datetime import datetime
import arcpy
from config import *
from postgres_to_dwg_converter import PostgresToDWGConverter

def main():
    """Main function using the enhanced converter"""
    try:
        # Set ArcGIS environment
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = arcpy.env.scratchGDB
        
        # Create enhanced converter instance and run
        converter = PostgresToDWGConverter()
        converter.run_conversion()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()