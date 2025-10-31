"""Component cost models.

According to 'Component Cost Models for Multi-Objective Optimizations of Switched-Mode Power Converters',
Ralph Burkart and Johann W. Kolar.
"""

# 3rd party libraries


# Fix cost values according to the above cited paper
COST_MODEL_DICT = {
    "b_electrolytic": 1.437e-3,   # €/V
    "c_electrolytic": 24.757e-15,  # €/(F*V²)
    "a_film": -1.022,             # €
    "b_film": 2.426e-3,           # €/V
    "c_film": 54.956e-9,          # €/F
}

def cost_electrolytic_capacitor(voltage_rated: float, capacitance_rated: float) -> float:
    """
    Calculate the cost in euro of a electrolytic capacitor.

    :param voltage_rated: rated capacitor voltage in V
    :type voltage_rated: float
    :param capacitance_rated: rated capacitor capacitance in F
    :type capacitance_rated: float
    :return: Cost of the capacitor
    :rtype: float
    """
    cost: float = COST_MODEL_DICT["b_electrolytic"] * voltage_rated + COST_MODEL_DICT["c_electrolytic"] * capacitance_rated * voltage_rated ** 2

    return cost


def cost_film_capacitor(voltage_rated: float, capacitance_rated: float) -> float:
    """
    Calculate the cost in euro of a film capacitor.

    :param voltage_rated: rated capacitor voltage in V
    :type voltage_rated: float
    :param capacitance_rated: rated capacitor capacitance in F
    :type capacitance_rated: float
    :return: Cost of the capacitor
    :rtype: float
    """
    cost: float = COST_MODEL_DICT["a_film"] + COST_MODEL_DICT["b_film"] * voltage_rated + COST_MODEL_DICT["c_film"] * capacitance_rated

    return cost
