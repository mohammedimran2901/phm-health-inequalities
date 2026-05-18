# PHM Health Inequalities Dashboard

A web-based Population Health Management (PHM) Tool focused on Health Inequalities in England, using 100% open-source, publicly available UK government and NHS data.

## Overview

This tool visualizes health inequalities across England by combining:
- **Index of Multiple Deprivation (IMD) 2019** - Official measure of relative deprivation
- **OHID Fingertips API** - Public health indicators from the Office for Health Improvement and Disparities
- **Core20PLUS5 Framework** - NHS strategy targeting the most deprived 20% of areas and 5 key clinical areas

## Project Structure

```
phm-health-inequalities/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── data/                          # Data storage (gitignored)
│   ├── raw/                       # Downloaded source data
│   ├── processed/                 # Cleaned/transformed data
│   └── db/                        # DuckDB database files
├── src/                           # Source code
│   ├── data_acquisition/          # Data fetching modules
│   │   ├── data_fetch.py          # Main orchestration script
│   │   ├── fingertips_api.py      # OHID Fingertips API client
│   │   └── imd_fetcher.py         # IMD 2019 data fetcher
│   ├── database/                  # Database management
│   ├── analytics/                 # Analytical engine
│   └── dashboard/                 # Streamlit application
├── notebooks/                     # Jupyter notebooks
├── tests/                         # Unit tests
└── docs/                          # Documentation
```

## Quick Start

### 1. Setup Environment

```bash
# Navigate to project directory
cd phm-health-inequalities

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Test Data Connections

```bash
# Test API connections without downloading data
python src/data_acquisition/data_fetch.py --test
```

Expected output:
```
============================================================
DATA FETCH STATUS REPORT
============================================================

FINGERTIPS_API:
  ✓ Success
    - area_types_count: 44
    - sample_areas: [{'Id': 3, 'Name': 'Middle Super Output Area'}, ...]

IMD_GOV_UK:
  ✓ Success
    - status_code: 200
    - content_length: 1433347

ALL_CONNECTED: True
```

### 3. Download Data

```bash
# Fetch all data sources
python src/data_acquisition/data_fetch.py --fetch-all

# Or fetch specific datasets
python src/data_acquisition/data_fetch.py --fetch-imd
python src/data_acquisition/data_fetch.py --fetch-fingertips
```

### 4. Verify Data

```bash
# Test the IMD fetcher directly
python src/data_acquisition/imd_fetcher.py
```

## Data Sources

### 1. Index of Multiple Deprivation (IMD) 2019

- **Source**: Ministry of Housing, Communities & Local Government (MHCLG)
- **URL**: https://opendatacommunities.org/resource/imd-2019
- **Coverage**: 32,844 LSOAs (Lower Layer Super Output Areas) in England
- **Metrics**:
  - Overall IMD Rank, Score, Decile, Quintile
  - 7 Domain scores: Income, Employment, Education, Health, Crime, Housing, Living Environment

### 2. OHID Fingertips API

- **Source**: Office for Health Improvement and Disparities
- **URL**: https://fingertips.phe.org.uk/api
- **Indicators Available**:
  - Life Expectancy (male, female, at birth)
  - Smoking Prevalence
  - Cardiovascular Disease Prevalence
  - Hypertension Prevalence
  - Cancer Emergency Presentations
  - Severe Mental Illness
  - COPD Prevalence
  - Maternity Early Access
  - And many more...

### 3. Geographic Hierarchy

- **LSOA (Lower Layer Super Output Area)**: ~1,500 residents
- **LAD (Local Authority District)**: Council boundaries
- **ICB (Integrated Care Board)**: NHS organisational boundaries
- **Region**: NHS England regions

## Core20PLUS5 Framework

The tool implements the NHS Core20PLUS5 framework:

**Core 20**: The most deprived 20% of areas (IMD Quintile 1)
- Identified automatically from IMD 2019 data
- ~6,569 LSOAs in England

**PLUS**: Additional inclusion criteria (configurable)
- People with learning disabilities
- Care home residents
- Gypsy, Roma, Traveller communities

**5 Clinical Areas**:
1. **Maternity**: Early access to maternity services
2. **Severe Mental Illness**: SMI mortality
3. **Chronic Respiratory**: COPD prevalence
4. **Early Cancer Diagnosis**: Emergency cancer presentations
5. **Hypertension**: QOF achievement rates

## Key Indicators

| Indicator | Fingertips ID | Description |
|-----------|--------------|-------------|
| life_expectancy_birth | 93505 | Life expectancy at birth (persons) |
| smoking_prevalence | 92443 | Smoking prevalence in adults |
| hypertension_prevalence | 241 | Hypertension prevalence (QOF) |
| cancer_emergency_presentations | 91156 | Emergency cancer presentations |
| severe_mental_illness | 93095 | Severe mental illness prevalence |
| copd_prevalence | 250 | COPD prevalence (QOF) |
| maternity_early_access | 93741 | Early access to maternity services |

## Usage Examples

### Fetch IMD Data

```python
from src.data_acquisition.imd_fetcher import IMDFetcher

