from pathlib import Path

import geopandas as gpd
import plotly.express as px
import streamlit as st


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "county_analysis_base.parquet"
)


# =========================================================
# Page configuration
# =========================================================

st.set_page_config(
    page_title="Behavioral Health Access Explorer",
    page_icon="🧭",
    layout="wide",
)


# =========================================================
# Load processed analytical data
# =========================================================

@st.cache_data
def load_data() -> gpd.GeoDataFrame:
    """Load the validated county analytical dataset."""
    return gpd.read_parquet(DATA_FILE)


gdf = load_data().copy()


# =========================================================
# Validate required fields
# =========================================================

REQUIRED_COLUMNS = [
    "GEOID",
    "NAMELSAD",
    "STUSPS",
    "STATE_NAME",
    "geometry",
    "population_2024",
    "poverty_pct_2024",
    "uninsured_pct_2024",
    "median_household_income_2024",
    "psychiatrists_total_2023",
    "psychiatrists_md_patient_care_2023",
    "psychiatrists_per_100k_2023",
    "md_patient_care_psychiatrists_per_100k_2023",
    "facility_records_total",
    "facility_records_per_100k",
    "mental_health_facility_records",
    "substance_use_facility_records",
    "metro_status_2023",
    "rucc_2023",
]

missing_columns = [
    column
    for column in REQUIRED_COLUMNS
    if column not in gdf.columns
]

if missing_columns:
    st.error(
        "The processed dataset is missing required columns: "
        + ", ".join(missing_columns)
    )
    st.stop()


# =========================================================
# Create resource profile
# =========================================================

# IMPORTANT:
# Missing psychiatrist data are NOT treated as zero.

psych_available = gdf["psychiatrists_total_2023"].notna()
psych_present = (
    psych_available
    & (gdf["psychiatrists_total_2023"] > 0)
)
psych_zero = (
    psych_available
    & (gdf["psychiatrists_total_2023"] == 0)
)

facility_available = gdf["facility_records_total"].notna()
facility_present = (
    facility_available
    & (gdf["facility_records_total"] > 0)
)
facility_zero = (
    facility_available
    & (gdf["facility_records_total"] == 0)
)

gdf["resource_profile"] = "Neither measured resource"

# Both resources
gdf.loc[
    psych_present & facility_present,
    "resource_profile",
] = "Both measured resources"

# Facilities only
gdf.loc[
    psych_zero & facility_present,
    "resource_profile",
] = "Facilities only"

# Psychiatrists only
gdf.loc[
    psych_present & facility_zero,
    "resource_profile",
] = "Psychiatrists only"

# Neither
gdf.loc[
    psych_zero & facility_zero,
    "resource_profile",
] = "Neither measured resource"

# Missing psychiatrist data
gdf.loc[
    (~psych_available) & facility_present,
    "resource_profile",
] = "Psychiatrist data missing - facilities present"

gdf.loc[
    (~psych_available) & facility_zero,
    "resource_profile",
] = "Psychiatrist data missing - no facilities"


# =========================================================
# Header
# =========================================================

st.title("Behavioral Health Access Explorer")

st.markdown(
    """
    Explore county-level behavioral-health workforce,
    facility infrastructure, rurality, and socioeconomic
    context across the United States.
    """
)

st.caption(
    "Primary geography: 50 states + DC | "
    "Psychiatrist workforce: AHRF 2023 | "
    "Socioeconomic context: 2020–2024 ACS 5-year estimates"
)


# =========================================================
# Sidebar filters
# =========================================================

st.sidebar.header("Filters")

states = sorted(
    gdf["STUSPS"]
    .dropna()
    .unique()
)

selected_state = st.sidebar.selectbox(
    "State",
    ["All states"] + states,
)

if selected_state == "All states":
    filtered = gdf.copy()
else:
    filtered = gdf[
        gdf["STUSPS"] == selected_state
    ].copy()


counties = sorted(
    filtered["NAMELSAD"]
    .dropna()
    .unique()
)

selected_county = st.sidebar.selectbox(
    "County",
    ["All counties"] + counties,
)


if selected_county == "All counties":
    selected = filtered.copy()
else:
    selected = filtered[
        filtered["NAMELSAD"] == selected_county
    ].copy()


# =========================================================
# Overview metrics
# =========================================================

st.subheader("Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Counties in view",
    f"{len(selected):,}",
)

zero_psych_count = (
    selected["psychiatrists_total_2023"]
    .notna()
    & (
        selected["psychiatrists_total_2023"] == 0
    )
).sum()

zero_facility_count = (
    selected["facility_records_total"]
    .notna()
    & (
        selected["facility_records_total"] == 0
    )
).sum()

col2.metric(
    "Zero psychiatrist counties",
    f"{zero_psych_count:,}",
)

col3.metric(
    "Zero facility counties",
    f"{zero_facility_count:,}",
)

population_total = selected[
    "population_2024"
].sum()

col4.metric(
    "Population",
    f"{population_total:,.0f}",
)


# =========================================================
# County-specific profile
# =========================================================

