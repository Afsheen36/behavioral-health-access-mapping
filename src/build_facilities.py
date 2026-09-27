from pathlib import Path
import io
import time

import pandas as pd
import requests


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

MH_FILE = RAW_DATA_DIR / "National Directory MH 2024_Final.xlsx"
SU_FILE = RAW_DATA_DIR / "National Directory SU 2024_Final.xlsx"

GEOCODE_RESULTS_FILE = (
    PROCESSED_DATA_DIR / "facility_geocoding_results.csv"
)

OUTPUT_FILE = (
    PROCESSED_DATA_DIR / "county_facilities.parquet"
)


# ---------------------------------------------------------
# Census Geocoder settings
# ---------------------------------------------------------

GEOCODER_URL = (
    "https://geocoding.geo.census.gov/"
    "geocoder/geographies/addressbatch"
)

BENCHMARK = "Public_AR_Current"
VINTAGE = "Current_Current"


def load_directory(path: Path, facility_type: str) -> pd.DataFrame:
    """Load the Facilities List worksheet and standardize addresses."""

    df = pd.read_excel(
        path,
        sheet_name="Facilities List",
        dtype=str,
    )

    required = [
        "name1",
        "name2",
        "street1",
        "street2",
        "city",
        "state",
        "zip",
    ]

    missing = [
        column for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{path.name} is missing columns: {missing}"
        )

    out = df[required].copy()

    for column in required:
        out[column] = (
            out[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    out["facility_type"] = facility_type

    out["facility_name"] = (
        out["name1"] + " " + out["name2"]
    ).str.strip()

    out["street_address"] = (
        out["street1"] + " " + out["street2"]
    ).str.strip()

    out["state"] = out["state"].str.upper()

    out["zip"] = (
        out["zip"]
        .str.extract(r"(\d{5})", expand=False)
        .fillna("")
    )

    return out[
        [
            "facility_name",
            "street_address",
            "city",
            "state",
            "zip",
            "facility_type",
        ]
    ].copy()


def load_facilities() -> pd.DataFrame:
    """Load both SAMHSA directories."""

    print("Loading mental-health directory...")
    mh = load_directory(
        MH_FILE,
        "mental_health",
    )

    print("Loading substance-use directory...")
    su = load_directory(
        SU_FILE,
        "substance_use",
    )

    facilities = pd.concat(
        [mh, su],
        ignore_index=True,
    )

    facilities["facility_id"] = (
        facilities.index + 1
    )

    print(
        f"Mental-health facilities: "
        f"{len(mh):,}"
    )

    print(
        f"Substance-use facilities: "
        f"{len(su):,}"
    )

    print(
        f"Combined facility records: "
        f"{len(facilities):,}"
    )

    return facilities


def create_geocoder_input(
    facilities: pd.DataFrame,
) -> pd.DataFrame:
    """Create the Census batch geocoder input."""

    geocode = facilities[
        [
            "facility_id",
            "street_address",
            "city",
            "state",
            "zip",
        ]
    ].copy()

    # Census batch format:
    # Unique ID, Street, City, State, ZIP
    geocode = geocode.rename(
        columns={
            "facility_id": "id",
        }
    )

    return geocode


def geocode_batch(
    batch: pd.DataFrame,
) -> pd.DataFrame:
    """Submit one batch to Census Geocoder."""

    csv_buffer = io.StringIO()

    batch.to_csv(
        csv_buffer,
        index=False,
        header=False,
    )

    files = {
        "addressFile": (
            "addresses.csv",
            csv_buffer.getvalue(),
            "text/csv",
        )
    }

    data = {
        "benchmark": BENCHMARK,
        "vintage": VINTAGE,
    }

    response = requests.post(
        GEOCODER_URL,
        files=files,
        data=data,
        timeout=180,
    )

    response.raise_for_status()

    return pd.read_csv(
        io.StringIO(response.text),
        header=None,
        dtype=str,
    )


def parse_geocoder_results(
    result: pd.DataFrame,
) -> pd.DataFrame:
    """
    Parse Census batch geography response.

    Relevant output fields include:
    input ID, input address,
    match status, match type,
    matched address,
    coordinates,
    state code, county code,
    tract, block.
    """

    if result.empty:
        return pd.DataFrame()

    print(
        f"Geocoder response columns: "
        f"{result.shape[1]}"
    )

    print(
        result.head().to_string(
            index=False,
            header=False,
        )
    )

    return result


def main() -> None:

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    facilities = load_facilities()

    # -----------------------------------------------------
    # Basic address QC
    # -----------------------------------------------------

    facilities["has_street"] = (
        facilities["street_address"].str.len() > 0
    )

    facilities["has_city"] = (
        facilities["city"].str.len() > 0
    )

    facilities["has_state"] = (
        facilities["state"].str.len() > 0
    )

    facilities["has_zip"] = (
        facilities["zip"].str.len() > 0
    )

    print(
        "\nFacilities missing street address:",
        (~facilities["has_street"]).sum(),
    )

    print(
        "Facilities missing city:",
        (~facilities["has_city"]).sum(),
    )

    print(
        "Facilities missing state:",
        (~facilities["has_state"]).sum(),
    )

    print(
        "Facilities missing ZIP:",
        (~facilities["has_zip"]).sum(),
    )

    geocode_input = create_geocoder_input(
        facilities
    )

    # Census currently supports up to 10,000
    # records per batch.
    batch_size = 9000

    all_results = []

    for start in range(
        0,
        len(geocode_input),
        batch_size,
    ):
        end = min(
            start + batch_size,
            len(geocode_input),
        )

        batch = geocode_input.iloc[
            start:end
        ].copy()

        print(
            f"\nGeocoding records "
            f"{start + 1:,}-{end:,}..."
        )

        result = geocode_batch(batch)

        parsed = parse_geocoder_results(
            result
        )

        if not parsed.empty:
            all_results.append(parsed)

        # Give the service a short pause
        time.sleep(1)

    if not all_results:
        raise RuntimeError(
            "No geocoder results were returned."
        )

    geocoded = pd.concat(
        all_results,
        ignore_index=True,
    )

    geocoded.to_csv(
        GEOCODE_RESULTS_FILE,
        index=False,
    )

    print(
        f"\nSaved raw geocoder results: "
        f"{GEOCODE_RESULTS_FILE}"
    )

    print(
        "\nGeocoder processing completed."
    )

    print(
        "We are intentionally stopping here "
        "before county aggregation."
    )


if __name__ == "__main__":
    main()