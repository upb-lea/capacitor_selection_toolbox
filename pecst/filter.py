"""Capacitor Pareto front filtering."""

# 3rd party libraries
import pandas as pd
import numpy as np

# Faster than is_pareto_efficient_simple, but less readable.
def _is_pareto_efficient(costs: np.ndarray, return_mask: bool = True) -> np.ndarray:
    """
    Find the pareto-efficient points.

    :param costs: An (n_points, n_costs) array
    :type costs: np.array
    :param return_mask: True to return a mask
    :type return_mask: bool
    :return: An array of indices of pareto-efficient points.
        If return_mask is True, this will be an (n_points, ) boolean array
        Otherwise it will be a (n_efficient_points, ) integer array of indices.
    :rtype: np.array
    """
    is_efficient = np.arange(costs.shape[0])
    n_points = costs.shape[0]
    next_point_index = 0  # Next index in the is_efficient array to search for
    while next_point_index < len(costs):
        nondominated_point_mask: np.ndarray = np.array(np.any(costs < costs[next_point_index], axis=1))
        nondominated_point_mask[next_point_index] = True
        is_efficient = is_efficient[nondominated_point_mask]  # Remove dominated points
        costs = costs[nondominated_point_mask]
        next_point_index = np.sum(nondominated_point_mask[:next_point_index]) + 1
    if return_mask:
        is_efficient_mask = np.zeros(n_points, dtype=bool)
        is_efficient_mask[is_efficient] = True
        return is_efficient_mask
    else:
        return is_efficient

def _pareto_front_from_df(df: pd.DataFrame, x: str, y: str) -> pd.DataFrame:
    """
    Calculate the Pareto front from a Pandas dataframe. Return a Pandas dataframe.

    :param df: Pandas dataframe
    :type df: pd.DataFrame
    :return: Pandas dataframe with pareto efficient points
    :rtype: pd.DataFrame
    """
    x_vec = df[x][~pd.isnull(df[x])]
    y_vec = df[y][~pd.isnull(df[x])]
    numpy_zip = np.column_stack((x_vec, y_vec))
    pareto_tuple_mask_vec = _is_pareto_efficient(numpy_zip)
    pareto_df = df[~pd.isnull(df[x])][pareto_tuple_mask_vec]
    return pareto_df

def filter_df(df: pd.DataFrame, x: str = "volume_total", y: str = "power_loss_total", factor_min_dc_losses: float = 0.5,
              factor_max_dc_losses: float = 1000) -> pd.DataFrame:
    """
    Remove designs with too high losses compared to the minimum losses.

    :param df: pandas dataframe with study results
    :type df: pd.DataFrame
    :param x: x-value name for Pareto plot filtering
    :type x: str
    :param y: y-value name for Pareto plot filtering
    :type y: str
    :param factor_min_dc_losses: filter factor for the minimum dc losses
    :type factor_min_dc_losses: float
    :param factor_max_dc_losses: dc_max_loss = factor_max_dc_losses * min_available_dc_losses_in_pareto_front
    :type factor_max_dc_losses: float
    :returns: pandas dataframe with Pareto front near points
    :rtype: pd.DataFrame
    """
    pareto_df: pd.DataFrame = _pareto_front_from_df(df, x=x, y=y)

    vector_to_sort = np.array([pareto_df[x], pareto_df[y]])

    # sorting 2d array by 1st row
    # https://stackoverflow.com/questions/49374253/sort-a-numpy-2d-array-by-1st-row-maintaining-columns
    sorted_vector = vector_to_sort[:, vector_to_sort[0].argsort()]
    x_pareto_vec = sorted_vector[0]
    y_pareto_vec = sorted_vector[1]

    total_losses_list = df[y][~pd.isnull(df[y])].to_numpy()

    min_total_dc_losses = total_losses_list[np.argmin(total_losses_list)]
    loss_offset = factor_min_dc_losses * min_total_dc_losses

    ref_loss_max = np.interp(df[x], x_pareto_vec, y_pareto_vec) + loss_offset
    # clip losses to a maximum of the minimum losses
    ref_loss_max = np.clip(ref_loss_max, a_min=-1, a_max=factor_max_dc_losses * min_total_dc_losses)

    pareto_df_offset: pd.DataFrame = df[df[y] < ref_loss_max]

    return pareto_df_offset
