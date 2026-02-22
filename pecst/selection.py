
# own libraries
from pecst.foil.selection import select_foil_capacitors
from pecst.cst_dataclasses import CapacitorRequirements

def select_capacitors(c_requirements: CapacitorRequirements):
    c_name_list, c_db_list = select_foil_capacitors(c_requirements)

    return c_name_list, c_db_list


