"""
Download impedance and ESR over frequency curve and capacitance change over voltage from kemet ksim.

Make sure you do not violate the kemet ksim license rules.
"""

# python libraries
import itertools
import os.path
from io import StringIO
import requests

# 3rd party libraries
import pandas as pd
from matplotlib import pyplot as plt
import pickle



debug = False
ask_api = True

# directory to download
file_directory = "../pecst/ceramic_downloads"

# choose capacitor type, series, housing size, voltage and dielectric to download
# non-existing combinations will be skipped
types_to_download = ["ceramic"]
series_to_download = ['General Purpose Surface Mount (4V – 10kV)']
housing_sizes_to_download = ['C0805', 'C1206', 'C1210', 'C1808', 'C1812', 'C1825', 'C2220', 'C2225', 'C3040', 'C3640']
dc_voltage_ratings_to_download = ["100", "200", "250", "500", "630", "1000"]
dielectrics_to_download = ["C0G", "U2J", "X5R", "X7R", "X8G", "X8L", "X8R", "Y5V", "Z5U"]

# download impedance and ESR plots over frequency as well as capacitance over voltage
# do not change this!
plot_types = ["Imp,ESR", "Vbias"]


directory = os.path.dirname(os.path.abspath(__file__))
capacitor_downloaded_files_directory = os.path.join(directory, file_directory)
if not os.path.exists(capacitor_downloaded_files_directory):
    os.makedirs(capacitor_downloaded_files_directory)

# ask API for which parameter combinations are available as real capacitor
# store the results (material numbers only) on disk
# The curves will be downloaded later.
if ask_api:
    generated_config_list = []
    for capacitor_type, housing_size, dielectric, voltage_rating in itertools.product(types_to_download, housing_sizes_to_download, dielectrics_to_download,
                                                                                      dc_voltage_ratings_to_download):
        # example
        # generated_config = {'type': 'ceramic', 'partStatus': 'active', 'size': 'C1206', 'dielectric': 'X7R', 'voltage': '2000'}
        generated_config = {'type': capacitor_type, 'partStatus': 'active', 'size': housing_size, 'dielectric': dielectric, 'voltage': voltage_rating}
        generated_config_list.append(generated_config)

    part_number_config_list = []
    for config in generated_config_list:
        url = "https://ksim3.kemet.com/capacitance"
        print("Fetching capacitance for config:", config)
        response = requests.post(url, json=config)
        if response.json() is not None:
            for capacitance in response.json():
                if capacitance is not None:
                    print("Capacitance item:", capacitance)
                    part_number_config_list.append(capacitance)

    with open("../pecst/material_number_list.pkl", "wb") as fp:  # Pickling
        pickle.dump(part_number_config_list, fp)


# Download the impedance/ESR over frequency curves and capacitance over voltage curves.

with open("../pecst/material_number_list.pkl", "rb") as fp:
    part_number_config_list = pickle.load(fp)
# configs with sizes item: {'type': 'ceramic', 'partStatus': 'active', 'series': 'General Purpose Surface Mount (4V – 10kV)', 'size': 'C0201'}

print("Getting csv...")

