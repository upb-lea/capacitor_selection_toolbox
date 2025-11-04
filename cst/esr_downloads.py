"""Download capacitor ESR files."""

# python libraries
import requests
import pathlib
import logging

# 3rd party libraries

# own libraries
import cst.constants as const
from cst.read_capacitor_database import load_dc_film_capacitors

logger = logging.getLogger(__name__)

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
            logger.info(f"File downloaded successfully: {save_path}")
        else:
            logger.warning(f"Failed to download file ({url}). Status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error {e} while downloading capacitor url:{url}")


def download_esr_csv_files(capacitor_series_name_list: list[str] = const.FOIL_CAPACITOR_SERIES_NAME_LIST) -> None:
    """Download ESR over frequency data from the manufacturers homepage."""
    for capacitor_series_name in capacitor_series_name_list:
        c_db, c_thermal, c_derating, _, _ = load_dc_film_capacitors(capacitor_series_name)

        esr_folder_name = (pathlib.Path(__file__).parent).joinpath(const.ESR_OVER_FREQUENCY_DIRECTORY)
        if not esr_folder_name.exists():
            pathlib.Path.mkdir(esr_folder_name)

        # capacitor pareto plane calculation
        for ordering_code in c_db['ordering code']:
            # modify ordering code for url
            # ESR graphs are the same for 5 % ("J") and 10 % ("K") tolerance. So 10 % is used, as in 5 %, not all capacitors are available
            ordering_code = ordering_code.replace("+", "K")
            # replace * by nothing, as this is for an optional 2-pin version only
            ordering_code = ordering_code.replace("*", "")
            # this is a URL specific replacement (not clear why needed, but figured out by studying the URL. Works fine.)
            ordering_code_short = ordering_code.replace("000", "")

            # generate csv file path
            save_path = (pathlib.Path(__file__).parent).joinpath(const.ESR_OVER_FREQUENCY_DIRECTORY, f"{ordering_code}.csv")
            if save_path.exists():
                logger.info(f"{save_path} already exists. Skip download.")
            else:
                url = (f"https://captools.tdk-electronics.tdk.com/CLARA/api/ApiWebCLARA/DownloadThermalRating?partNumber={ordering_code}"
                       f"&modelPartNumber={ordering_code_short}")
                _download_file(url, str(save_path))
