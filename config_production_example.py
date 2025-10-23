"""
Example production configuration file
Copy this to config.py and update with your production values
"""
import os

# Environment settings
ENVIRONMENT = "production"  # Set to production

# Database and table settings
TABLE_SOURCE = "gis_nafot"
COLUMNS_FILTER = ["nafa"]

# File paths (UPDATE THESE FOR PRODUCTION)
TARGET_PATH = r"\\server\share\cad_exports"  # UPDATE: Your production target path
LOG_PATH = r"\\server\share\cad_exports\logs"  # UPDATE: Your production log path
DWG_FILE_NAME = "GIS_NAFOT_ExportCAD.dwg"
COMPARISON_GDB = "comparison"

# SDE connection (UPDATE FOR PRODUCTION)
SDE_PATH = r"\\server\path\to\your\production.sde"  # UPDATE: Your production SDE path

# Email settings (UPDATE FOR PRODUCTION)
EMAIL_GROUP = ["admin@yourcompany.com", "gis@yourcompany.com"]  # UPDATE: Your production email list

# merchav mapping (code to string) - UPDATE AS NEEDED
merchav_MAPPING = {
    101: "jerushalem",
    102: "center",
    103: "north",
    104: "south",
    # Add more mappings as needed
}

# Email server settings (UPDATE FOR PRODUCTION)
SMTP_SERVER = "your-smtp-server.com"  # UPDATE: Your SMTP server
SMTP_PORT = 587  # UPDATE: Your SMTP port
SMTP_USER = "your-email@yourcompany.com"  # UPDATE: Your SMTP username
SMTP_PASSWORD = "your-email-password"  # UPDATE: Your SMTP password
