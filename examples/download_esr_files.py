"""Download initial capacitor ESR data."""
# python libraries
import logging

# own libraries
import cst

# configure logging to show femmt terminal output
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

cst.download_esr_csv_files()
