"""
Configuration file for PostgreSQL to DWG conversion project
"""
import os

# Environment settings
ENVIRONMENT = "test"  # "test" or "production"

# Database and table settings
TABLE_SOURCE = "gis_nafot"
# COLUMNS_FILTER = ["nafa", "objectid", "objectid_1", "Shape"]

COLUMNS_FILTER=[
"poly_id",
"nafaname",
"mahoz_name",
"merchav",
"created_user",
"created_date",
"last_edited_user",
"last_edited_date",
"machoz",
"nafa_archaeologist",
"nafanameeng"
]

# File paths
TARGET_PATH = r"U:\IT\eyalSchwarzwald\cad_exports"
LOG_PATH = r"U:\IT\eyalSchwarzwald\cad_exports\logs"
DWG_FILE_NAME = "GIS_NAFOT_ExportCAD.dwg"
COMPARISON_GDB = "comparison"

# SDE connection
SDE_PATH = r"C:\Users\yagelm\AppData\Roaming\ESRI\ArcGISPro\Favorites\gis-postgres03.sde"

# Email settings
EMAIL_GROUP = ["yagel@me.com"]

# merchav mapping (code to string)
merchav_MAPPING = {
    101: "jerushalem",
    102: "center",
    103: "north",
    104: "south",
}

# Email server settings (for production, these should be placeholders)
if ENVIRONMENT == "production":
    SMTP_SERVER = "PLACEHOLDER_SMTP_SERVER"
    SMTP_PORT = "PLACEHOLDER_SMTP_PORT"
    SMTP_USER = "PLACEHOLDER_SMTP_USER"
    SMTP_PASSWORD = "PLACEHOLDER_SMTP_PASSWORD"
else:
    # Test environment settings
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "test@example.com"
    SMTP_PASSWORD = "test_password"
