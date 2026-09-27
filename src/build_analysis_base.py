from pathlib import Path

import geopandas as gpd
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

GEOGRAPHY_FILE = PROCESSED_DATA_DIR / "county_geography.parquet"
WORKFORCE_FILE = PROCESSED_DATA_DIR / "county_workforce.parquet"
ACS_FILE = PROCESSED_DATA_DIR / "county_acs_context.parquet"

OUTPUT_FILE = PROCESSED_DATA_DIR / "county_analysis_base.parquet"


def main() -> None:

    print("Loading county geography...")
    geography = gpd.read_parquet(GEOGRAPHY_FILE)

    print("Loading AHRF workforce...")
    workforce = pd.read_parquet(WORKFORCE_FILE)

    print("Loading ACS context...")
    acs = pd.read_parquet(ACS_FILE)

    print(f"\nGeography records: {len(geography):,}")
    print(f"Workforce records: {len(workforce):,}")
    print(f"ACS records: {len(acs):,}")

    # -----------------------------------------------------
    # Merge workforce onto validated Census geography
    # -----------------------------------------------------

    merged = geography.merge(
        workforce,
        on="GEOID",
        how="left",
        validate="one_to_one",
        indicator="workforce_merge",
    )

    print("\nWorkforce merge:")
    print(merged["workforce_merge"].value_counts().to_string())

    merged = merged.drop(columns="workforce_merge")

    # -----------------------------------------------------
    # Merge ACS context
    # -----------------------------------------------------

    merged = merged.merge(
        acs,
        on="GEOID",
        how="left",
        validate="one_to_one",
        indicator="acs_merge",
    )

    print("\nACS merge:")
    print(merged["acs_merge"].value_counts().to_string())

    unmatched_acs = merged.loc[
        merged["acs_merge"] != "both",
        ["GEOID", "NAMELSAD", "STUSPS"],
    ]

    print(
        f"\nGeography records without ACS match: "
        f"{len(unmatched_acs):,}"
    )

    if len(unmatched_acs) > 0:
        print(unmatched_acs.to_string(index=False))

    merged = merged.drop(columns="acs_merge")

    # -----------------------------------------------------
    # Derived workforce rates
    # -----------------------------------------------------

    merged["psychiatrists_per_100k_2023"] = (
        merged["psychiatrists_total_2023"]
        / merged["population_2024"]
        * 100_000
    )

    merged["md_patient_care_psychiatrists_per_100k_2023"] = (
        merged["psychiatrists_md_patient_care_2023"]
        / merged["population_2024"]
        * 100_000
    )

    # -----------------------------------------------------
    # Quality control
    # -----------------------------------------------------

    print(
        "\nMissing population after merge:",
        merged["population_2024"].isna().sum(),
    )

    print(
        "Missing total psychiatrist counts:",
        merged["psychiatrists_total_2023"].isna().sum(),
    )

    print(
        "Missing psychiatrist rate:",
        merged["psychiatrists_per_100k_2023"].isna().sum(),
    )

    print(
        "Counties with zero total psychiatrists:",
        (merged["psychiatrists_total_2023"] == 0).sum(),
    )

    assert len(merged) == len(geography)
    assert merged["GEOID"].is_unique

    merged.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print(f"\nFinal analysis-base records: {len(merged):,}")
    print(f"Saved: {OUTPUT_FILE}")
    print(
        "Geography + workforce + ACS integration "
        "completed successfully."
    )


if __name__ == "__main__":
    main()