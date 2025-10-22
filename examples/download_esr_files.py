"""Download initial capacitor ESR data."""

# own packages
import cst

# select capacitors to download
capacitor_type_list = [cst.CapacitorType.FilmCapacitor]

cst.download_esr_csv_files(capacitor_type_list)
