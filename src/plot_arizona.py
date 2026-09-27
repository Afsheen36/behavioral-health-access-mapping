from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "county_analysis_base.parquet"
)

FIGURE_DIR = PROJECT_ROOT / "results" / "figures"

OUTPUT_FILE = (
    FIGURE_DIR
    / "arizona_behavioral_health_resources.png"
)


def main() -> None:

    print("Loading integrated county dataset...")

    gdf = gpd.read_parquet(DATA_FILE)

    az = gdf[gdf["STUSPS"] == "AZ"].copy()

    assert len(az) == 15

    print(f"Arizona counties: {len(az)}")

    # -----------------------------------------------------
    # Plot psychiatrist supply
    # -----------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(11, 9)
    )

    az.plot(
        column="psychiatrists_per_100k_2023",
        cmap="viridis",
        linewidth=0.8,
        edgecolor="white",
        legend=True,
        ax=ax,
        missing_kwds={
            "color": "lightgrey",
            "label": "Missing",
        },
    )

    # -----------------------------------------------------
    # County labels
    # -----------------------------------------------------

    label_points = az.geometry.representative_point()

    for idx, row in az.iterrows():

        point = label_points.loc[idx]

        psychiatrist_rate = (
            row["psychiatrists_per_100k_2023"]
        )

        facility_count = row["facility_records_total"]

        label = (
            f"{row['NAME_x']}\n"
            f"Psych: {psychiatrist_rate:.1f}/100k\n"
            f"Facilities: {facility_count:.0f}"
        )

        ax.annotate(
            label,
            xy=(point.x, point.y),
            ha="center",
            va="center",
            fontsize=6,
        )

    # -----------------------------------------------------
    # Figure formatting
    # -----------------------------------------------------

    ax.set_title(
        "Arizona Behavioral Health Resource Distribution",
        fontsize=16,
        pad=15,
    )

    ax.text(
        0.5,
        -0.04,
        (
            "County shading: psychiatrists per 100,000 residents "
            "(AHRF 2023)\n"
            "Labels show psychiatrist rate and matched "
            "behavioral-health facility records."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
    )

    ax.set_axis_off()

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_FILE,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Saved: {OUTPUT_FILE}")
    print(
        "Arizona behavioral-health resource map "
        "created successfully."
    )


if __name__ == "__main__":
    main()