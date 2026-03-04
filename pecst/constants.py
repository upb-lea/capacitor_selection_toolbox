"""Constants for the capacitor selection toolbox."""

# 3rd party libraries
import pandas as pd

# milli, micro, nano to normal
MILLI_TO_NORM = 1e-3
MICRO_TO_NORM = 1e-6
NANO_TO_NORM = 1e-9
PICO_TO_NORM = 1e-12

# normal to milli
NORM_TO_MILLI = 1e3

# qubic milli/deci-meter
QUBIC_METER_TO_QUBIC_DECI_METER = 1e3
QUBIC_METER_TO_QUBIC_CENTI_METER = 1e6
QUBIC_METER_TO_QUBIC_MILLI_METER = 1e9

# square milli/deci-meter
SQUARE_METER_TO_SQUARE_DECI_METER = 1e2
SQUARE_METER_TO_SQUARE_CENTI_METER = 1e4
SQUARE_METER_TO_SQUARE_MILLI_METER = 1e6

# folder names
FOIL_CAPACITOR_ESR_OVER_FREQUENCY_DIRECTORY = "foil_downloads"
FOIL_CAPACITOR_DATA_DIRECTORY = "foil_capacitor_data"
ELECTROLYTIC_CAPACITOR_DATA_DIRECTORY = "electrolytic_capacitor_data"
ELECTROLYTIC_CAPACITOR_DOWNLOAD_DIRECTORY = "electrolytic_downloads"
CERAMIC_CAPACITOR_DOWNLOAD_DIRECTORY = "ceramic_downloads"


# available foil capacitor series
FOIL_CAPACITOR_SERIES_NAME_LIST = ["B3271*P", "B3272*AGT", "B3277*P"]
FOIL_CAPACITOR_SERIES_VALUES = "series_values"

ELECTROLYTIC_CAPACITOR_SERIES_NAME_LIST = ["056057psmsi"]

TEMPERATURE_85 = 85
TEMPERATURE_105 = 105
TEMPERATURE_125 = 125

SMD_SIZE_DICT = {"size": ["C0402", "C0603", "C0805", "C1206", "C1210", "C1808", "C1812", "C1825", "C2220", "C2225", "C3040", "CAN06", "CAN08", "CAN12",
                          "CAN13", "CAN17", "CAN18", "CAN19", "CAN21", "CAN22", "CKC18", "CKC21", "CKC33", "CAS21"],
                 "area": [5.16128e-07, 1.1612879999999997e-06, 2.58064e-06, 4.645151999999999e-06, 7.74192e-06, 9.290303999999999e-06, 1.3935455999999997e-05,
                          2.9032199999999996e-05, 2.8387039999999997e-05, 3.5483799999999994e-05, 7.74192e-05, 1.1612879999999997e-06, 2.58064e-06,
                          4.645151999999999e-06, 7.74192e-06, 9.290303999999999e-06, 1.3935455999999997e-05, 2.9032199999999996e-05, 2.8387039999999997e-05,
                          3.5483799999999994e-05, 1.3935455999999997e-05, 2.8387039999999997e-05, 9.290304e-05, 2.8387039999999997e-05],
                 "footprint_area": [6.2451488e-07, 1.4051584799999996e-06, 3.1225744000000003e-06, 5.6206339199999986e-06, 9.3677232e-06, 1.124126784e-05,
                                    1.6861901759999998e-05, 3.5128962000000005e-05, 3.43483184e-05, 4.2935398e-05, 9.367723200000001e-05,
                                    1.4051584799999996e-06, 3.1225744000000003e-06, 5.6206339199999986e-06, 9.3677232e-06, 1.124126784e-05,
                                    1.6861901759999998e-05, 3.5128962000000005e-05, 3.43483184e-05, 4.2935398e-05, 1.6861901759999998e-05, 3.43483184e-05,
                                    0.00011241267840000002, 3.43483184e-05]}

SMD_SIZE_DF = pd.DataFrame(SMD_SIZE_DICT)

VOLTAGE_CODE_KEMET_DICT = {"8": 10,
                           "4": 16,
                           "3": 25,
                           "5": 50,
                           "1": 100,
                           "2": 200,
                           "A": 250,
                           "C": 500,
                           "B": 630,
                           "D": 1000,
                           "F": 1500,
                           "G": 2000}

CAPACITANCE_TOLERANCE_KEMET_DICT = {"F": 0.01,
                                    "J": 0.05,
                                    "K": 0.1,
                                    "M": 0.2}

MATERIAL_KEMET_DICT = {"G": "C0G"}
