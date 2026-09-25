from pathlib import Path
import zipfile

import pandas as pd


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

AHRF_ZIP = RAW_DATA_DIR / "AHRF_2024-2025_CSV.zip"

AHRF_HP_FILE = (
    "NCHWA-2024-2025+AHRF+COUNTY+CSV/"
    "AHRF2025hp.csv"
)

OUTPUT_FILE = PROCESSED_DATA_DIR / "county_workforce.parquet"


# ---------------------------------------------------------
# Variables selected from AHRF documentation
# ---------------------------------------------------------

USECOLS = [
    "fips_st_cnty",
    "cnty_name_st_abbrev",
    "tot_md_do_psych_23",
    "md_nf_psych_all_pc_23",
]


def main() -> None:

    print("Loading AHRF health-professions data...")

    with zipfile.ZipFile(AHRF_ZIP) as zf:
        workforce = pd.read_csv(
            zf.open(AHRF_HP_FILE),
            usecols=USECOLS,
            dtype={"fips_st_cnty": str},
        )

    # Standardize county identifier
    workforce["GEOID"] = (
        workforce["fips_st_cnty"]
        .astype(str)
        .str.zfill(5)
    )

    # Rename variables to analysis-friendly names
    workforce = workforce.rename(
        columns={
            "cnty_name_st_abbrev": "county_name_ahrf",
            "tot_md_do_psych_23": "psychiatrists_total_2023",
            "md_nf_psych_all_pc_23":
                "psychiatrists_md_patient_care_2023",
        }
    )

    workforce = workforce[
        [
            "GEOID",
            "county_name_ahrf",
            "psychiatrists_total_2023",
            "psychiatrists_md_patient_care_2023",
        ]
    ].copy()

    # Convert workforce measures to numeric
    numeric_columns = [
        "psychiatrists_total_2023",
        "psychiatrists_md_patient_care_2023",
    ]

    for column in numeric_columns:
        workforce[column] = pd.to_numeric(
            workforce[column],
            errors="coerce",
        )

    # -----------------------------------------------------
    # Quality control
    # -----------------------------------------------------

    print(f"AHRF county records: {len(workforce):,}")
    print(f"Unique GEOID: {workforce['GEOID'].nunique():,}")
    print(f"Duplicate GEOID: {workforce['GEOID'].duplicated().sum():,}")
    print(f"Missing GEOID: {workforce['GEOID'].isna().sum():,}")

    print(
        "Missing total psychiatrist counts:",
        workforce["psychiatrists_total_2023"].isna().sum(),
    )

    print(
        "Missing MD patient-care psychiatrist counts:",
        workforce[
            "psychiatrists_md_patient_care_2023"
        ].isna().sum(),
    )

    print(
        "Counties with zero total psychiatrists:",
        (workforce["psychiatrists_total_2023"] == 0).sum(),
    )

    # -----------------------------------------------------
    # Save processed workforce dataset
    # -----------------------------------------------------

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    workforce.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print(f"Saved: {OUTPUT_FILE}")
    print("County workforce dataset created successfully.")


if __name__ == "__main__":
    main()