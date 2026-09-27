from pathlib import Path

import geopandas as gpd
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = PROJECT_ROOT / "data" / "processed" / "county_analysis_base.parquet"
TABLE_DIR = PROJECT_ROOT / "results" / "tables"

TABLE_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:

    print("Loading integrated county analysis dataset...")

    gdf = gpd.read_parquet(DATA_FILE)

    # -----------------------------------------------------
    # Arizona subset
    # -----------------------------------------------------

    az = gdf[gdf["STUSPS"] == "AZ"].copy()

    print(f"Arizona counties: {len(az)}")

    assert len(az) == 15
    assert az["GEOID"].is_unique

    # -----------------------------------------------------
    # Resource indicators
    # -----------------------------------------------------

    az["zero_psychiatrists"] = (
        az["psychiatrists_total_2023"] == 0
    )

    az["zero_facilities"] = (
        az["facility_records_total"] == 0
    )

    az["zero_both_resources"] = (
        az["zero_psychiatrists"]
        & az["zero_facilities"]
    )

    # -----------------------------------------------------
    # Resource profile
    # -----------------------------------------------------

    conditions = [
        (~az["zero_psychiatrists"]) & (~az["zero_facilities"]),
        az["zero_psychiatrists"] & (~az["zero_facilities"]),
        (~az["zero_psychiatrists"]) & az["zero_facilities"],
        az["zero_psychiatrists"] & az["zero_facilities"],
    ]

    labels = [
        "Both measured resources",
        "Facilities only",
        "Psychiatrists only",
        "Neither measured resource",
    ]

    az["resource_profile"] = pd.NA

    for condition, label in zip(conditions, labels):
        az.loc[condition, "resource_profile"] = label

    # -----------------------------------------------------
    # Arizona analytical table
    # -----------------------------------------------------

    columns = [
        "GEOID",
        "NAMELSAD",
        "population_2024",
        "rucc_2023",
        "metro_status_2023",
        "poverty_pct_2024",
        "uninsured_pct_2024",
        "median_household_income_2024",
        "psychiatrists_total_2023",
        "psychiatrists_per_100k_2023",
        "facility_records_total",
        "facility_records_per_100k",
        "mental_health_facility_records",
        "substance_use_facility_records",
        "resource_profile",
    ]

    az_table = az[columns].sort_values(
        "psychiatrists_per_100k_2023"
    )

    az_table.to_csv(
        TABLE_DIR / "arizona_county_profile.csv",
        index=False,
    )

    # -----------------------------------------------------
    # Arizona summary
    # -----------------------------------------------------

    summary = pd.DataFrame(
        {
            "indicator": [
                "Arizona counties",
                "Zero psychiatrists",
                "Zero matched facility records",
                "Neither measured resource",
                "Metropolitan counties",
                "Nonmetropolitan counties",
            ],
            "counties": [
                len(az),
                az["zero_psychiatrists"].sum(),
                az["zero_facilities"].sum(),
                az["zero_both_resources"].sum(),
                (az["metro_status_2023"] == "Metropolitan").sum(),
                (az["metro_status_2023"] == "Nonmetropolitan").sum(),
            ],
        }
    )

    summary["percent_counties"] = (
        summary["counties"] / len(az) * 100
    )

    summary.to_csv(
        TABLE_DIR / "arizona_resource_summary.csv",
        index=False,
    )

    # -----------------------------------------------------
    # Resource-profile distribution
    # -----------------------------------------------------

    profiles = (
        az["resource_profile"]
        .value_counts(dropna=False)
        .rename_axis("resource_profile")
        .reset_index(name="counties")
    )

    profiles["percent_counties"] = (
        profiles["counties"] / len(az) * 100
    )

    profiles.to_csv(
        TABLE_DIR / "arizona_resource_profiles.csv",
        index=False,
    )

    # -----------------------------------------------------
    # Console output
    # -----------------------------------------------------

    print("\nArizona resource summary:")
    print(summary.to_string(index=False))

    print("\nArizona resource profiles:")
    print(profiles.to_string(index=False))

    print("\nCounty profile:")
    print(
        az_table[
            [
                "NAMELSAD",
                "metro_status_2023",
                "psychiatrists_per_100k_2023",
                "facility_records_per_100k",
                "resource_profile",
            ]
        ].to_string(index=False)
    )

    print("\nSaved:")
    print(TABLE_DIR / "arizona_county_profile.csv")
    print(TABLE_DIR / "arizona_resource_summary.csv")
    print(TABLE_DIR / "arizona_resource_profiles.csv")

    print("\nArizona deep-dive analysis completed successfully.")


if __name__ == "__main__":
    main()