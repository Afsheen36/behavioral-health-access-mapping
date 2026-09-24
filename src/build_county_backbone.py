from pathlib import Path

import geopandas as gpd


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

COUNTY_ZIP = RAW_DATA_DIR / "cb_2024_us_county_500k.zip"
OUTPUT_FILE = PROCESSED_DATA_DIR / "county_geography.parquet"


# ---------------------------------------------------------
# Analysis universe
# ---------------------------------------------------------

# U.S. territories included in the Census file but excluded
# from the primary 50 states + DC analysis.
EXCLUDED_STATEFP = {"60", "66", "69", "72", "78"}


# ---------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------

def main() -> None:
    """Build and validate the county geographic backbone."""

    print("Loading Census county geography...")

    if not COUNTY_ZIP.exists():
        raise FileNotFoundError(
            f"County geography file not found: {COUNTY_ZIP}"
        )

    gdf = gpd.read_file(COUNTY_ZIP)

    print(f"Full Census geography: {len(gdf):,} records")

    # -----------------------------------------------------
    # Restrict to 50 states + DC
    # -----------------------------------------------------

    county_gdf = gdf[
        ~gdf["STATEFP"].isin(EXCLUDED_STATEFP)
    ].copy()

    print(
        f"Primary analysis universe (50 states + DC): "
        f"{len(county_gdf):,} records"
    )

    print(
        f"Territory records excluded: "
        f"{len(gdf) - len(county_gdf):,}"
    )

    # -----------------------------------------------------
    # Select the core geographic variables
    # -----------------------------------------------------

    county_gdf = county_gdf[
        [
            "GEOID",
            "STATEFP",
            "COUNTYFP",
            "NAME",
            "NAMELSAD",
            "STUSPS",
            "STATE_NAME",
            "geometry",
        ]
    ].copy()

    # -----------------------------------------------------
    # FIPS validation
    # -----------------------------------------------------

    county_gdf["GEOID"] = county_gdf["GEOID"].astype(str)

    assert county_gdf["GEOID"].notna().all()
    assert county_gdf["GEOID"].str.len().eq(5).all()
    assert county_gdf["GEOID"].is_unique

    # -----------------------------------------------------
    # Geometry validation
    # -----------------------------------------------------

    assert county_gdf.geometry.notna().all()
    assert county_gdf.geometry.is_valid.all()

    # -----------------------------------------------------
    # CRS validation
    # -----------------------------------------------------

    assert county_gdf.crs is not None

    print(f"CRS: {county_gdf.crs}")
    print(f"Unique GEOID: {county_gdf['GEOID'].nunique():,}")
    print(f"Invalid geometries: {(~county_gdf.geometry.is_valid).sum()}")
    print(f"Arizona counties: {(county_gdf['STUSPS'] == 'AZ').sum()}")

    # -----------------------------------------------------
    # Create output directory
    # -----------------------------------------------------

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------
    # Write processed geographic backbone
    # -----------------------------------------------------

    county_gdf.to_parquet(OUTPUT_FILE, index=False)

    print(f"Saved: {OUTPUT_FILE}")
    print("County geography backbone created successfully.")


if __name__ == "__main__":
    main()