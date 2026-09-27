from pathlib import Path

import geopandas as gpd
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "county_analysis_base.parquet"
)

TABLE_DIR = PROJECT_ROOT / "results" / "tables"


def main() -> None:

    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading integrated county analysis dataset...")

    gdf = gpd.read_parquet(DATA_FILE)

    print(f"Counties: {len(gdf):,}")

    # -----------------------------------------------------
    # 1. Overall descriptive statistics
    # -----------------------------------------------------

    variables = [
        "population_2024",
        "poverty_pct_2024",
        "uninsured_pct_2024",
        "median_household_income_2024",
        "psychiatrists_total_2023",
        "psychiatrists_per_100k_2023",
        "mental_health_facility_records",
        "substance_use_facility_records",
        "facility_records_total",
        "facility_records_per_100k",
    ]

    descriptive = (
        gdf[variables]
        .describe()
        .T
    )

    descriptive.to_csv(
        TABLE_DIR / "descriptive_statistics.csv"
    )

    # -----------------------------------------------------
    # 2. Metro vs nonmetro comparison
    # -----------------------------------------------------

    metro_comparison = (
        gdf
        .groupby("metro_status_2023")
        .agg(
            counties=("GEOID", "count"),

            population=(
                "population_2024",
                "sum",
            ),

            median_psychiatrists_per_100k=(
                "psychiatrists_per_100k_2023",
                "median",
            ),

            mean_psychiatrists_per_100k=(
                "psychiatrists_per_100k_2023",
                "mean",
            ),

            median_facility_records_per_100k=(
                "facility_records_per_100k",
                "median",
            ),

            mean_poverty_pct=(
                "poverty_pct_2024",
                "mean",
            ),

            mean_uninsured_pct=(
                "uninsured_pct_2024",
                "mean",
            ),
        )
        .reset_index()
    )

    metro_comparison.to_csv(
        TABLE_DIR / "metro_nonmetro_comparison.csv",
        index=False,
    )

    # -----------------------------------------------------
    # 3. Zero-resource indicators
    # -----------------------------------------------------

    gdf["zero_psychiatrists"] = (
        gdf["psychiatrists_total_2023"] == 0
    )

    gdf["zero_facility_records"] = (
        gdf["facility_records_total"] == 0
    )

    gdf["zero_both"] = (
        gdf["zero_psychiatrists"]
        & gdf["zero_facility_records"]
    )

    zero_summary = pd.DataFrame(
        {
            "indicator": [
                "Zero psychiatrists",
                "Zero matched facility records",
                "Zero psychiatrists AND zero matched facility records",
            ],
            "counties": [
                gdf["zero_psychiatrists"].sum(),
                gdf["zero_facility_records"].sum(),
                gdf["zero_both"].sum(),
            ],
        }
    )

    zero_summary["percent_counties"] = (
        zero_summary["counties"]
        / len(gdf)
        * 100
    )

    zero_summary.to_csv(
        TABLE_DIR / "zero_resource_summary.csv",
        index=False,
    )

    # -----------------------------------------------------
    # 4. Counties with zero workforce AND facilities
    # -----------------------------------------------------

    zero_both_counties = gdf.loc[
        gdf["zero_both"],
        [
            "GEOID",
            "NAMELSAD",
            "STUSPS",
            "population_2024",
            "poverty_pct_2024",
            "uninsured_pct_2024",
            "median_household_income_2024",
            "rucc_2023",
            "metro_status_2023",
        ],
    ].copy()

    zero_both_counties = (
        zero_both_counties
        .sort_values(
            "population_2024",
            ascending=False,
        )
    )

    zero_both_counties.to_csv(
        TABLE_DIR / "zero_workforce_and_facilities.csv",
        index=False,
    )

    # -----------------------------------------------------
    # 5. State-level summary
    # -----------------------------------------------------

    state_summary = (
        gdf
        .groupby(
            ["STUSPS", "STATE_NAME"]
        )
        .agg(
            counties=("GEOID", "count"),

            population=(
                "population_2024",
                "sum",
            ),

            zero_psychiatrist_counties=(
                "zero_psychiatrists",
                "sum",
            ),

            zero_facility_counties=(
                "zero_facility_records",
                "sum",
            ),

            zero_both_counties=(
                "zero_both",
                "sum",
            ),

            median_psychiatrists_per_100k=(
                "psychiatrists_per_100k_2023",
                "median",
            ),

            median_facility_records_per_100k=(
                "facility_records_per_100k",
                "median",
            ),
        )
        .reset_index()
    )

    state_summary.to_csv(
        TABLE_DIR / "state_access_summary.csv",
        index=False,
    )

    # -----------------------------------------------------
    # Console summary
    # -----------------------------------------------------

    print("\nZero-resource summary:")
    print(
        zero_summary.to_string(
            index=False
        )
    )

    print("\nMetro/nonmetro comparison:")
    print(
        metro_comparison.to_string(
            index=False
        )
    )

    print(
        "\nCounties with both zero psychiatrists "
        "and zero matched facility records:",
        gdf["zero_both"].sum(),
    )

    print(
        f"\nTables saved to: {TABLE_DIR}"
    )

    print(
        "Phase 7 descriptive analysis completed successfully."
    )


if __name__ == "__main__":
    main()
