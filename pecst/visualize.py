"""Visualize results."""

# 3rd party libraries
import pandas as pd
from matplotlib import pyplot as plt  # type: ignore

# own libraries


def generate_label(n_series, n_parallel, capacitor_id):
    """
    Generate labels for mouse hover.

    :param n_series: number of capacitors in series
    :type n_series: int
    :param n_parallel: number of capacitors in parallel
    :type n_parallel: int
    :param capacitor_id: capacitor ID
    :type capacitor_id: str
    :return: label string for the annotation
    """
    return f"s: {n_series}, p: {n_parallel}, o: {capacitor_id}"


def df_plot_pareto_front(df: pd.DataFrame, figure_size: tuple) -> None:
    """
    Plot an interactive Pareto diagram (losses vs. volume) to select the transformers to re-simulate.

    :param df: DataFrame
    :type df: pd.DataFrame
    :param figure_size: figures size as a x/y-tuple in mm, e.g. (160, 80)
    :type figure_size: tuple
    """
    names = df.apply(lambda x: generate_label(x["in_series_needed"], x["in_parallel_needed"], x["ordering_2_terminal"]), axis=1).values

    fig, ax = plt.subplots(figsize=[x / 25.4 for x in figure_size] if figure_size is not None else None, dpi=80)
    sc = plt.scatter(df["volume_total"], df["power_loss_total"], color=df["color"], s=15, label=df['label'])

    unique_labels = df['label'].unique()
    colors = df["color"].unique()
    color_map = {label: colors[count] for count, label in enumerate(unique_labels)}

    handles = []
    for label in unique_labels:
        handles.append(plt.Line2D(
            [], [], marker='o', linestyle='',
            color=color_map[label], label=label
        ))
    ax.legend(handles=handles)

    annot = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="w"),
                        arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    def update_annot(ind):
        pos = sc.get_offsets()[ind["ind"][0]]
        annot.xy = pos
        text = f"{[names[n] for n in ind['ind']]}"
        annot.set_text(text)
        annot.get_bbox_patch().set_alpha(0.4)

    def hover(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            cont, ind = sc.contains(event)
            if cont:
                update_annot(ind)
                annot.set_visible(True)
                fig.canvas.draw_idle()
            else:
                if vis:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)

    plt.xlabel(r'Volume / m³')
    plt.ylabel(r'$P_\mathrm{loss}$ / W')
    plt.grid()
    plt.tight_layout()
    plt.show()