payload = {
    "calculated": "No",
    "combine": "No",
    "freqList": [
        10000,
        50000,
        100000,
        500000,
        1000000,
        5000000,
        10000000
    ],
    "highlight": 1,
    "ind": 0,
    "line": "50",
    "path": "Shunt",
    "parts": [
        {
            "id": 0,
            "instances": 0,
            "capDisplay": "",
            "capValue": 0,
            "capType": "",
            "dielectric": "-",
            "kemetPn": "Combined",
            "basePn": "Combined",
            "maxTemp": 155,
            "series": "",
            "appDef": "",
            "spicePn": "Combined",
            "voltageRating": 0,
            "ceProps": [],
            "filmProps": {},
            "hidden": False,
            "param": {
                "qty": {
                    "title": "Qty",
                    "select": 1,
                    "min": 1,
                    "max": 10,
                    "step": 1,
                    "disabled": True,
                    "width": 4
                },
                "bias": {
                    "title": "Bias (V)",
                    "select": 0,
                    "min": 0,
                    "max": 0,
                    "step": 0.1,
                    "disabled": False,
                    "width": 6
                },
                "tempAmbient": {
                    "title": "Amb. (°C)",
                    "select": 25,
                    "min": -55,
                    "max": 155,
                    "step": 1,
                    "disabled": False,
                    "width": 6
                }
            },
            "tolerance": {
                "title": "Tolerance",
                "select": "",
                "disabled": True,
                "options": []
            },
            "seedProps": [],
            "displayAllCeProps": False,
            "tcc": "",
            "vcac": ""
        },
        {
            "id": 1,
            "instances": 1,
            "capDisplay": "10 pF",
            "dielectric": "C0G",
            "maxTemp": 125,
            "kemetPn": "C0201C100K8GAC",
            "basePn": "C0201C100K8GAC",
            "series": "General Purpose Surface Mount (4V – 10kV)",
            "appDef": "Commercial/Standard Chips",
            "spicePn": "",
            "capType": "Ceramic",
            "capValue": 10,
            "voltageRating": 10,
            "ceProps": [],
            "hidden": False,
            "param": {
                "qty": {
                    "title": "Qty",
                    "select": 1,
                    "min": 1,
                    "max": 1000,
                    "step": 1,
                    "disabled": False,
                    "width": 6
                },
                "bias": {
                    "title": "Bias (VDC)",
                    "select": 0,
                    "min": 0,
                    "max": 10,
                    "step": 0.1,
                    "disabled": False,
                    "width": 6
                },
                "tempAmbient": {
                    "title": "Amb (°C)",
                    "select": 25,
                    "min": -55,
                    "max": 125,
                    "step": 1,
                    "disabled": False,
                    "width": 6
                }
            },
            "tolerance": {
                "title": "Tolerance",
                "select": "K",
                "disabled": False,
                "hidden": False,
                "options": [
                    {
                        "value": "B",
                        "label": ".1pF",
                        "disabled": False
                    },
                    {
                        "value": "C",
                        "label": ".25pF",
                        "disabled": False
                    },
                    {
                        "value": "D",
                        "label": ".5pF",
                        "disabled": False
                    },
                    {
                        "value": "F",
                        "label": "1%",
                        "disabled": False
                    },
                    {
                        "value": "G",
                        "label": "2%",
                        "disabled": False
                    },
                    {
                        "value": "J",
                        "label": "5%",
                        "disabled": False
                    },
                    {
                        "value": "K",
                        "label": "10%",
                        "disabled": False
                    },
                    {
                        "value": "M",
                        "label": "20%",
                        "disabled": False
                    }
                ]
            },
            "filmProps": {},
            "seedProps": [],
            "displayAllCeProps": False,
            "tcc": "",
            "vcac": ""
        }
    ],
    "plotType": "Imp,ESR",
    "res": 0,
    "spiceFileFormat": "CKT",
    "spiceFreq": 10000,
    "start": "10000",
    "stop": "10000000000",
    "tempRise": 20,
    "session": ""
}

