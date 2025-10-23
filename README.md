# PostgreSQL to DWG Conversion Tool

This tool converts PostgreSQL tables with PostGIS geometry to DWG format with comparison logic to detect changes.

## Features

- Converts PostgreSQL tables to DWG format
- Compares current data with previous versions
- Adds custom `merchav_string` column based on mapping
- Sends email notifications when changes are detected
- Comprehensive logging

## Requirements

- ArcGIS Pro or ArcGIS Server with Python API
- PostgreSQL database with PostGIS extension
- SDE connection file to PostgreSQL database

## Configuration

Edit `config.py` to set up your environment:

### Test Environment (Default)
- Uses test email settings
- All paths are as configured

### Production Environment
- Set `ENVIRONMENT = "production"`
- Update email server settings with real values
- Update all paths to production locations

## Usage

1. Ensure your SDE connection file is accessible
2. Update the configuration in `config.py`
3. Run the main script:

```bash
python main.py
```

## Process Flow

1. **Check for existing DWG file**
   - If no DWG exists: Create new DWG from PostgreSQL table
   - If DWG exists: Perform comparison with current data

2. **Data Processing**
   - Export PostgreSQL table to temporary GDB
   - Add `merchav_string` column based on mapping
   - Convert to DWG format

3. **Comparison (if DWG exists)**
   - Convert existing DWG to GDB
   - Compare current vs previous data
   - Detect changes in geometry, attributes, and feature count

4. **Update and Notification**
   - If changes found: Update DWG file and send email
   - If no changes: Log and exit

## File Structure

```
├── main.py              # Main conversion script
├── config.py            # Configuration settings
├── db_utils.py          # Database utilities
├── gdb_utils.py         # Geodatabase utilities
├── dwg_utils.py         # DWG conversion utilities
├── comparison_utils.py  # Comparison logic
├── email_utils.py       # Email notification utilities
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Logging

Logs are written to the configured `LOG_PATH` directory with timestamps. Each run creates a new log file.

## Email Notifications

Email notifications are sent when:
- New DWG file is created
- Changes are detected in existing data

## Permissions

The tool only writes to:
- `TARGET_PATH`: DWG files only
- `LOG_PATH`: Log files only
- Temporary directory: Temporary GDB files (automatically cleaned up)

No database write permissions are required.
