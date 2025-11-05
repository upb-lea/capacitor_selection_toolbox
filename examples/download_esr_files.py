"""Download initial capacitor ESR data."""
# python libraries
import logging

# own libraries
import pecst

# configure logging to show femmt terminal output
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

pecst.download_esr_csv_files()
