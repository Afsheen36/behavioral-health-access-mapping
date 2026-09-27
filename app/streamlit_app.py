from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# PROJECT CONFIGURATION
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "county_analysis_base.parquet"
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Behavioral Health Access Explorer",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DATA LOADING
# =========================================================

@st.cache_data
def load_data() -> gpd.GeoDataFrame:
    """Load the validated county-level analytical dataset."""
    return gpd.read_parquet(DATA_FILE)


gdf = load_data().copy()


# =========================================================
# REQUIRED DATA VALIDATION
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
        "The analytical dataset is missing required fields: "
        + ", ".join(missing_columns)
    )
    st.stop()


# =========================================================
# RESOURCE PROFILE CLASSIFICATION
# =========================================================
#
# Important:
# Missing psychiatrist observations are NOT converted to zero.
#
# Zero means the source reports zero.
# Missing means the source does not provide an observation.
# =========================================================

psychiatrist_available = (
    gdf["psychiatrists_total_2023"].notna()
)

psychiatrist_present = (
    psychiatrist_available
    & (gdf["psychiatrists_total_2023"] > 0)
)

psychiatrist_zero = (
    psychiatrist_available
    & (gdf["psychiatrists_total_2023"] == 0)
)

facility_available = (
    gdf["facility_records_total"].notna()
)

facility_present = (
    facility_available
    & (gdf["facility_records_total"] > 0)
)

facility_zero = (
    facility_available
    & (gdf["facility_records_total"] == 0)
)


gdf["resource_profile"] = "Neither measured resource"


# Both measured resources
gdf.loc[
    psychiatrist_present & facility_present,
    "resource_profile",
] = "Both measured resources"


# Facilities only
gdf.loc[
    psychiatrist_zero & facility_present,
    "resource_profile",
] = "Facilities only"


# Psychiatrists only
gdf.loc[
    psychiatrist_present & facility_zero,
    "resource_profile",
] = "Psychiatrists only"


# Neither measured resource
gdf.loc[
    psychiatrist_zero & facility_zero,
    "resource_profile",
] = "Neither measured resource"


# Missing psychiatrist data but facilities present
gdf.loc[
    (~psychiatrist_available) & facility_present,
    "resource_profile",
] = "Psychiatrist data missing - facilities present"


# Missing psychiatrist data and no facilities
gdf.loc[
    (~psychiatrist_available) & facility_zero,
    "resource_profile",
] = "Psychiatrist data missing - no facilities"


# =========================================================
# HEADER
# =========================================================

st.title("Behavioral Health Access Explorer")

st.markdown(
    """
    ### County-Level Behavioral Health Resource Landscape

    Explore geographic variation in psychiatrist workforce,
    behavioral-health facility records, rurality, and socioeconomic
    context across U.S. counties.
    """
)

st.caption(
    "50 states + DC | AHRF psychiatrist workforce: 2023 | "
    "Population and socioeconomic context: 2020–2024 ACS 5-year estimates"
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Explore the data")

states = sorted(
    gdf["STUSPS"]
    .dropna()
    .unique()
    .tolist()
)

selected_state = st.sidebar.selectbox(
    "State",
    ["All states"] + states,
)


# Filter by state
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
    .tolist()
)

selected_county = st.sidebar.selectbox(
    "County",
    ["All counties"] + counties,
)


# Map measures
map_metric_options = {
    "Psychiatrists per 100,000": (
        "psychiatrists_per_100k_2023"
    ),
    "Facility records per 100,000": (
        "facility_records_per_100k"
    ),
    "Poverty percentage": (
        "poverty_pct_2024"
    ),
    "Uninsured percentage": (
        "uninsured_pct_2024"
    ),
    "Median household income": (
        "median_household_income_2024"
    ),
    "Metro / nonmetro status": (
        "metro_status_2023"
    ),
}

selected_metric_label = st.sidebar.selectbox(
    "Map measure",
    list(map_metric_options.keys()),
)

selected_metric = map_metric_options[
    selected_metric_label
]


