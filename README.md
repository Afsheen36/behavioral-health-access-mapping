\# Behavioral Health Access Mapping



\## Geographic Behavioral Health Access \& Shortage Mapping



This project is a county-level geographic extension of the completed

"Medicaid Behavioral Health Capability" project.



The purpose of this project is to examine geographic variation in

behavioral-health resources across U.S. counties and identify potential

mismatches between available behavioral-health infrastructure and

population need or vulnerability.



\## Research Question



Where are behavioral-health resources geographically mismatched with

population need, particularly among Medicaid-relevant, rural, and

socioeconomically vulnerable populations?



\## Project Objectives



1\. Construct a validated county-level geographic data backbone using

&#x20;  five-digit county FIPS identifiers.

2\. Integrate behavioral-health workforce, facility/infrastructure,

&#x20;  population, socioeconomic, Medicaid-relevant, and rurality measures.

3\. Examine geographic variation and potential resource mismatches.

4\. Develop an Arizona-focused county-level case study.

5\. Build an interactive research dashboard for exploring county-level

&#x20;  behavioral-health patterns.



\## Planned Data Sources



Potential data sources include:



\- Area Health Resources Files (AHRF)

\- U.S. Census American Community Survey (ACS)

\- National Substance Use and Mental Health Services Survey / related

&#x20; behavioral-health facility data

\- CMS Medicaid enrollment and related public data

\- Publicly available county geographic boundary data

\- Rurality classification data



Final source selection will be documented after evaluating county-level

coverage, definitions, comparability, and reproducibility.



\## Planned Methods



The project will use:



\- Python

\- pandas

\- GeoPandas

\- GeoJSON/shapefile geographic data

\- county FIPS harmonization

\- spatial joins

\- descriptive geographic analysis

\- population-relative measures

\- rural/urban comparisons

\- interactive Plotly visualization

\- Streamlit dashboard development



Additional statistical or spatial methods will be selected only after

the county-level analytic dataset has been validated.



\## Interpretation Framework



This project distinguishes among:



\- workforce supply

\- facility infrastructure

\- geographic availability

\- population-relative capacity

\- potential resource mismatch

\- realized patient access



Low measured resource availability will not automatically be described

as a shortage or as evidence of inadequate patient access.



The analysis is observational and county-level. Findings will therefore

be interpreted as geographic associations and patterns rather than causal

effects or direct measures of individual patient access.



\## Planned Output



The primary portfolio product will be an interactive web application:



\*\*Behavioral Health Access Explorer\*\*



The application is planned to include:



\- National county explorer

\- Arizona deep dive

\- County comparison tools

\- Methods and data documentation



\## Project Structure



```text

Behavioral Health Access Mapping/

├── app/

├── data/

│   ├── raw/

│   └── processed/

├── docs/

├── results/

│   ├── figures/

│   └── tables/

├── src/

├── .gitignore

└── README.md

