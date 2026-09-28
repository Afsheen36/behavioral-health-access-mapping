# Behavioral Health Access Mapping

## County-Level Behavioral Health Resource Landscape

An interactive, reproducible county-level research project examining geographic variation in behavioral-health workforce, facility infrastructure, rurality, and socioeconomic context across the United States.

**Live application:**  
https://behavioral-health-access-mapping.streamlit.app/

---

## Overview

Behavioral-health resources are not distributed uniformly across U.S. counties. Workforce availability, facility infrastructure, rurality, population size, and socioeconomic conditions vary substantially across geographic areas.

This project builds a reproducible county-level analytical framework for exploring those patterns.

The project integrates multiple public data sources into a common county geography, constructs population-relative resource measures, evaluates national and rural/nonmetropolitan patterns, develops an Arizona case study, and provides an interactive Streamlit application for exploring the resulting dataset.

The analysis focuses on **measured behavioral-health resources and geographic resource patterns**. It does not treat resource presence as equivalent to realized patient access.

---

## Research Question

How do measured behavioral-health workforce and facility resources vary across U.S. counties, and how do those patterns differ by rurality and socioeconomic context?

A secondary case study examines county-level resource patterns within Arizona.

---

## Live Behavioral Health Access Explorer

The deployed application allows users to interactively explore county-level behavioral-health indicators.

**Launch the application:**  
https://behavioral-health-access-mapping.streamlit.app/

The dashboard supports:

- national county-level exploration
- state filtering
- county filtering
- psychiatrist workforce mapping
- behavioral-health facility mapping
- poverty mapping
- uninsured-rate mapping
- median household income mapping
- metropolitan/nonmetropolitan comparison
- county resource profiles
- detailed county indicators
- downloadable filtered data
- methods and interpretation documentation

---

## Analytical Universe

The primary analysis contains:

**3,144 counties and county-equivalent geographic units**

covering the:

- 50 U.S. states
- District of Columbia

Territory records are excluded from the primary analytical universe.

County records are harmonized using five-digit county FIPS identifiers (`GEOID`).

---

## Data Sources

### U.S. Census Bureau

2024 county cartographic boundary geography provides the geographic backbone for the analysis.

County boundaries are harmonized using five-digit county FIPS codes.

### Area Health Resources Files (AHRF)

The HRSA Area Health Resources Files 2024–2025 release provides county-level health workforce information.

The primary workforce indicators used in the application include:

- total psychiatrists
- patient-care psychiatrists
- psychiatrists per 100,000 residents
- patient-care psychiatrists per 100,000 residents

The psychiatrist measures used in this project represent **2023 observations**.

### American Community Survey

The 2020–2024 ACS 5-year estimates provide county-level population and socioeconomic context, including:

- population
- poverty percentage
- uninsured percentage
- median household income

### USDA Rural-Urban Continuum Codes

USDA Rural-Urban Continuum Codes provide county rurality information used to classify counties as:

- Metropolitan
- Nonmetropolitan

The project also retains the underlying RUCC classification.

### Behavioral-Health Facility Data

County-level matched behavioral-health facility records are incorporated to describe facility infrastructure.

Measures include:

- total matched facility records
- mental-health facility records
- substance-use facility records
- facility records per 100,000 residents

Facility records represent measured infrastructure and should not be interpreted as direct measures of treatment capacity.

---

## Data Pipeline

The project was developed as a reproducible analytical pipeline rather than as a single notebook.

```text
2024 Census County Geography
            |
            v
County Geographic Backbone
            |
            +--------------------+
            |                    |
            v                    v
     AHRF Workforce         ACS Context
            |                    |
            +---------+----------+
                      |
                      v
                USDA Rurality
                      |
                      v
        Behavioral-Health Facilities
                      |
                      v
          Integrated County Dataset
                      |
          +-----------+-----------+
          |                       |
          v                       v
   National Analysis       Arizona Case Study
          |                       |
          +-----------+-----------+
                      |
                      v
        Behavioral Health Access Explorer
                      |
                      v
             Streamlit Deployment
```

---

## Core Measures

### Psychiatrist Workforce

The project calculates population-relative psychiatrist supply:

```text
Psychiatrists per 100,000
=
Psychiatrist count / County population × 100,000
```

### Facility Infrastructure

A comparable population-relative facility measure is calculated:

```text
Facility records per 100,000
=
Matched facility records / County population × 100,000
```

### Socioeconomic Context

County context includes:

- poverty percentage
- uninsured percentage
- median household income
- population

### Rurality

Counties are compared using metropolitan/nonmetropolitan status and USDA Rural-Urban Continuum Codes.

---

## Resource Profiles

Counties are classified according to the combination of measured psychiatrist workforce and matched facility records.

### Both measured resources

At least one measured psychiatrist and at least one matched behavioral-health facility record.

### Facilities only

No psychiatrist recorded, but at least one matched behavioral-health facility record.

### Psychiatrists only

At least one psychiatrist recorded, but no matched behavioral-health facility record.

### Neither measured resource

Neither a psychiatrist nor a matched behavioral-health facility record was identified.

Missing psychiatrist observations are retained as missing rather than automatically converted to zero.

---

## Selected National Findings

Across the 3,144-county primary analytical universe:

- **1,663 counties (52.9%)** have zero measured psychiatrists.
- **924 counties (29.4%)** have zero matched behavioral-health facility records.
- **770 counties (24.5%)** have neither measured psychiatrists nor matched facility records.

