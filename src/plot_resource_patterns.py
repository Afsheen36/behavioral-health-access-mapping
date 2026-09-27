from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


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

TABLE_DIR = (
    PROJECT_ROOT
    / "results"
    / "tables"
)


def main() -> None:

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Loading county analysis dataset...")

    gdf = gpd.read_parquet(DATA_FILE)

    # -----------------------------------------------------
    # Exclude unknown psychiatrist observations
    # -----------------------------------------------------

    analysis = gdf.loc[
        gdf["psychiatrists_total_2023"].notna()
    ].copy()

    print(
        f"Resource-profile counties: "
        f"{len(analysis):,}"
    )

    # -----------------------------------------------------
    # Construct resource profiles
    # -----------------------------------------------------

    psychiatrist_present = (
        analysis["psychiatrists_total_2023"] > 0
    )

    facility_present = (
        analysis["facility_records_total"] > 0
    )

    analysis["resource_profile"] = (
        "Neither measured resource"
    )

    analysis.loc[
        psychiatrist_present
        & facility_present,
        "resource_profile",
    ] = "Both measured resources"

    analysis.loc[
        ~psychiatrist_present
        & facility_present,
        "resource_profile",
    ] = "Facilities only"

    analysis.loc[
        psychiatrist_present
        & ~facility_present,
        "resource_profile",
    ] = "Psychiatrists only"

    # -----------------------------------------------------
    # Calculate metro/nonmetro percentages
    # -----------------------------------------------------

    summary = (
        analysis
        .groupby(
            [
                "metro_status_2023",
                "resource_profile",
            ]
        )
        .size()
        .reset_index(name="counties")
    )

    summary["percent"] = (
        summary["counties"]
        /
        summary.groupby(
            "metro_status_2023"
        )["counties"].transform("sum")
        * 100
    )

    profile_order = [
        "Both measured resources",
        "Facilities only",
        "Psychiatrists only",
        "Neither measured resource",
    ]

    pivot = (
        summary
        .pivot(
            index="metro_status_2023",
            columns="resource_profile",
            values="percent",
        )
        .reindex(
            columns=profile_order
        )
        .fillna(0)
    )

    # -----------------------------------------------------
    # Plot grouped bars
    # -----------------------------------------------------

    ax = pivot.plot(
        kind="bar",
        figsize=(11, 7),
        width=0.78,
    )

    ax.set_title(
        "Behavioral-Health Resource Profiles by County Rurality",
        fontsize=16,
        pad=15,
    )

    ax.set_xlabel("")

    ax.set_ylabel(
        "Percentage of counties",
        fontsize=11,
    )

    ax.tick_params(
        axis="x",
        rotation=0,
    )

    ax.legend(
        title="Resource profile",
        frameon=False,
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Percentage labels
    for container in ax.containers:
        ax.bar_label(
            container,
            fmt="%.1f%%",
            padding=3,
            fontsize=9,
        )

    plt.tight_layout()

    output = (
        FIGURE_DIR
        / "resource_profiles_by_rurality.png"
    )

    # Use binary file handle because of the Windows
    # PNG-writing issue encountered earlier.
    with output.open("wb") as file:
        plt.savefig(
            file,
            format="png",
            dpi=300,
            bbox_inches="tight",
        )

    plt.close()

    print(f"Saved: {output}")

    print(
        "\nResource-profile figure created successfully."
    )


if __name__ == "__main__":
    main()