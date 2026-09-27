from pathlib import Path

import geopandas as gpd
import pandas as pd


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

GEOGRAPHY_FILE = PROCESSED_DATA_DIR / "county_geography.parquet"
WORKFORCE_FILE = PROCESSED_DATA_DIR / "county_workforce.parquet"
ACS_FILE = PROCESSED_DATA_DIR / "county_acs_context.parquet"
RURALITY_FILE = PROCESSED_DATA_DIR / "county_rurality.parquet"
FACILITIES_FILE = PROCESSED_DATA_DIR / "county_facilities.parquet"

OUTPUT_FILE = PROCESSED_DATA_DIR / "county_analysis_base.parquet"


def main() -> None:

    # -----------------------------------------------------
    # Load datasets
    # -----------------------------------------------------

    print("Loading county geography...")
    geography = gpd.read_parquet(GEOGRAPHY_FILE)

    print("Loading AHRF workforce...")
    workforce = pd.read_parquet(WORKFORCE_FILE)

    print("Loading ACS context...")
    acs = pd.read_parquet(ACS_FILE)

    print("Loading USDA rurality...")
    rurality = pd.read_parquet(RURALITY_FILE)

    print("Loading SAMHSA facilities...")
    facilities = pd.read_parquet(FACILITIES_FILE)

    print(f"\nGeography records: {len(geography):,}")
    print(f"Workforce records: {len(workforce):,}")
    print(f"ACS records: {len(acs):,}")
    print(f"Rurality records: {len(rurality):,}")
    print(f"Facility counties: {len(facilities):,}")

    # -----------------------------------------------------
    # Merge workforce
    # -----------------------------------------------------

    merged = geography.merge(
        workforce,
        on="GEOID",
        how="left",
        validate="one_to_one",
        indicator="workforce_merge",
    )

    print("\nWorkforce merge:")
    print(
        merged["workforce_merge"]
        .value_counts()
        .to_string()
    )

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
    print(
        merged["acs_merge"]
        .value_counts()
        .to_string()
    )

    merged = merged.drop(columns="acs_merge")

    # -----------------------------------------------------
    # Merge rurality
    # -----------------------------------------------------

    merged = merged.merge(
        rurality,
        on="GEOID",
        how="left",
        validate="one_to_one",
        indicator="rurality_merge",
    )

    print("\nRurality merge:")
    print(
        merged["rurality_merge"]
        .value_counts()
        .to_string()
    )

    merged = merged.drop(columns="rurality_merge")

    # -----------------------------------------------------
    # Merge SAMHSA facility records
    # -----------------------------------------------------

    merged = merged.merge(
        facilities,
        on="GEOID",
        how="left",
        validate="one_to_one",
        indicator="facility_merge",
    )

    print("\nFacility merge:")
    print(
        merged["facility_merge"]
        .value_counts()
        .to_string()
    )

    # Counties without matched facility records should
    # represent zero observed matched facility records,
    # rather than missing values.
    facility_count_columns = [
        "facility_records_total",
        "mental_health_facility_records",
        "substance_use_facility_records",
    ]

    for column in facility_count_columns:
        merged[column] = (
            merged[column]
            .fillna(0)
            .astype(int)
        )

    merged = merged.drop(columns="facility_merge")

    # -----------------------------------------------------
    # Derived psychiatrist workforce rates
    # -----------------------------------------------------

    merged["psychiatrists_per_100k_2023"] = (
        merged["psychiatrists_total_2023"]
        / merged["population_2024"]
        * 100_000
    )

    merged[
        "md_patient_care_psychiatrists_per_100k_2023"
    ] = (
        merged["psychiatrists_md_patient_care_2023"]
        / merged["population_2024"]
        * 100_000
    )

    # -----------------------------------------------------
    # Derived facility-record rates
    # -----------------------------------------------------

    merged["facility_records_per_100k"] = (
        merged["facility_records_total"]
        / merged["population_2024"]
        * 100_000
    )

    merged["mental_health_facility_records_per_100k"] = (
        merged["mental_health_facility_records"]
        / merged["population_2024"]
        * 100_000
    )

    merged["substance_use_facility_records_per_100k"] = (
        merged["substance_use_facility_records"]
        / merged["population_2024"]
        * 100_000
    )

    # -----------------------------------------------------
    # Final quality control
    # -----------------------------------------------------

    print("\nFinal quality control:")

    print(
        "Missing population:",
        merged["population_2024"].isna().sum(),
    )

    print(
        "Missing poverty percentage:",
        merged["poverty_pct_2024"].isna().sum(),
    )

    print(
        "Missing uninsured percentage:",
        merged["uninsured_pct_2024"].isna().sum(),
    )

    print(
        "Missing median household income:",
        merged["median_household_income_2024"].isna().sum(),
    )

    print(
        "Missing RUCC:",
        merged["rucc_2023"].isna().sum(),
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

    print(
        "Counties with zero matched facility records:",
        (merged["facility_records_total"] == 0).sum(),
    )

    print(
        "Counties with >=1 matched facility record:",
        (merged["facility_records_total"] > 0).sum(),
    )

    print("\nMetro/nonmetro distribution:")
    print(
        merged["metro_status_2023"]
        .value_counts(dropna=False)
        .to_string()
    )

    # -----------------------------------------------------
    # Structural safeguards
    # -----------------------------------------------------

    assert len(merged) == len(geography)
    assert merged["GEOID"].is_unique

    # -----------------------------------------------------
    # Save integrated analysis base
    # -----------------------------------------------------

    merged.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nFinal analysis-base records: "
        f"{len(merged):,}"
    )

    print(f"Saved: {OUTPUT_FILE}")

    print(
        "Geography + workforce + ACS + rurality + "
        "facility integration completed successfully."
    )


if __name__ == "__main__":
    main()