from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

FACILITY_GEOCODE_FILE = (
    PROCESSED_DATA_DIR / "facility_geocoding_results.csv"
)

OUTPUT_FILE = (
    PROCESSED_DATA_DIR / "county_facilities.parquet"
)


def main() -> None:

    print("Loading SAMHSA facility records...")

    # Recreate the facility metadata so we retain
    # mental-health vs substance-use classification.
    from build_facilities import load_facilities

    facilities = load_facilities()

    print(
        f"Facility records loaded: "
        f"{len(facilities):,}"
    )

    print("Loading Census geocoder results...")

    geo = pd.read_csv(
        FACILITY_GEOCODE_FILE,
        dtype=str,
        header=None,
    )

    # Census batch geocoder response format:
    # 0 = input ID
    # 1 = input address
    # 2 = match status
    # 3 = match type
    # 4 = matched address
    # 5 = coordinates
    # 6 = tigerline ID
    # 7 = side
    # 8 = state FIPS
    # 9 = county FIPS
    # 10 = tract
    # 11 = block

    geo = geo.iloc[:, :12].copy()

    geo.columns = [
        "facility_id",
        "input_address",
        "match_status",
        "match_type",
        "matched_address",
        "coordinates",
        "tigerline_id",
        "side",
        "state_fips",
        "county_fips",
        "tract",
        "block",
    ]

    # -----------------------------------------------------
    # Match QC
    # -----------------------------------------------------

    print("\nGeocoder match status:")
    print(
        geo["match_status"]
        .value_counts(dropna=False)
        .to_string()
    )

    # Keep only confident Census matches.
    matched = geo.loc[
        geo["match_status"] == "Match"
    ].copy()

    print(
        f"\nConfident matches retained: "
        f"{len(matched):,}"
    )

    # -----------------------------------------------------
    # Create five-digit county GEOID
    # -----------------------------------------------------

    matched["GEOID"] = (
        matched["state_fips"]
        .astype(str)
        .str.zfill(2)
        +
        matched["county_fips"]
        .astype(str)
        .str.zfill(3)
    )

    # -----------------------------------------------------
    # Connect geocoder results to facility type
    # -----------------------------------------------------

    facilities["facility_id"] = (
        facilities["facility_id"]
        .astype(str)
    )

    matched["facility_id"] = (
        matched["facility_id"]
        .astype(str)
    )

    matched = matched.merge(
        facilities[
            [
                "facility_id",
                "facility_type",
            ]
        ],
        on="facility_id",
        how="left",
        validate="one_to_one",
    )

    print(
        "\nMissing facility type after merge:",
        matched["facility_type"].isna().sum(),
    )

    # -----------------------------------------------------
    # Aggregate facility records by county
    # -----------------------------------------------------

    county_total = (
        matched
        .groupby("GEOID")
        .size()
        .rename("facility_records_total")
    )

    county_mh = (
        matched.loc[
            matched["facility_type"]
            == "mental_health"
        ]
        .groupby("GEOID")
        .size()
        .rename("mental_health_facility_records")
    )

    county_su = (
        matched.loc[
            matched["facility_type"]
            == "substance_use"
        ]
        .groupby("GEOID")
        .size()
        .rename("substance_use_facility_records")
    )

    county_facilities = pd.concat(
        [
            county_total,
            county_mh,
            county_su,
        ],
        axis=1,
    ).fillna(0)

    county_facilities = (
        county_facilities
        .reset_index()
    )

    # Convert counts back to integers.
    count_columns = [
        "facility_records_total",
        "mental_health_facility_records",
        "substance_use_facility_records",
    ]

    for column in count_columns:
        county_facilities[column] = (
            county_facilities[column]
            .astype(int)
        )

    # -----------------------------------------------------
    # QC
    # -----------------------------------------------------

    print(
        f"\nCounties represented by matched facilities: "
        f"{len(county_facilities):,}"
    )

    print(
        "Unique county GEOID:",
        county_facilities["GEOID"].nunique(),
    )

    print(
        "Duplicate county GEOID:",
        county_facilities["GEOID"]
        .duplicated()
        .sum(),
    )

    print(
        "\nTotal matched facility records:",
        matched.shape[0],
    )

    print(
        "Total aggregated facility records:",
        county_facilities[
            "facility_records_total"
        ].sum(),
    )

    print(
        "\nFacility record totals by type:"
    )

    print(
        matched["facility_type"]
        .value_counts()
        .to_string()
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    county_facilities.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nSaved: {OUTPUT_FILE}"
    )

    print(
        "County facility dataset created successfully."
    )


if __name__ == "__main__":
    main()