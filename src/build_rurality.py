from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

RUCC_FILE = RAW_DATA_DIR / "Ruralurbancontinuumcodes2023.csv"
OUTPUT_FILE = PROCESSED_DATA_DIR / "county_rurality.parquet"


def main() -> None:

    print("Loading 2023 USDA Rural-Urban Continuum Codes...")

    raw = pd.read_csv(
        RUCC_FILE,
        dtype=str,
        encoding="cp1252",
    )

    print(f"Raw long-format records: {len(raw):,}")

    # -----------------------------------------------------
    # Select the 2023 RUCC observations
    # -----------------------------------------------------

    rurality = raw.loc[
        raw["Attribute"] == "RUCC_2023",
        [
            "FIPS",
            "State",
            "County_Name",
            "Value",
        ],
    ].copy()

    rurality = rurality.rename(
        columns={
            "State": "state_name_rucc",
            "County_Name": "county_name_rucc",
            "Value": "rucc_2023",
        }
    )

    # Standardize county FIPS
    rurality["GEOID"] = (
        rurality["FIPS"]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    rurality["rucc_2023"] = pd.to_numeric(
        rurality["rucc_2023"],
        errors="coerce",
    )

    # -----------------------------------------------------
    # Derive metro/nonmetro classification
    #
    # USDA RUCC:
    # 1-3 = metropolitan
    # 4-9 = nonmetropolitan
    # -----------------------------------------------------

    rurality["metro_status_2023"] = rurality[
        "rucc_2023"
    ].apply(
        lambda x: (
            "Metropolitan"
            if pd.notna(x) and 1 <= x <= 3
            else (
                "Nonmetropolitan"
                if pd.notna(x) and 4 <= x <= 9
                else pd.NA
            )
        )
    )

    rurality["nonmetro_2023"] = rurality[
        "rucc_2023"
    ].apply(
        lambda x: (
            0
            if pd.notna(x) and 1 <= x <= 3
            else (
                1
                if pd.notna(x) and 4 <= x <= 9
                else pd.NA
            )
        )
    )

    rurality = rurality[
        [
            "GEOID",
            "state_name_rucc",
            "county_name_rucc",
            "rucc_2023",
            "metro_status_2023",
            "nonmetro_2023",
        ]
    ].copy()

    # -----------------------------------------------------
    # Quality control
    # -----------------------------------------------------

    print(f"RUCC county records: {len(rurality):,}")
    print(f"Unique GEOID: {rurality['GEOID'].nunique():,}")
    print(
        "Duplicate GEOID:",
        rurality["GEOID"].duplicated().sum(),
    )
    print(
        "Missing RUCC:",
        rurality["rucc_2023"].isna().sum(),
    )

    print("\nRUCC distribution:")
    print(
        rurality["rucc_2023"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nMetro/nonmetro distribution:")
    print(
        rurality["metro_status_2023"]
        .value_counts(dropna=False)
        .to_string()
    )

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    rurality.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print(f"\nSaved: {OUTPUT_FILE}")
    print("County rurality dataset created successfully.")


if __name__ == "__main__":
    main()