if selected_county != "All counties":

    row = selected.iloc[0]

    st.subheader(
        f"{row['NAMELSAD']}, {row['STATE_NAME']}"
    )

    c1, c2, c3, c4 = st.columns(4)

    psychiatrist_rate = row[
        "psychiatrists_per_100k_2023"
    ]

    facility_rate = row[
        "facility_records_per_100k"
    ]

    if psychiatrist_rate is None:
        psych_display = "Missing"
    elif psychiatrist_rate != psychiatrist_rate:
        # NaN check
        psych_display = "Missing"
    else:
        psych_display = f"{psychiatrist_rate:.2f}"

    if facility_rate is None:
        facility_display = "Missing"
    elif facility_rate != facility_rate:
        facility_display = "Missing"
    else:
        facility_display = f"{facility_rate:.2f}"

    c1.metric(
        "Psychiatrists / 100k",
        psych_display,
    )

    c2.metric(
        "Facility records / 100k",
        facility_display,
    )

    c3.metric(
        "Poverty",
        f"{row['poverty_pct_2024']:.1f}%",
    )

    c4.metric(
        "Uninsured",
        f"{row['uninsured_pct_2024']:.1f}%",
    )

    st.write(
        f"**Population:** {row['population_2024']:,.0f}"
    )

    st.write(
        f"**Rurality / metro status:** "
        f"{row['metro_status_2023']}"
    )

    st.write(
        f"**USDA RUCC:** {row['rucc_2023']}"
    )

    st.write(
        f"**Resource profile:** "
        f"{row['resource_profile']}"
    )


# =========================================================
# Resource profile summary
# =========================================================

st.subheader("Resource Profile")

profile_counts = (
    filtered["resource_profile"]
    .value_counts()
    .rename_axis("Resource Profile")
    .reset_index(name="Counties")
)

profile_counts["Percent of Counties"] = (
    profile_counts["Counties"]
    / len(filtered)
    * 100
)

st.dataframe(
    profile_counts,
    width="stretch",
    hide_index=True,
)


# =========================================================
# Map
# =========================================================

st.subheader("Psychiatrist Supply")

map_data = filtered.copy()

# Remove records with missing psychiatrist rates from
# the color scale while retaining them for table/profile
# information.
map_data["psychiatrist_rate_map"] = (
    map_data["psychiatrists_per_100k_2023"]
)


if selected_state == "All states":

    center_lat = 38.5
    center_lon = -96.5
    zoom_level = 3

else:

    # Approximate state centering based on county geometry.
    projected = map_data.to_crs(
        epsg=5070
    )

    centroid = projected.geometry.union_all().centroid

    center_point = gpd.GeoSeries(
        [centroid],
        crs="EPSG:5070",
    ).to_crs(
        epsg=4326
    ).iloc[0]

    center_lat = center_point.y
    center_lon = center_point.x
    zoom_level = 5.5


fig = px.choropleth_map(
    map_data,
    geojson=map_data.__geo_interface__,
    locations="GEOID",
    featureidkey="properties.GEOID",
    color="psychiatrist_rate_map",
    hover_name="NAMELSAD",
    hover_data={
        "GEOID": True,
        "psychiatrists_per_100k_2023": ":.2f",
        "facility_records_per_100k": ":.2f",
        "facility_records_total": True,
        "resource_profile": True,
        "metro_status_2023": True,
    },
    map_style="carto-positron",
    center={
        "lat": center_lat,
        "lon": center_lon,
    },
    zoom=zoom_level,
    opacity=0.65,
    labels={
        "psychiatrists_per_100k_2023":
            "Psychiatrists per 100k"
    },
)

fig.update_layout(
    height=650,
    margin={
        "l": 0,
        "r": 0,
        "t": 10,
        "b": 0,
    },
)

st.plotly_chart(
    fig,
    width="stretch",
)


# =========================================================
# County data table
# =========================================================

st.subheader("County Data")

display_columns = [
    "STUSPS",
    "NAMELSAD",
    "population_2024",
    "psychiatrists_total_2023",
    "psychiatrists_per_100k_2023",
    "facility_records_total",
    "facility_records_per_100k",
    "poverty_pct_2024",
    "uninsured_pct_2024",
    "median_household_income_2024",
    "metro_status_2023",
    "rucc_2023",
    "resource_profile",
]

display_data = filtered[
    display_columns
].sort_values(
    [
        "STUSPS",
        "NAMELSAD",
    ]
)

st.dataframe(
    display_data,
    width="stretch",
    hide_index=True,
)


# =========================================================
# Research notes
# =========================================================

with st.expander("About this dataset"):

    st.markdown(
        """
        **Geographic universe:** 50 U.S. states + District of Columbia.

        **County geography:** 2024 U.S. Census Cartographic Boundary
        county geography.

        **Psychiatrist workforce:** AHRF 2024–2025 release,
        psychiatrist observations from 2023.

        **Population and socioeconomic context:** 2020–2024
        ACS 5-year estimates.

        **Facility measures:** matched behavioral-health facility
        records incorporated into the county analytical dataset.

        **Important interpretation:** resource measures describe
        recorded county-level resources. They do not directly measure
        appointment availability, travel time, insurance acceptance,
        provider capacity, quality, or realized patient access.
        """
    )