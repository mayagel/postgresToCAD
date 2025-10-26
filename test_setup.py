"""
Test script to verify the setup and configuration
"""
import os
import sys
from config import *

def test_configuration():
    """Test if all configuration values are properly set"""
    print("Testing configuration...")
    
    # Check required paths
    required_paths = [TARGET_PATH, LOG_PATH]
    for path in required_paths:
        if not os.path.exists(path):
            print(f"WARNING: Path does not exist: {path}")
        else:
            print(f"✓ Path exists: {path}")
    
    # Check SDE file
    if not os.path.exists(SDE_PATH):
        print(f"WARNING: SDE file does not exist: {SDE_PATH}")
    else:
        print(f"✓ SDE file exists: {SDE_PATH}")
    
    # Check email configuration
    print(f"✓ Email group: {EMAIL_GROUP}")
    print(f"✓ Environment: {ENVIRONMENT}")
    print(f"✓ Table source: {TABLE_SOURCE}")
    print(f"✓ DWG file name: {DWG_FILE_NAME}")
    
    # Check merchav mapping
    print(f"✓ Merchav mapping entries: {len(merchav_MAPPING)}")
    for code, name in merchav_MAPPING.items():
        print(f"  {code}: {name}")

def test_imports():
    """Test if all required modules can be imported"""
    print("\nTesting imports...")
    
    try:
        import arcpy
        print("✓ arcpy imported successfully")
    except ImportError as e:
        print(f"✗ arcpy import failed: {e}")
        print("  Make sure ArcGIS Pro or ArcGIS Server is installed")
    
    try:
        from db_utils import DatabaseManager
        print("✓ db_utils imported successfully")
    except ImportError as e:
        print(f"✗ db_utils import failed: {e}")
    
    try:
        from gdb_utils import GDBManager
        print("✓ gdb_utils imported successfully")
    except ImportError as e:
        print(f"✗ gdb_utils import failed: {e}")
    
    try:
        from dwg_utils import DWGManager
        print("✓ dwg_utils imported successfully")
    except ImportError as e:
        print(f"✗ dwg_utils import failed: {e}")
    
    try:
        from comparison_utils import ComparisonManager
        print("✓ comparison_utils imported successfully")
    except ImportError as e:
        print(f"✗ comparison_utils import failed: {e}")
    
    try:
        from email_utils import EmailNotifier
        print("✓ email_utils imported successfully")
    except ImportError as e:
        print(f"✗ email_utils import failed: {e}")

def main():
    """Main test function"""
    print("PostgreSQL to DWG Conversion Tool - Setup Test")
    print("=" * 50)
    
    test_configuration()
    test_imports()
    
    print("\n" + "=" * 50)
    print("Setup test completed!")
    print("\nTo run the conversion tool, execute: python main.py")

if __name__ == "__main__":
    main()

