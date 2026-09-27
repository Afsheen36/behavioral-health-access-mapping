from pathlib import Path
import os

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = PROCESSED_DATA_DIR / "county_acs_context.parquet"

API_KEY = os.getenv("CENSUS_API_KEY")

DETAILED_URL = "https://api.census.gov/data/2024/acs/acs5"
SUBJECT_URL = "https://api.census.gov/data/2024/acs/acs5/subject"


DETAILED_VARIABLES = {
    "B01003_001E": "population_2024",
    "B17001_001E": "poverty_universe_2024",
    "B17001_002E": "poverty_below_2024",
    "B19013_001E": "median_household_income_2024",
}

SUBJECT_VARIABLES = {
    "S2701_C05_001E": "uninsured_pct_2024",
}


def get_county_data(url, variables):

    params = {
        "get": "NAME," + ",".join(variables.keys()),
        "for": "county:*",
        "in": "state:*",
        "key": API_KEY,
    }

    response = requests.get(
        url,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(
        data[1:],
        columns=data[0],
    )

    df["GEOID"] = (
        df["state"].astype(str).str.zfill(2)
        + df["county"].astype(str).str.zfill(3)
    )

    df = df.rename(columns=variables)

    for column in variables.values():
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


def main() -> None:

    if not API_KEY:
        raise RuntimeError(
            "CENSUS_API_KEY is not available in the environment."
        )

    print("Requesting 2024 ACS 5-year detailed-table data...")

    detailed = get_county_data(
        DETAILED_URL,
        DETAILED_VARIABLES,
    )

    print("Requesting 2024 ACS 5-year insurance data...")

    insurance = get_county_data(
        SUBJECT_URL,
        SUBJECT_VARIABLES,
    )

    detailed["poverty_pct_2024"] = (
        detailed["poverty_below_2024"]
        / detailed["poverty_universe_2024"]
        * 100
    )

    insurance = insurance[
        [
            "GEOID",
            "uninsured_pct_2024",
        ]
    ].copy()

    acs = detailed.merge(
        insurance,
        on="GEOID",
        how="left",
        validate="one_to_one",
    )

    acs = acs[
        [
            "GEOID",
            "NAME",
            "population_2024",
            "poverty_pct_2024",
            "uninsured_pct_2024",
            "median_household_income_2024",
        ]
    ].copy()

    print(f"\nACS county records: {len(acs):,}")
    print(f"Unique GEOID: {acs['GEOID'].nunique():,}")
    print(
        f"Duplicate GEOID: "
        f"{acs['GEOID'].duplicated().sum():,}"
    )

    print(
        f"Missing population: "
        f"{acs['population_2024'].isna().sum():,}"
    )

    print(
        f"Missing poverty percentage: "
        f"{acs['poverty_pct_2024'].isna().sum():,}"
    )

    print(
        f"Missing uninsured percentage: "
        f"{acs['uninsured_pct_2024'].isna().sum():,}"
    )

    print(
        f"Missing median household income: "
        f"{acs['median_household_income_2024'].isna().sum():,}"
    )

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    acs.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print(f"\nSaved: {OUTPUT_FILE}")
    print(
        "ACS county context dataset created successfully."
    )


if __name__ == "__main__":
    main()