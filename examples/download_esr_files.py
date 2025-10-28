"""Download initial capacitor ESR data."""
# python libraries
import logging

# own libraries
import cst

# configure logging to show femmt terminal output
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

# select capacitors to download
capacitor_type_list = [cst.CapacitorType.FilmCapacitor]

cst.download_esr_csv_files(capacitor_type_list)