fetcher = IMDFetcher()
df = fetcher.get_combined_imd_data()

print(f"Total LSOAs: {len(df)}")
print(f"Core 20% most deprived: {len(df[df['imd_quintile'] == 1])}")
```

### Fetch Health Indicators

```python
from src.data_acquisition.fingertips_api import FingertipsAPI

api = FingertipsAPI()

# Get life expectancy data for all Local Authorities
df = api.get_data_for_indicator(
    indicator_id=93505,  # Life expectancy at birth
    area_type_id=7       # LTLA (Lower Tier Local Authority)
)

print(f"Retrieved {len(df)} records")
print(df[['AreaName', 'Time period', 'Value']].head())
```

### Get Core 20% Areas

```python
from src.data_acquisition.imd_fetcher import IMDFetcher

fetcher = IMDFetcher()
core20 = fetcher.get_core20_areas()

print(f"Core 20% areas: {len(core20)} LSOAs")
print(core20[['lsoa11nm', 'lad19nm', 'imd_rank']].head())
```

## Dashboard Features (Planned)

### Screen 1: Geographic Map
- Choropleth visualization of England
- Zoom levels: Region → ICB → Local Authority → LSOA
- Layer toggles: IMD score, Life Expectancy, Smoking prevalence, etc.
- Interactive click for detailed metrics

### Screen 2: Inequality Gap Analysis
- Slope Index of Inequality (SII) visualization
- Quintile comparison charts (Q1 vs Q5)
- Time series of inequality trends
- Downloadable charts and data

### Screen 3: Core20PLUS5 Tracker
- Local Authority/ICB selector
- Performance scorecard vs national baseline
- Traffic light indicators (Red/Amber/Green)
- Benchmarking against similar areas

## Technology Stack

- **Backend/Data**: Python 3.12+
- **Data Processing**: Pandas, GeoPandas, DuckDB
- **APIs**: Requests for REST API consumption
- **Dashboard**: Streamlit (rapid prototyping)
- **Mapping**: Folium, PyDeck
- **Visualization**: Plotly, Matplotlib, Seaborn

## Data Schema

### IMD 2019 Table

| Column | Type | Description |
|--------|------|-------------|
| lsoa11cd | VARCHAR(9) | LSOA 2011 code |
| lsoa11nm | VARCHAR(100) | LSOA name |
| lad19cd | VARCHAR(9) | Local Authority code |
| lad19nm | VARCHAR(100) | Local Authority name |
| imd_rank | INTEGER | IMD rank (1 = most deprived) |
| imd_quintile | INTEGER | Deprivation quintile (1-5) |
| imd_score | DECIMAL | IMD score |
| income_score | DECIMAL | Income domain score |
| employment_score | DECIMAL | Employment domain score |
| health_score | DECIMAL | Health domain score |
| ... | ... | Other domain scores |

### Health Indicators Table

| Column | Type | Description |
|--------|------|-------------|
| indicator_id | VARCHAR(50) | Fingertips indicator ID |
| indicator_name | VARCHAR(200) | Indicator name |
| area_code | VARCHAR(9) | Geographic area code |
| area_name | VARCHAR(100) | Area name |
| time_period | VARCHAR(20) | Data time period |
| value | DECIMAL | Indicator value |
| lower_ci | DECIMAL | 95% CI lower bound |
| upper_ci | DECIMAL | 95% CI upper bound |

## Accessibility

The dashboard follows WCAG 2.1 AA guidelines:
- Colorblind-safe color palettes (Viridis/Plasma)
- Minimum 4.5:1 contrast ratios
- Alt text for all charts
- Keyboard navigation support
- Screen reader compatible

## Next Steps

1. **Complete Dashboard**: Build Streamlit interface with 3 screens
2. **Add Analytics**: Implement Slope Index of Inequality calculations
3. **Geographic Data**: Add LSOA boundary GeoJSON for mapping
4. **Database**: Set up DuckDB for efficient querying
5. **Testing**: Add unit tests for data acquisition
6. **Documentation**: Add API reference and data dictionary

## License

This project uses open data from:
- UK Government (Open Government Licence v3.0)
- NHS England (Open Government Licence v3.0)

## Contributing

Contributions welcome! Please follow PEP 8 style guidelines and add tests for new features.

## Contact

For questions or issues, please open a GitHub issue.

---

**Built with open data for public health improvement**