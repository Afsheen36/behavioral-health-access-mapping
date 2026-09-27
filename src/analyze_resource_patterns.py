from pathlib import Path

import geopandas as gpd
import pandas as pd


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

TABLE_DIR = (
    PROJECT_ROOT
    / "results"
    / "tables"
)


# ---------------------------------------------------------
# Main analysis
# ---------------------------------------------------------

def main() -> None:

    TABLE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Loading integrated county dataset...")

    gdf = gpd.read_parquet(DATA_FILE)

    print(
        f"Analysis records: {len(gdf):,}"
    )

    # -----------------------------------------------------
    # Identify counties with missing psychiatrist counts
    # -----------------------------------------------------

    missing_psychiatrists = (
        gdf["psychiatrists_total_2023"]
        .isna()
    )

    missing_count = (
        missing_psychiatrists.sum()
    )

    print(
        "Counties excluded from resource-profile "
        "analysis because psychiatrist count is missing:",
        missing_count,
    )

    # These counties remain in the master dataset.
    # They are excluded only from analyses that require
    # determining whether psychiatrist resources are present.
    analysis = gdf.loc[
        ~missing_psychiatrists
    ].copy()

    print(
        f"Resource-profile analysis records: "
        f"{len(analysis):,}"
    )

    # -----------------------------------------------------
    # Resource presence indicators
    # -----------------------------------------------------

    analysis["psychiatrists_present"] = (
        analysis["psychiatrists_total_2023"]
        > 0
    )

    analysis["facilities_present"] = (
        analysis["facility_records_total"]
        > 0
    )

    # -----------------------------------------------------
    # Four-category resource profile
    # -----------------------------------------------------

    analysis["resource_profile"] = (
        "Neither measured resource"
    )

    analysis.loc[
        analysis["psychiatrists_present"]
        & ~analysis["facilities_present"],
        "resource_profile",
    ] = "Psychiatrists only"

    analysis.loc[
        ~analysis["psychiatrists_present"]
        & analysis["facilities_present"],
        "resource_profile",
    ] = "Facilities only"

    analysis.loc[
        analysis["psychiatrists_present"]
        & analysis["facilities_present"],
        "resource_profile",
    ] = "Both measured resources"

    # -----------------------------------------------------
    # 1. National resource profile
    # -----------------------------------------------------

    resource_profile = (
        analysis["resource_profile"]
        .value_counts()
        .rename_axis("resource_profile")
        .reset_index(name="counties")
    )

    resource_profile["percent_counties"] = (
        resource_profile["counties"]
        / len(analysis)
        * 100
    )

    resource_profile.to_csv(
        TABLE_DIR
        / "resource_profile_summary.csv",
        index=False,
    )

    print("\nResource profile:")
    print(
        resource_profile.to_string(
            index=False
        )
    )

    # -----------------------------------------------------
    # 2. Resource profile by rurality
    # -----------------------------------------------------

    profile_by_rurality = (
        analysis
        .groupby(
            [
                "metro_status_2023",
                "resource_profile",
            ]
        )
        .size()
        .reset_index(
            name="counties"
        )
    )

    profile_by_rurality[
        "percent_within_rurality"
    ] = (
        profile_by_rurality["counties"]
        /
        profile_by_rurality.groupby(
            "metro_status_2023"
        )["counties"]
        .transform("sum")
        * 100
    )

    profile_by_rurality.to_csv(
        TABLE_DIR
        / "resource_profile_by_rurality.csv",
        index=False,
    )

    print(
        "\nResource profile by rurality:"
    )

    print(
        profile_by_rurality.to_string(
            index=False
        )
    )

    # -----------------------------------------------------
    # 3. Socioeconomic context by resource profile
    # -----------------------------------------------------

    socioeconomic = (
        analysis
        .groupby("resource_profile")
        .agg(
            counties=(
                "GEOID",
                "count",
            ),

            median_population=(
                "population_2024",
                "median",
            ),

            mean_poverty_pct=(
                "poverty_pct_2024",
                "mean",
            ),

            median_poverty_pct=(
                "poverty_pct_2024",
                "median",
            ),

            mean_uninsured_pct=(
                "uninsured_pct_2024",
                "mean",
            ),

            median_uninsured_pct=(
                "uninsured_pct_2024",
                "median",
            ),

            median_income=(
                "median_household_income_2024",
                "median",
            ),

            median_psychiatrists_per_100k=(
                "psychiatrists_per_100k_2023",
                "median",
            ),

            median_facilities_per_100k=(
                "facility_records_per_100k",
                "median",
            ),
        )
        .reset_index()
    )

    socioeconomic.to_csv(
        TABLE_DIR
        / "resource_profile_socioeconomic_context.csv",
        index=False,
    )

    print(
        "\nSocioeconomic context by resource profile:"
    )

    print(
        socioeconomic.to_string(
            index=False
        )
    )

    # -----------------------------------------------------
    # 4. Zero-resource counties
    # -----------------------------------------------------

    zero_resource = analysis.loc[
        analysis["resource_profile"]
        == "Neither measured resource"
    ].copy()

    zero_resource = zero_resource[
        [
            "GEOID",
            "NAMELSAD",
            "STUSPS",
            "STATE_NAME",
            "population_2024",
            "poverty_pct_2024",
            "uninsured_pct_2024",
            "median_household_income_2024",
            "rucc_2023",
            "metro_status_2023",
            "psychiatrists_total_2023",
            "facility_records_total",
        ]
    ].sort_values(
        "population_2024",
        ascending=False,
    )

    zero_resource.to_csv(
        TABLE_DIR
        / "zero_resource_counties.csv",
        index=False,
    )

    # -----------------------------------------------------
    # 5. Zero-resource counties by RUCC
    # -----------------------------------------------------

    zero_by_rucc = (
        zero_resource
        .groupby(
            [
                "rucc_2023",
                "metro_status_2023",
            ]
        )
        .size()
        .reset_index(
            name="zero_resource_counties"
        )
    )

    zero_by_rucc.to_csv(
        TABLE_DIR
        / "zero_resource_by_rucc.csv",
        index=False,
    )

    # -----------------------------------------------------
    # 6. State-level resource profiles
    # -----------------------------------------------------

    state_profile = (
        analysis
        .groupby(
            [
                "STUSPS",
                "STATE_NAME",
                "resource_profile",
            ]
        )
        .size()
        .reset_index(
            name="counties"
        )
    )

    state_profile.to_csv(
        TABLE_DIR
        / "state_resource_profiles.csv",
        index=False,
    )

    # -----------------------------------------------------
    # 7. Population represented by each profile
    # -----------------------------------------------------

    population_by_profile = (
        analysis
        .groupby("resource_profile")
        .agg(
            counties=(
                "GEOID",
                "count",
            ),

            population=(
                "population_2024",
                "sum",
            ),
        )
        .reset_index()
    )

    population_by_profile[
        "percent_population"
    ] = (
        population_by_profile["population"]
        / analysis["population_2024"].sum()
        * 100
    )

    population_by_profile.to_csv(
        TABLE_DIR
        / "resource_profile_population.csv",
        index=False,
    )

    # -----------------------------------------------------
    # 8. Document excluded counties
    # -----------------------------------------------------

    excluded = gdf.loc[
        missing_psychiatrists,
        [
            "GEOID",
            "NAMELSAD",
            "STUSPS",
            "STATE_NAME",
            "population_2024",
            "poverty_pct_2024",
            "uninsured_pct_2024",
            "median_household_income_2024",
            "rucc_2023",
            "metro_status_2023",
            "psychiatrists_total_2023",
            "facility_records_total",
        ],
    ].copy()

    excluded.to_csv(
        TABLE_DIR
        / "resource_profile_excluded_missing_psychiatrists.csv",
        index=False,
    )

    # -----------------------------------------------------
    # Console summary
    # -----------------------------------------------------

    print(
        "\nZero-resource counties:",
        len(zero_resource),
    )

    print(
        "\nExcluded counties with missing psychiatrist "
        "counts:",
        len(excluded),
    )

    print(
        "\nAnalysis tables saved to:",
        TABLE_DIR,
    )

    print(
        "\nPhase 9 resource-pattern analysis "
        "completed successfully."
    )


if __name__ == "__main__":
    main()