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

OUTPUT_FILE = PROCESSED_DATA_DIR / "county_analysis_base.parquet"


def main() -> None:

    # -----------------------------------------------------
    # Load processed datasets
    # -----------------------------------------------------

    print("Loading county geography...")
    geography = gpd.read_parquet(GEOGRAPHY_FILE)

    print("Loading AHRF workforce...")
    workforce = pd.read_parquet(WORKFORCE_FILE)

    print("Loading ACS context...")
    acs = pd.read_parquet(ACS_FILE)

    print("Loading USDA rurality...")
    rurality = pd.read_parquet(RURALITY_FILE)

    print(f"\nGeography records: {len(geography):,}")
    print(f"Workforce records: {len(workforce):,}")
    print(f"ACS records: {len(acs):,}")
    print(f"Rurality records: {len(rurality):,}")

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
    print(
        merged["workforce_merge"]
        .value_counts()
        .to_string()
    )

    unmatched_workforce = merged.loc[
        merged["workforce_merge"] != "both",
        ["GEOID", "NAMELSAD", "STUSPS"],
    ]

    print(
        "\nGeography records without workforce match:",
        len(unmatched_workforce),
    )

    if len(unmatched_workforce) > 0:
        print(
            unmatched_workforce.to_string(
                index=False
            )
        )

    merged = merged.drop(
        columns="workforce_merge"
    )

    # -----------------------------------------------------
    # Merge ACS socioeconomic context
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

    unmatched_acs = merged.loc[
        merged["acs_merge"] != "both",
        ["GEOID", "NAMELSAD", "STUSPS"],
    ]

    print(
        "\nGeography records without ACS match:",
        len(unmatched_acs),
    )

    if len(unmatched_acs) > 0:
        print(
            unmatched_acs.to_string(
                index=False
            )
        )

    merged = merged.drop(
        columns="acs_merge"
    )

    # -----------------------------------------------------
    # Merge USDA rurality
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

    unmatched_rurality = merged.loc[
        merged["rurality_merge"] != "both",
        ["GEOID", "NAMELSAD", "STUSPS"],
    ]

    print(
        "\nGeography records without RUCC match:",
        len(unmatched_rurality),
    )

    if len(unmatched_rurality) > 0:
        print(
            unmatched_rurality.to_string(
                index=False
            )
        )

    merged = merged.drop(
        columns="rurality_merge"
    )

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
    # Final quality control
    # -----------------------------------------------------

    print("\nFinal quality control:")

    print(
        "Missing population:",
        merged["population_2024"]
        .isna()
        .sum(),
    )

    print(
        "Missing poverty percentage:",
        merged["poverty_pct_2024"]
        .isna()
        .sum(),
    )

    print(
        "Missing uninsured percentage:",
        merged["uninsured_pct_2024"]
        .isna()
        .sum(),
    )

    print(
        "Missing median household income:",
        merged["median_household_income_2024"]
        .isna()
        .sum(),
    )

    print(
        "Missing RUCC:",
        merged["rucc_2023"]
        .isna()
        .sum(),
    )

    print(
        "Missing total psychiatrist counts:",
        merged["psychiatrists_total_2023"]
        .isna()
        .sum(),
    )

    print(
        "Missing psychiatrist rate:",
        merged["psychiatrists_per_100k_2023"]
        .isna()
        .sum(),
    )

    print(
        "Counties with zero total psychiatrists:",
        (
            merged["psychiatrists_total_2023"] == 0
        ).sum(),
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
        "Geography + workforce + ACS + rurality "
        "integration completed successfully."
    )


if __name__ == "__main__":
    main()