# =========================================================
# SELECTED COUNTY
# =========================================================

if selected_county == "All counties":

    selected = filtered.copy()

else:

    selected = filtered[
        filtered["NAMELSAD"] == selected_county
    ].copy()


# =========================================================
# OVERVIEW METRICS
# =========================================================

st.subheader("Overview")

m1, m2, m3, m4, m5 = st.columns(5)


county_count = len(selected)

population_total = selected[
    "population_2024"
].sum()


zero_psych_count = (
    selected[
        "psychiatrists_total_2023"
    ].notna()
    & (
        selected[
            "psychiatrists_total_2023"
        ] == 0
    )
).sum()


zero_facility_count = (
    selected[
        "facility_records_total"
    ].notna()
    & (
        selected[
            "facility_records_total"
        ] == 0
    )
).sum()


missing_psych_count = (
    selected[
        "psychiatrists_total_2023"
    ].isna()
).sum()


m1.metric(
    "Counties",
    f"{county_count:,}",
)

m2.metric(
    "Population",
    f"{population_total:,.0f}",
)

m3.metric(
    "Zero psychiatrists",
    f"{zero_psych_count:,}",
)

m4.metric(
    "Zero facilities",
    f"{zero_facility_count:,}",
)

m5.metric(
    "Psychiatrist data missing",
    f"{missing_psych_count:,}",
)


# =========================================================
# SELECTED STATE SNAPSHOT
# =========================================================

if selected_state != "All states":

    state_zero_psych = (
        filtered[
            "psychiatrists_total_2023"
        ].notna()
        & (
            filtered[
                "psychiatrists_total_2023"
            ] == 0
        )
    ).sum()

    state_zero_facilities = (
        filtered[
            "facility_records_total"
        ].notna()
        & (
            filtered[
                "facility_records_total"
            ] == 0
        )
    ).sum()

    state_facilities_only = (
        filtered["resource_profile"]
        == "Facilities only"
    ).sum()

    st.info(
        f"**{filtered['STATE_NAME'].iloc[0]} snapshot:** "
        f"{state_zero_psych} of {len(filtered)} counties have "
        f"zero measured psychiatrists; "
        f"{state_zero_facilities} have zero matched facility records; "
        f"{state_facilities_only} are classified as facilities only."
    )


# =========================================================
# SELECTED COUNTY PROFILE
# =========================================================

