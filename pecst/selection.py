"""Select capacitors according to the requirements."""

# own libraries
from pecst.ceramic.selection import select_ceramic_capacitors
from pecst.cst_dataclasses import CapacitorRequirements

def select_capacitors(c_requirements: CapacitorRequirements):
    """
    Capacitor selection of all types: foil, ceramic, electrolytic.

    :param c_requirements: Capacitor requirements
    :type c_requirements: CapacitorRequirements
    """
    # c_foil_name_list, c_foil_db_list = select_foil_capacitors(c_requirements)
    c_foil_name_list, c_foil_db_list = select_ceramic_capacitors(c_requirements)

    return c_foil_name_list, c_foil_db_list
