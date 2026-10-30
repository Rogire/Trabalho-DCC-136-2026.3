import re
import numpy as np
import matplotlib.pyplot as plt


def plot_instance_sums(results,
                       title="Soma das distâncias por instância",
                       xlabel="Instância (grupos)", ylabel="Soma (distância km)",
                       time=False,
                       figsize=(12, 6),
                       annotate=True,
                       logy=False,
                       show_mean=False,
                       show_minmax=False,
                       tight_ylim=False,
                       save_path=None):
    """
    results: lista de dicts no formato [{'file': 'Instancia1_G3', 'sum': np.float64(...)}, ...]
    """

    def group_num(name):
        m = re.search(r'G(\d+)$', name)
        return int(m.group(1)) if m else float("inf")

    rows = sorted(results, key=lambda r: group_num(r["file"]))
    xs    = [group_num(r["file"])   for r in rows]
    ys    = [(float(r["time"]) if time else float(r["sum"]))        for r in rows]
    names = [r["file"]              for r in rows]

    if time:
        ylabel = "Tempo (s)"
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(xs, ys, marker="o", linestyle="-",
            color="C0", markersize=8,
            label="tempo (s)" if time else"distância (km)", zorder=3)

    if annotate:
        for x, y, n in zip(xs, ys, names):
            ax.annotate(
                n, (x, y),
                textcoords="offset points",
                xytext=(0, 11),
                ha="center",
                fontsize=9,
                color="C0",
            )

    if show_mean:
        mean = float(np.mean(ys))
        ax.axhline(mean, color="C1", linestyle="--", linewidth=1.2,
                   label=f"Média = {mean:.2f}", zorder=2)

    if show_minmax:
        ax.axhline(min(ys), color="C2", linestyle=":", linewidth=1.0,
                   label=f"Mín = {min(ys):.2f}", zorder=2)
        ax.axhline(max(ys), color="C3", linestyle=":", linewidth=1.0,
                   label=f"Máx = {max(ys):.2f}", zorder=2)

    ax.set_xticks(xs)
    ax.set_xticklabels([f"G{x}" for x in xs])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3, zorder=0)

    if logy:
        ax.set_yscale("log")
    elif tight_ylim:
        pad = (max(ys) - min(ys)) * 0.05
        ax.set_ylim(min(ys) - pad, max(ys) + pad)

    if any([show_mean, show_minmax]):
        ax.legend(loc="upper left", frameon=True)

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig, ax