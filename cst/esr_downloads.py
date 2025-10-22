"""Download capacitor ESR files."""

# python libraries
import requests
import pathlib

# 3rd party libraries

# own libraries
import cst.constants as const
from cst.cst_dataclasses import CapacitorType
from cst.read_capacitor_database import load_capacitors

def _download_file(url: str, save_path: str) -> None:
    """
    Download the capacitor csv file containing ESR over frequency.

    :param url: download URL
    :type url: str
    :param save_path: path to save downloaded csv file
    :type save_path: str
    """
    try:
        # Send GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Write the content of the response to a local file
            with open(save_path, 'wb') as file:
                file.write(response.content)
            print(f"File downloaded successfully: {save_path}")
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")


def download_esr_csv_files(capacitor_type_list: list[CapacitorType]) -> None:
    """
    Download ESR over frequency data from the manufacturers homepage.

    :param capacitor_type_list: capacitor types to download
    :type capacitor_type_list: CapacitorType
    """
    c_db, c_thermal, c_derating = load_capacitors(capacitor_type_list)

    esr_folder_name = (pathlib.Path(__file__).parent).joinpath(const.ESR_OVER_FREQUENCY_FOLDER)
    if not esr_folder_name.exists():
        pathlib.Path.mkdir(esr_folder_name)

    # capacitor pareto plane calculation
    for ordering_code in c_db['ordering code']:
        # modify ordering code for url
        ordering_code = ordering_code.replace("+", "K")
        ordering_code_short = ordering_code.replace("000", "")

        # generate csv file path
        save_path = (pathlib.Path(__file__).parent).joinpath(const.ESR_OVER_FREQUENCY_FOLDER, f"{ordering_code}.csv")
        if save_path.exists():
            print(f"{save_path} already exists. Skip download.")
        else:
            url = (f"https://captools.tdk-electronics.tdk.com/CLARA/api/ApiWebCLARA/DownloadThermalRating?partNumber={ordering_code}"
                   f"&modelPartNumber={ordering_code_short}")
            _download_file(url, str(save_path))
