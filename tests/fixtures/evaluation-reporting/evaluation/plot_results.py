"""Draw invented saved estimates; this fixture performs no statistical analysis."""

import argparse
import json
from pathlib import Path


def read_estimates(path):
    return json.loads(path.read_text())


def build_figure(rows):
    import matplotlib.pyplot as plt
    import seaborn as sns

    with sns.axes_style("whitegrid"), sns.plotting_context("notebook"):
        figure, axes = plt.subplots(figsize=(7, 3.4), layout="constrained")
        for position, row in enumerate(rows):
            estimate = row["estimate"]
            if estimate is None:
                axes.text(
                    0.5,
                    position,
                    "No estimate",
                    transform=axes.get_yaxis_transform(),
                    ha="center",
                )
                continue
            axes.errorbar(
                estimate,
                position,
                xerr=[[estimate - row["lower"]], [row["upper"] - estimate]],
                fmt="o",
                color="0.2",
                capsize=4,
            )
        axes.set_yticks(
            range(len(rows)),
            [f"{row['scenario']} ({row['n']}/{row['planned']} runs)" for row in rows],
        )
        axes.set_ylim(len(rows) - 0.5, -0.5)
        axes.axvline(0, color="0.5", linestyle="--", linewidth=1)
        axes.set_xlabel("Mean score change (points)")
        axes.set_title("Saved estimates and 95% confidence intervals")
        sns.despine(ax=axes, left=True)
    return figure, axes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=Path("results/estimates.json"))
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    rows = read_estimates(arguments.inputs)
    arguments.output_dir.mkdir(parents=True, exist_ok=False)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, _ = build_figure(rows)
    try:
        figure.savefig(arguments.output_dir / "estimates.png", dpi=150)
    finally:
        plt.close(figure)


if __name__ == "__main__":
    main()
