
# python libraries
import pathlib

# 3rd party libraries
import pandas as pd




def load_dc_film_capacitors():

    path = pathlib.Path(__file__)
    database_path = pathlib.PurePath(path.parents[0], "B3271*P.csv")

    c_df = pd.read_csv(database_path, sep=';', decimal=',')

    # drop unused columns to reduce the data set
    c_df = c_df.drop(columns=["multiplier_1", "multiplier_2", "MOQ", "p1_in_mm"])
    print(c_df.columns)

    # transfer the datasheet given units to SI units
    c_df['volume'] = c_df["width_in_mm"].astype(float) * 1e-3 * c_df["height_in_mm"].astype(float) * 1e-3 * c_df["length_in_mm"].astype(float) * 1e-3
    c_df['area'] = c_df["width_in_mm"].astype(float) * 1e-3 * c_df["length_in_mm"].astype(float) * 1e-3
    c_df = c_df.drop(columns=["width_in_mm", "height_in_mm", "length_in_mm"])

    c_df['capacitance'] = c_df["capacitance_in_uf"].astype(float) * 1e-6
    c_df = c_df.drop(columns=["capacitance_in_uf"])

    c_df["ESR_85degree_in_Ohm"] = c_df["ESR_85degree_in_mOhm"].astype(float) * 1e-3
    c_df = c_df.drop(columns=["ESR_85degree_in_mOhm"])

    c_df["ESL_in_H"] = c_df["ESL_in_nH"].astype(float) * 1e-9
    c_df = c_df.drop(columns=["ESL_in_nH"])

    return c_df








if __name__ == "__main__":
    load_dc_film_capacitors()

