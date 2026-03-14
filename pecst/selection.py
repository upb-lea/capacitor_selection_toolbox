"""Select capacitors according to the requirements."""
import pandas as pd

# own libraries
from pecst.ceramic.selection import select_ceramic_capacitors
from pecst.film.selection import select_film_capacitors
from pecst.electrolytic.selection import select_electrolytic_capacitors
from pecst.cst_dataclasses import CapacitorRequirements, CapacitorType

def select_capacitors(c_requirements: CapacitorRequirements) -> tuple[list[str], list[pd.DataFrame]]:
    """
    Capacitor selection of all types: film, ceramic, electrolytic.

    :param c_requirements: Capacitor requirements
    :type c_requirements: CapacitorRequirements
    """
    c_db_film: list[pd.DataFrame] = []
    c_ceramic_db_list: list[pd.DataFrame] = []
    c_electrolytic_db_list: list[pd.DataFrame] = []
    technology_list: list[str] = []
    if CapacitorType.CeramicCapacitor in c_requirements.capacitor_type_list:
        c_ceramic_name_list, c_ceramic_db_list = select_ceramic_capacitors(c_requirements)
        technology_list.append("ceramic")
    if CapacitorType.FilmCapacitor in c_requirements.capacitor_type_list:
        c_film_name_list, c_film_db_list = select_film_capacitors(c_requirements)
        technology_list.append("film")
        c_db_film = [pd.concat(c_film_db_list)]
    if CapacitorType.ElectrolyticCapacitor in c_requirements.capacitor_type_list:
        c_electrolytic_name_list, c_electrolytic_db_list = select_electrolytic_capacitors(c_requirements)
        technology_list.append("electrolytic")

    c_db = c_ceramic_db_list + c_db_film + c_electrolytic_db_list

    return technology_list, c_db