if selected_county != "All counties":

    row = selected.iloc[0]

    st.divider()

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

    if pd.isna(psychiatrist_rate):
        psych_display = "Missing"
    else:
        psych_display = f"{psychiatrist_rate:.2f}"

    if pd.isna(facility_rate):
        facility_display = "Missing"
    else:
        facility_display = f"{facility_rate:.2f}"

    c1.metric(
        "Psychiatrists / 100k",
        psych_display,
    )

    c2.metric(
        "Facilities / 100k",
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


    detail_left, detail_right = st.columns(2)


    with detail_left:

        st.write(
            f"**Population:** "
            f"{row['population_2024']:,.0f}"
        )

        income = row[
            "median_household_income_2024"
        ]

        if pd.isna(income):
            st.write(
                "**Median household income:** Missing"
            )
        else:
            st.write(
                f"**Median household income:** "
                f"${income:,.0f}"
            )

        st.write(
            f"**Metro status:** "
            f"{row['metro_status_2023']}"
        )


    with detail_right:

        st.write(
            f"**USDA RUCC:** "
            f"{row['rucc_2023']}"
        )

        st.write(
            f"**Mental-health facility records:** "
            f"{row['mental_health_facility_records']:.0f}"
        )

        st.write(
            f"**Substance-use facility records:** "
            f"{row['substance_use_facility_records']:.0f}"
        )


    st.success(
        f"Resource profile: **{row['resource_profile']}**"
    )


# =========================================================
# RESOURCE PROFILE
# =========================================================

st.divider()

# Define the geographic scope represented by the chart.
if selected_state == "All states":
    profile_scope = "National"
    profile_caption = (
        "Distribution across all counties in the 50 states "
        "and District of Columbia."
    )

else:
    state_name = filtered["STATE_NAME"].iloc[0]
    profile_scope = state_name

    if selected_county == "All counties":
        profile_caption = (
            f"Distribution across all {state_name} counties."
        )
    else:
        profile_caption = (
            f"Distribution across all {state_name} counties; "
            f"selected county: {selected_county}."
        )


st.subheader(
    f"{profile_scope} Resource Profile"
)

st.caption(
    "Classification based on measured psychiatrist workforce "
    "and matched behavioral-health facility records."
)

st.caption(
    profile_caption
)


profile_order = [
    "Both measured resources",
    "Facilities only",
    "Psychiatrists only",
    "Neither measured resource",
    "Psychiatrist data missing - facilities present",
    "Psychiatrist data missing - no facilities",
]


profile_counts = (
    filtered["resource_profile"]
    .value_counts()
    .rename_axis("Resource profile")
    .reset_index(name="Counties")
)


profile_counts["Percent of counties"] = (
    profile_counts["Counties"]
    / len(filtered)
    * 100
)


profile_counts["order"] = (
    profile_counts["Resource profile"]
    .map(
        {
            label: index
            for index, label in enumerate(profile_order)
        }
    )
    .fillna(999)
)


profile_counts = (
    profile_counts
    .sort_values("order")
    .drop(columns="order")
)


profile_fig = px.bar(
    profile_counts,
    x="Counties",
    y="Resource profile",
    orientation="h",
    text="Counties",
    hover_data={
        "Percent of counties": ":.1f",
    },
)


profile_fig.update_layout(
    height=360,
    margin={
        "l": 0,
        "r": 40,
        "t": 20,
        "b": 20,
    },
    xaxis_title="Number of counties",
    yaxis_title=None,
)


profile_fig.update_traces(
    textposition="outside"
)


st.plotly_chart(
    profile_fig,
    width="stretch",
)


with st.expander("What do these profiles mean?"):

    st.markdown(
        """
        **Both measured resources**  
        At least one measured psychiatrist and at least one
        matched behavioral-health facility record.

        **Facilities only**  
        No psychiatrist recorded, but at least one matched
        behavioral-health facility record.

        **Psychiatrists only**  
        At least one psychiatrist recorded, but no matched
        behavioral-health facility record.

        **Neither measured resource**  
        Neither a psychiatrist nor a matched behavioral-health
        facility record was identified.

        **Psychiatrist data missing**  
        The AHRF psychiatrist observation is missing, so the
        county is not treated as having zero psychiatrists.

        These categories describe measured county-level resources;
        they do not directly measure appointment availability,
        travel time, provider capacity, or realized patient access.
        """
    )




# =========================================================
# MAP
# =========================================================

st.divider()

st.subheader(
    f"County Map: {selected_metric_label}"
)

st.caption(
    "Hover over a county to inspect the underlying indicators."
)


map_data = filtered.copy()


# ---------------------------------------------------------
# MAP CENTERING
# ---------------------------------------------------------

if selected_state == "All states":

    center_lat = 38.5
    center_lon = -96.5
    zoom_level = 3

else:

    projected = map_data.to_crs(
        epsg=5070
    )

    geometry_union = (
        projected.geometry.union_all()
    )

    center = geometry_union.centroid

    center_point = gpd.GeoSeries(
        [center],
        crs="EPSG:5070",
    ).to_crs(
        epsg=4326
    ).iloc[0]

    center_lat = center_point.y
    center_lon = center_point.x

    if selected_county != "All counties":
        zoom_level = 7.0
    else:
        zoom_level = 5.3


# ---------------------------------------------------------
# MAP VALUE
# ---------------------------------------------------------

map_data["map_value"] = map_data[
    selected_metric
]


# ---------------------------------------------------------
# NUMERICAL MAP
# ---------------------------------------------------------

if selected_metric != "metro_status_2023":

    numeric_values = pd.to_numeric(
        map_data["map_value"],
        errors="coerce",
    )

    valid_values = numeric_values.dropna()


    if len(valid_values) > 0:

        lower_bound = float(
            max(0, valid_values.min())
        )

        upper_bound = float(
            valid_values.quantile(0.95)
        )

        # Make sure the range remains usable when
        # the data have little variation.
        if upper_bound <= lower_bound:
            upper_bound = float(
                valid_values.max()
            )

        if upper_bound <= lower_bound:
            upper_bound = lower_bound + 1


        fig = px.choropleth_map(
            map_data,
            geojson=map_data.__geo_interface__,
            locations="GEOID",
            featureidkey="properties.GEOID",
            color="map_value",
            hover_name="NAMELSAD",
            hover_data={
                "GEOID": True,
                "map_value": ":.2f",
                "psychiatrists_per_100k_2023": ":.2f",
                "facility_records_per_100k": ":.2f",
                "poverty_pct_2024": ":.1f",
                "uninsured_pct_2024": ":.1f",
                "resource_profile": True,
            },
            color_continuous_scale="Blues",
            range_color=[
                lower_bound,
                upper_bound,
            ],
            map_style="carto-positron",
            center={
                "lat": center_lat,
                "lon": center_lon,
            },
            zoom=zoom_level,
            opacity=0.70,
            labels={
                "map_value": selected_metric_label,
            },
        )

    else:

        fig = px.choropleth_map(
            map_data,
            geojson=map_data.__geo_interface__,
            locations="GEOID",
            featureidkey="properties.GEOID",
            color_discrete_sequence=["#BDBDBD"],
            hover_name="NAMELSAD",
            hover_data={
                "GEOID": True,
                "resource_profile": True,
            },
            map_style="carto-positron",
            center={
                "lat": center_lat,
                "lon": center_lon,
            },
            zoom=zoom_level,
            opacity=0.70,
        )


# ---------------------------------------------------------
# METRO / NONMETRO MAP
# ---------------------------------------------------------

else:

    fig = px.choropleth_map(
        map_data,
        geojson=map_data.__geo_interface__,
        locations="GEOID",
        featureidkey="properties.GEOID",
        color="map_value",
        hover_name="NAMELSAD",
        hover_data={
            "GEOID": True,
            "psychiatrists_per_100k_2023": ":.2f",
            "facility_records_per_100k": ":.2f",
            "resource_profile": True,
        },
        color_discrete_map={
            "Metropolitan": "#4C78A8",
            "Nonmetropolitan": "#F58518",
        },
        map_style="carto-positron",
        center={
            "lat": center_lat,
            "lon": center_lon,
        },
        zoom=zoom_level,
        opacity=0.70,
        labels={
            "map_value": "Metro status",
        },
    )


fig.update_layout(
    height=680,
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


if selected_metric != "metro_status_2023":

    st.caption(
        "The continuous color scale is capped at the 95th percentile "
        "to improve visual differentiation among most counties. "
        "Hover values show the underlying county value."
    )


# =========================================================
# COUNTY DATA TABLE
# =========================================================

st.divider()

st.subheader("County Data")

st.caption(
    "Core indicators for the currently selected geography."
)


display_data = filtered[
    [
        "STUSPS",
        "NAMELSAD",
        "population_2024",
        "psychiatrists_per_100k_2023",
        "facility_records_per_100k",
        "poverty_pct_2024",
        "uninsured_pct_2024",
        "metro_status_2023",
        "resource_profile",
    ]
].copy()


display_data = display_data.rename(
    columns={
        "STUSPS": "State",
        "NAMELSAD": "County",
        "population_2024": "Population",
        "psychiatrists_per_100k_2023":
            "Psychiatrists / 100k",
        "facility_records_per_100k":
            "Facilities / 100k",
        "poverty_pct_2024":
            "Poverty %",
        "uninsured_pct_2024":
            "Uninsured %",
        "metro_status_2023":
            "Metro status",
        "resource_profile":
            "Resource profile",
    }
)


st.dataframe(
    display_data,
    width="stretch",
    hide_index=True,
)


# =========================================================
# DETAILED DATA
# =========================================================

with st.expander("View detailed county variables"):

    detailed_data = filtered[
        [
            "STUSPS",
            "NAMELSAD",
            "population_2024",
            "psychiatrists_total_2023",
            "psychiatrists_md_patient_care_2023",
            "psychiatrists_per_100k_2023",
            "md_patient_care_psychiatrists_per_100k_2023",
            "facility_records_total",
            "facility_records_per_100k",
            "mental_health_facility_records",
            "substance_use_facility_records",
            "poverty_pct_2024",
            "uninsured_pct_2024",
            "median_household_income_2024",
            "metro_status_2023",
            "rucc_2023",
            "resource_profile",
        ]
    ].copy()


    detailed_data = detailed_data.rename(
        columns={
            "STUSPS": "State",
            "NAMELSAD": "County",
            "population_2024": "Population",
            "psychiatrists_total_2023":
                "Psychiatrists (2023)",
            "psychiatrists_md_patient_care_2023":
                "Psychiatrists in patient care (2023)",
            "psychiatrists_per_100k_2023":
                "Psychiatrists / 100k",
            "md_patient_care_psychiatrists_per_100k_2023":
                "Patient-care psychiatrists / 100k",
            "facility_records_total":
                "Facility records",
            "facility_records_per_100k":
                "Facilities / 100k",
            "mental_health_facility_records":
                "Mental-health facility records",
            "substance_use_facility_records":
                "Substance-use facility records",
            "poverty_pct_2024":
                "Poverty %",
            "uninsured_pct_2024":
                "Uninsured %",
            "median_household_income_2024":
                "Median household income",
            "metro_status_2023":
                "Metro status",
            "rucc_2023":
                "USDA RUCC",
            "resource_profile":
                "Resource profile",
        }
    )


    st.dataframe(
        detailed_data,
        width="stretch",
        hide_index=True,
    )


# =========================================================
# DOWNLOAD
# =========================================================

csv_data = detailed_data.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="Download filtered county data (CSV)",
    data=csv_data,
    file_name="behavioral_health_access_filtered.csv",
    mime="text/csv",
)


# =========================================================
# METHODS AND INTERPRETATION
# =========================================================

st.divider()

with st.expander("Methods, definitions, and interpretation"):

    st.markdown(
        """
        ### Geographic universe

        The primary analytical universe contains the 50 U.S. states
        and District of Columbia at the county or county-equivalent
        level.

        ### County geography

        County boundaries come from the 2024 U.S. Census county
        geography backbone used by this project.

        ### Psychiatrist workforce

        Psychiatrist workforce measures come from the AHRF
        2024–2025 release and represent 2023 observations.

        ### Population and socioeconomic context

        Population, poverty, uninsured status, and median household
        income come from the 2020–2024 ACS 5-year estimates.

        ### Facility measures

        Facility measures represent matched behavioral-health facility
        records incorporated into the county analytical dataset.

        ### Rates

        Psychiatrist and facility rates are expressed per 100,000
        residents using the county population denominator.

        ### Zero versus missing

        A reported zero is retained as zero.

        Missing psychiatrist observations are not converted to zero.

        ### Resource profiles

        Resource profiles describe the combination of measured
        psychiatrist workforce and matched facility records.

        ### Interpretation

        These indicators describe county-level measured resources.

        They do not directly measure appointment availability,
        wait times, provider capacity, insurance acceptance, travel
        distance, telehealth availability, treatment intensity,
        quality of care, or realized patient access.

        County-level results are ecological and descriptive and should
        not be interpreted as individual-level measures of access.

        The dashboard is intended for exploratory health-services
        research and visualization rather than clinical decision-making.
        """
    )


# =========================================================
# FOOTER
# =========================================================

st.caption(
    "Behavioral Health Access Mapping | "
    "Reproducible county-level research application"
)