Resource-profile analysis identified:

- **1,327 counties (42.3%)** with both measured resources
- **893 counties (28.4%)** with facilities only
- **770 counties (24.5%)** with neither measured resource
- **145 counties (4.6%)** with psychiatrists only

A small number of counties contain missing psychiatrist observations and are distinguished from counties reporting zero psychiatrists.

---

## Metropolitan and Nonmetropolitan Patterns

The analysis identified substantial differences between metropolitan and nonmetropolitan counties.

### Metropolitan counties

- Counties: **1,186**
- Population: approximately **288.9 million**
- Median psychiatrists per 100,000: **4.74**
- Mean psychiatrists per 100,000: **8.40**
- Mean poverty percentage: approximately **12.4%**
- Mean uninsured percentage: approximately **8.1%**

### Nonmetropolitan counties

- Counties: **1,958**
- Population: approximately **46.0 million**
- Median psychiatrists per 100,000: **0**
- Mean psychiatrists per 100,000: approximately **2.50**
- Mean poverty percentage: approximately **15.3%**
- Mean uninsured percentage: approximately **9.6%**

These results describe geographic resource patterns and should not be interpreted as causal effects of rurality.

---

## Arizona Case Study

Arizona contains **15 counties** in the analytical dataset.

The Arizona resource profile identified:

- **11 counties (73.3%)** with both measured resources
- **4 counties (26.7%)** with facilities only
- **4 counties** with zero measured psychiatrists
- **0 counties** with zero matched facility records

The four counties classified as facilities only are:

- Graham County
- Greenlee County
- La Paz County
- Santa Cruz County

The Arizona analysis illustrates why workforce and facility infrastructure should be examined separately: facility presence does not necessarily imply local psychiatrist availability.

---

## Interactive Mapping

The Streamlit application supports several county-level map measures:

- psychiatrists per 100,000
- facility records per 100,000
- poverty percentage
- uninsured percentage
- median household income
- metropolitan/nonmetropolitan status

Continuous map scales use a display cap at the 95th percentile to improve visual differentiation among most counties. Hover information retains the underlying county values.

---

## Interpretation

This project distinguishes between:

- workforce supply
- facility infrastructure
- geographic resource availability
- population-relative resource measures
- socioeconomic context
- realized patient access

The presence of a facility does **not** necessarily indicate:

- appointment availability
- treatment capacity
- adequate staffing
- insurance acceptance
- service quality
- short travel distance
- timely care

Similarly, a county with zero measured psychiatrists should not automatically be interpreted as having no psychiatric care available through neighboring counties, telehealth, traveling providers, or other delivery mechanisms.

The results are therefore best interpreted as **descriptive county-level resource patterns**.

---

## Limitations

Important limitations include:

1. The analysis is ecological and county-level.
2. Resource measures do not directly measure individual patient access.
3. Facility records do not necessarily represent treatment capacity.
4. Psychiatrist counts do not measure appointment availability or clinical workload.
5. County boundaries do not represent actual patient travel patterns or service markets.
6. Data sources represent different reporting systems and observation periods.
7. Cross-sectional geographic patterns should not be interpreted as causal relationships.

---

## Project Structure

```text
Behavioral Health Access Mapping/
|
|-- app/
|   `-- streamlit_app.py
|
|-- data/
|   |-- raw/
|   `-- processed/
|       `-- county_analysis_base.parquet
|
|-- docs/
|
|-- results/
|   |-- figures/
|   `-- tables/
|
|-- src/
|   |-- aggregate_facilities.py
|   |-- analyze_access.py
|   |-- analyze_arizona.py
|   |-- analyze_resource_patterns.py
|   |-- build_acs_context.py
|   |-- build_analysis_base.py
|   |-- build_county_backbone.py
|   |-- build_facilities.py
|   |-- build_rurality.py
|   |-- build_workforce.py
|   |-- create_maps.py
|   |-- plot_arizona.py
|   `-- plot_resource_patterns.py
|
|-- .gitignore
|-- README.md
`-- requirements.txt
```

---

## Reproducibility

The deployed dashboard requires:

- Python
- Streamlit
- pandas
- GeoPandas
- Plotly
- PyArrow

Install the application dependencies with:

```bash
pip install -r requirements.txt
```

Run the dashboard locally from the project root with:

```bash
streamlit run app/streamlit_app.py
```

The application reads:

```text
data/processed/county_analysis_base.parquet
```

as its validated analytical dataset.

The raw source files are intentionally excluded from the repository. The `src/` directory documents the data-processing workflow used to construct the analytical dataset.

---

## Technical Skills Demonstrated

This project demonstrates practical experience with:

- Python
- pandas
- GeoPandas
- geospatial data processing
- county FIPS harmonization
- multi-source data integration
- Census API data
- health workforce data
- rurality classification
- population-relative rate construction
- descriptive health-services research
- data validation
- reproducible project architecture
- Git and GitHub
- Plotly interactive visualization
- Streamlit application development
- cloud application deployment
- research interpretation and documentation

---

## Application

**Behavioral Health Access Explorer**

https://behavioral-health-access-mapping.streamlit.app/

---

## Project Status

**Completed and publicly deployed.**

The project includes a reproducible county-level analytical pipeline, national analysis, rurality comparison, Arizona case study, interactive research dashboard, downloadable county data, and public Streamlit deployment.
