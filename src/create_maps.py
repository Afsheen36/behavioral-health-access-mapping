from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "county_analysis_base.parquet"
)

FIGURE_DIR = (
    PROJECT_ROOT
    / "results"
    / "figures"
)


# ---------------------------------------------------------
# Geographic preparation
# ---------------------------------------------------------

def prepare_contiguous_us(gdf):
    """
    Keep the contiguous 48 states + DC for the first
    national map series.

    Alaska and Hawaii will be handled separately later.
    """

    return gdf.loc[
        ~gdf["STUSPS"].isin(["AK", "HI"])
    ].copy()


# ---------------------------------------------------------
# Save continuous-rate map
# ---------------------------------------------------------

def save_rate_map(
    gdf,
    column,
    title,
    filename,
    legend_label,
):
    """
    Create a county-level choropleth for a continuous rate.

    The display scale is capped at the 95th percentile
    so extreme outliers do not flatten most county-level
    differences.

    Original data values are not modified.
    """

    plot_data = gdf.copy()

    upper_limit = plot_data[column].quantile(0.95)

    plot_data["map_value"] = (
        plot_data[column]
        .clip(upper=upper_limit)
    )

    fig, ax = plt.subplots(
        figsize=(14, 9)
    )

    plot_data.plot(
        column="map_value",
        ax=ax,
        cmap="viridis",
        linewidth=0.10,
        edgecolor="white",
        legend=True,
        missing_kwds={
            "color": "lightgrey",
            "edgecolor": "white",
            "label": "Missing",
        },
        legend_kwds={
            "label": (
                f"{legend_label}\n"
                "Display capped at 95th percentile"
            ),
            "shrink": 0.65,
        },
    )

    ax.set_title(
        title,
        fontsize=17,
        pad=18,
    )

    ax.axis("off")

    plt.tight_layout()

    output = FIGURE_DIR / filename

    # Write through an explicit binary file handle.
    # This avoids the Windows path-writing issue encountered
    # with Pillow's direct filename handling.
    with output.open("wb") as file:
        fig.savefig(
            file,
            format="png",
            dpi=300,
            bbox_inches="tight",
        )

    plt.close(fig)

    print(
        f"Saved: {output} "
        f"(95th percentile = {upper_limit:.2f})"
    )


# ---------------------------------------------------------
# Save RUCC map
# ---------------------------------------------------------

def save_rucc_map(gdf):
    """
    Plot USDA Rural-Urban Continuum Codes as nine
    discrete categories.
    """

    colors = plt.cm.plasma(
        [i / 8 for i in range(9)]
    )

    cmap = ListedColormap(colors)

    norm = BoundaryNorm(
        boundaries=[
            0.5,
            1.5,
            2.5,
            3.5,
            4.5,
            5.5,
            6.5,
            7.5,
            8.5,
            9.5,
        ],
        ncolors=9,
    )

    fig, ax = plt.subplots(
        figsize=(14, 9)
    )

    gdf.plot(
        column="rucc_2023",
        ax=ax,
        cmap=cmap,
        norm=norm,
        linewidth=0.08,
        edgecolor="white",
        legend=True,
        legend_kwds={
            "label": (
                "RUCC 2023\n"
                "1-3 Metropolitan | "
                "4-9 Nonmetropolitan"
            ),
            "ticks": list(range(1, 10)),
            "shrink": 0.65,
        },
    )

    ax.set_title(
        "USDA Rural-Urban Continuum Codes, 2023",
        fontsize=17,
        pad=18,
    )

    ax.axis("off")

    plt.tight_layout()

    output = FIGURE_DIR / "rucc_2023.png"

    with output.open("wb") as file:
        fig.savefig(
            file,
            format="png",
            dpi=300,
            bbox_inches="tight",
        )

    plt.close(fig)

    print(
        f"Saved: {output}"
    )


# ---------------------------------------------------------
# Save zero-resource map
# ---------------------------------------------------------

def save_zero_resource_map(gdf):
    """
    Create a binary map showing counties with both:

    1. zero recorded psychiatrists
    2. zero matched SAMHSA facility records
    """

    plot_data = gdf.copy()

    plot_data["zero_resource_overlap"] = (
        (
            plot_data["psychiatrists_total_2023"] == 0
        )
        &
        (
            plot_data["facility_records_total"] == 0
        )
    )

    fig, ax = plt.subplots(
        figsize=(14, 9)
    )

    # Background
    plot_data.plot(
        ax=ax,
        color="#eeeeee",
        edgecolor="white",
        linewidth=0.10,
    )

    # Counties meeting both conditions
    zero = plot_data.loc[
        plot_data["zero_resource_overlap"]
    ]

    zero.plot(
        ax=ax,
        color="#9b2226",
        edgecolor="white",
        linewidth=0.10,
    )

    legend_elements = [
        Patch(
            facecolor="#9b2226",
            label=(
                "Zero psychiatrists + "
                "zero matched facility records"
            ),
        ),
        Patch(
            facecolor="#eeeeee",
            label="All other counties",
        ),
    ]

    ax.legend(
        handles=legend_elements,
        loc="lower left",
        frameon=False,
        fontsize=10,
    )

    ax.set_title(
        (
            "Counties with Zero Recorded Psychiatrists "
            "and Zero Matched Facility Records"
        ),
        fontsize=17,
        pad=18,
    )

    ax.axis("off")

    plt.tight_layout()

    output = (
        FIGURE_DIR
        / "zero_resource_overlap.png"
    )

    with output.open("wb") as file:
        fig.savefig(
            file,
            format="png",
            dpi=300,
            bbox_inches="tight",
        )

    plt.close(fig)

    print(
        f"Saved: {output} "
        f"({len(zero):,} contiguous-US counties)"
    )


# ---------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------

def main():

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Loading integrated county dataset..."
    )

    gdf = gpd.read_parquet(
        DATA_FILE
    )

    print(
        f"Primary analysis records: "
        f"{len(gdf):,}"
    )

    contiguous = prepare_contiguous_us(
        gdf
    )

    print(
        f"Contiguous-US records mapped: "
        f"{len(contiguous):,}"
    )

    # -----------------------------------------------------
    # Map 1: Psychiatrist supply
    # -----------------------------------------------------

    save_rate_map(
        contiguous,
        column="psychiatrists_per_100k_2023",
        title=(
            "Psychiatrist Supply by U.S. County, 2023"
        ),
        filename="psychiatrists_per_100k.png",
        legend_label=(
            "Psychiatrists per 100,000 residents"
        ),
    )

    # -----------------------------------------------------
    # Map 2: Rurality
    # -----------------------------------------------------

    save_rucc_map(
        contiguous
    )

    # -----------------------------------------------------
    # Map 3: Facility infrastructure
    # -----------------------------------------------------

    save_rate_map(
        contiguous,
        column="facility_records_per_100k",
        title=(
            "Matched Behavioral-Health Facility Records "
            "per 100,000 Residents"
        ),
        filename="facility_records_per_100k.png",
        legend_label=(
            "Matched facility records per 100,000 residents"
        ),
    )

    # -----------------------------------------------------
    # Map 4: Zero-resource overlap
    # -----------------------------------------------------

    save_zero_resource_map(
        contiguous
    )

    print(
        "\nNational county maps created successfully."
    )


if __name__ == "__main__":
    main()