for c in part_number_config_list:
    if "pF" in c["capDisplay"]:
        print(f"ignore - {c['capDisplay']}")
    elif "AUTO" in c["basePn"]:
        print(f"ignore automotive type - {c['capDisplay']}")
    else:
        print(c)
        url = "https://ksim3.kemet.com/api/csv"
        print("Fetching csv for capacitance:", c)
        for plot_type in plot_types:
            updated_payload_part = {
            "id": 1,
            "instances": 1,
            "capDisplay": c["capDisplay"],
            "dielectric": c["dielectric"],
            "maxTemp": c["maxTemp"],
            "kemetPn": c["kemetPn"],
            "basePn": c["basePn"],
            "series": c["series"],
            "appDef": "Commercial/Standard Chips",
            "spicePn": "",
            "capType": c["capType"],
            "capValue": 10,
            "voltageRating": c["voltageRating"],
            "ceProps": [],
            "hidden": False,
            "param": {
                "qty": {
                    "title": "Qty",
                    "select": 1,
                    "min": 1,
                    "max": 1000,
                    "step": 1,
                    "disabled": False,
                    "width": 6
                },
                "bias": {
                    "title": "Bias (VDC)",
                    "select": 0,
                    "min": 0,
                    "max": 10,
                    "step": 0.1,
                    "disabled": False,
                    "width": 6
                },
                "tempAmbient": {
                    "title": "Amb (°C)",
                    "select": c["param"]["tempAmbient"]["select"],
                    "min": c["param"]["tempAmbient"]["min"],
                    "max": c["param"]["tempAmbient"]["max"],
                    "step": 1,
                    "disabled": False,
                    "width": 6
                }
            },
            "tolerance": {
                "title": "Tolerance",
                "select": "K",
                "disabled": False,
                "hidden": False,
                "options": [
                    {
                        "value": "B",
                        "label": ".1pF",
                        "disabled": False
                    },
                    {
                        "value": "C",
                        "label": ".25pF",
                        "disabled": False
                    },
                    {
                        "value": "D",
                        "label": ".5pF",
                        "disabled": False
                    },
                    {
                        "value": "F",
                        "label": "1%",
                        "disabled": False
                    },
                    {
                        "value": "G",
                        "label": "2%",
                        "disabled": False
                    },
                    {
                        "value": "J",
                        "label": "5%",
                        "disabled": False
                    },
                    {
                        "value": "K",
                        "label": "10%",
                        "disabled": False
                    },
                    {
                        "value": "M",
                        "label": "20%",
                        "disabled": False
                    }
                ]
            },
            "filmProps": {},
            "seedProps": [],
            "displayAllCeProps": False,
            "tcc": "",
            "vcac": ""
            }
            payload["parts"][1] = updated_payload_part
            payload["plotType"] = plot_type

            response = requests.post(url, json=payload)
            print("CSV data for", c["kemetPn"], ":\n", response.text[:200], "\n...")

            df = pd.read_csv(StringIO(response.text))
            if plot_type == "Imp,ESR":
                df = df.drop(columns=["Unnamed: 5"])
            elif plot_type == "Vbias":
                df = df.drop(columns=["Unnamed: 3", "Combined - Change %"])
            print(df.head())
            df.to_csv(f"{capacitor_downloaded_files_directory}/{c['basePn']}_{plot_type}.csv")

            # fig, ax = plt.subplots(2, 1)
            # ax[0].loglog(df["Frequency (Hz)"], df[f"{c['basePn']} - Imp"])
            # ax[0].set_ylabel(r"|Z| \ $\Omega$")
            # ax[1].loglog(df["Frequency (Hz)"], df[f"{c['basePn']} - ESR"])
            # ax[1].set_xlabel(r"f / Hz")
            # ax[1].set_ylabel(r"ESR \ $\Omega$")

            # ax[0].grid()
            # ax[1].grid()
            # plt.show()

types_list = []
# types_list.append({"type":"tantalum","cathode":"Poly","partStatus":"active"})
types_list.append({"type": "ceramic", "partStatus": "active"})
# types_list.append({"type":"tantalum","cathode":"MnO2","partStatus":"active"})
# types_list.append({"type":"film","partStatus":"active"})

# series overview
# {'type': 'ceramic', 'partStatus': 'active', 'series': 'AC Rated (CAN Series)'}
# {'type': 'ceramic', 'partStatus': 'active', 'series': 'ArcShield'}

configs_to_fetch = types_list.copy()

# get series for type
series = []

for type in types_list:
    url = "https://ksim3.kemet.com/series"
    response = requests.post(url, json=type)
    # type["series"] = response.json()["series"]
    series_item = response.json()
    for i in series_item:
        item = type.copy()
        item["series"] = i["series"]
        configs_to_fetch.append(item)
        print(item)

    if debug:
        print("Status Code:", response.status_code)
        print("Response Body:", response.text)

# get sizes
sizes = []
print("Fetching sizes...")
configs_with_sizes = []

for config in configs_to_fetch:
    url = "https://ksim3.kemet.com/size"
    print("Fetching size for config:", config)
    response = requests.post(url, json=config)
    for size in response.json():
        item = config.copy()
        item["size"] = size["case_Size"]
        configs_with_sizes.append(item)
        print("configs with sizes item:", item)

# Fetching size for config: {'type': 'ceramic', 'partStatus': 'active', 'series': 'AC Rated (CAN Series)'}
# configs with sizes item: {'type': 'ceramic', 'partStatus': 'active', 'series': 'AC Rated (CAN Series)', 'size': 'C0805'}
# configs with sizes item: {'type': 'ceramic', 'partStatus': 'active', 'series': 'AC Rated (CAN Series)', 'size': 'C1206'}

