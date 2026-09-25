from pathlib import Path

import geopandas as gpd
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

GEOGRAPHY_FILE = PROCESSED_DATA_DIR / "county_geography.parquet"
WORKFORCE_FILE = PROCESSED_DATA_DIR / "county_workforce.parquet"

OUTPUT_FILE = PROCESSED_DATA_DIR / "county_analysis_base.parquet"


def main() -> None:

    print("Loading county geography...")
    geography = gpd.read_parquet(GEOGRAPHY_FILE)

    print("Loading AHRF workforce...")
    workforce = pd.read_parquet(WORKFORCE_FILE)

    print(f"Geography records: {len(geography):,}")
    print(f"Workforce records: {len(workforce):,}")

    # -----------------------------------------------------
    # Merge workforce onto the validated Census geography
    # -----------------------------------------------------

    merged = geography.merge(
        workforce,
        on="GEOID",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    # -----------------------------------------------------
    # Merge quality control
    # -----------------------------------------------------

    print("\nMerge results:")
    print(merged["_merge"].value_counts().to_string())

    unmatched = merged.loc[
        merged["_merge"] != "both",
        ["GEOID", "NAMELSAD", "STUSPS"],
    ]

    print(f"\nGeography records without AHRF match: {len(unmatched):,}")

    if len(unmatched) > 0:
        print(unmatched.to_string(index=False))

    merged = merged.drop(columns="_merge")

    print(
        "\nMissing total psychiatrist counts after merge:",
        merged["psychiatrists_total_2023"].isna().sum(),
    )

    print(
        "Missing patient-care psychiatrist counts after merge:",
        merged["psychiatrists_md_patient_care_2023"].isna().sum(),
    )

    print(
        "Counties with zero total psychiatrists:",
        (merged["psychiatrists_total_2023"] == 0).sum(),
    )

    # Basic safeguards
    assert len(merged) == len(geography)
    assert merged["GEOID"].is_unique

    merged.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print(f"\nFinal analysis-base records: {len(merged):,}")
    print(f"Saved: {OUTPUT_FILE}")
    print("Geography + workforce integration completed successfully.")


if __name__ == "__main__":
    main()