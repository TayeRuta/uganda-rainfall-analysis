# Uganda Rainfall Variability & Drought Analysis (1990–2025)

An analysis of 36 years of monthly rainfall over Uganda using CHIRPS satellite precipitation data. It covers long-term trends, drought episodes, the two rainy seasons, decadal shifts and ENSO links, first at the national level and then for six regions.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/regional_trends_dark.png">
  <img alt="Annual rainfall 1990–2025 with linear trends: Eastern region +7.2 mm/yr (p = 0.008), Karamoja +6.7 mm/yr (p = 0.008), Uganda national +2.3 mm/yr (not significant)" src="figures/regional_trends_light.png">
</picture>

**Read the reports:** [National report (1990–2025)](https://tayeruta.github.io/uganda-rainfall-analysis/reports/national_report.html) · [Regional report](https://tayeruta.github.io/uganda-rainfall-analysis/reports/regional_report.html)

## Key findings

**National (Part 1)**

- **No significant long-term trend** in annual rainfall (linear p = 0.14; the Kendall test agrees). The gap between the driest year (2009) and the wettest (2020) is about 500 mm, roughly 40% of an average year.
- **2009 was the worst drought on record.** On a 3-month (SPI-3) basis it lasted 8 consecutive months (April–November) and fell to −2.47σ.
- **The short rains (Sep–Nov) are trending upward**, while the long rains (Mar–May), which matter most for planting, show no trend but more year-to-year volatility.
- **Rainfall has become more erratic.** Monthly variability (CV) rose about 12% from the 1990s to the 2010s.
- **ENSO shows no significant effect** on short-rains totals at the national scale (p = 0.80).

**Regional (Part 2)**

- **The flat national trend hides a regional split.** Karamoja (+6.7 mm/yr, p = 0.008) and the Eastern region (+7.2 mm/yr, p = 0.008) are getting significantly wetter. The other regions show no significant trend.
- **The wetting comes from the short rains.** Karamoja's Sep–Nov trend (+3.5 mm/yr, p = 0.0015) is the strongest result in the project.
- **Karamoja is the driest and most volatile region.** It averages 917 mm a year, and its annual totals vary about twice as much as the national average.
- **The 2009 drought hit the north hardest.** It ran 9 months in the Northern region, the longest regional drought since 1990.
- **ENSO still shows no effect at the regional scale.** The Indian Ocean Dipole is the more likely driver and the natural next test.

| Region | Mean annual (mm) | Annual CV | Trend (mm/yr) | Trend p |
|---|---:|---:|---:|---:|
| Eastern | 1,431 | 12.1% | +7.2 | 0.008 |
| Central | 1,209 | 9.2% | +2.2 | 0.22 |
| Northern | 1,160 | 10.7% | +1.4 | 0.50 |
| Western | 1,141 | 7.4% | +1.3 | 0.36 |
| Lake Victoria basin | 1,101 | 8.9% | +2.3 | 0.15 |
| Karamoja | 917 | 17.5% | +6.7 | 0.008 |
| **Uganda (national)** | **1,203** | **8.8%** | **+2.3** | **0.18** |

## Repository structure

```
.
├── data/
│   ├── raw/                                        # exported from Google Earth Engine
│   │   ├── uganda_monthly_rainfall.csv             # national average, 1990–2025
│   │   └── uganda_rainfall_by_region_1990_2025.csv # 6 regions + national reference
│   └── processed/
│       ├── regional_summary.csv                    # every metric per region (pipeline)
│       ├── regional_droughts.csv                   # top 5 SPI-3 droughts per region (pipeline)
│       ├── regional_results.json                   # full results + monthly series behind the regional report
│       ├── uganda_rainfall_regional_summary.csv    # headline stats per region (notebook 02)
│       └── uganda_rainfall_regional_droughts.csv   # top 3 droughts per region (notebook 02)
├── notebooks/
│   ├── 01_national_analysis.ipynb   # Part 1: national trends, droughts, seasons, ENSO
│   └── 02_regional_analysis.ipynb   # Part 2: the same analysis, per region
├── figures/                         # README figure (light and dark versions)
├── reports/
│   ├── national_report.html         # standalone write-up of Part 1
│   └── regional_report.html         # standalone write-up of Part 2
├── scripts/
│   ├── gee/
│   │   ├── uganda_national_rainfall_gee.js   # Earth Engine export → data/raw/uganda_monthly_rainfall.csv
│   │   └── uganda_regional_rainfall_gee.js   # Earth Engine export → data/raw/uganda_rainfall_by_region_1990_2025.csv
│   ├── regional_pipeline.py         # regional analysis as a script → data/processed/regional_*
│   └── make_readme_figure.py        # builds the figures/ chart from regional_results.json
├── LICENSE
└── requirements.txt
```

## Workflow

1. **Export:** run the scripts in `scripts/gee/` in the [Earth Engine Code Editor](https://code.earthengine.google.com/) and start the export from the Tasks tab. Each one writes a CSV to Google Drive, which goes in `data/raw/`.
2. **Analyse:** the notebooks in `notebooks/` contain the full analysis with a written finding after each step. `scripts/regional_pipeline.py` runs the regional analysis non-interactively and writes the tables and JSON in `data/processed/`.
3. **Report:** the HTML pages in `reports/` present the results.

## Data

- **Period:** January 1990 to December 2025, with 432 months per series and no gaps.
- **Processing:** daily CHIRPS rainfall is summed to monthly totals, then averaged over each boundary at CHIRPS's native ~5.5 km resolution.
- **Masking:** permanent open water (JRC occurrence ≥ 50%) is masked in the regional dataset because CHIRPS is weak over lakes. As a result, the national figures differ slightly between Part 1 and Part 2. Set `MASK_WATER = true` in the national script to match.

### Data sources

The CSVs in this repo are derived rainfall statistics. No boundary files or raw imagery are redistributed. All datasets were accessed through the Google Earth Engine data catalog.

| Dataset | Used for | Provider | Terms |
|---|---|---|---|
| [CHIRPS Daily v2.0](https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY) | Rainfall | Climate Hazards Center, UC Santa Barbara | Public domain (CC0) |
| [FAO GAUL 2015](https://developers.google.com/earth-engine/datasets/catalog/FAO_GAUL_2015_level1) | Uganda boundary, Karamoja districts | UN FAO | Non-commercial use |
| [geoBoundaries ADM1](https://www.geoboundaries.org/) | Central, Eastern, Northern, Western regions | William & Mary geoLab | Open license, attribution required |
| [HydroSHEDS / HydroBASINS](https://www.hydrosheds.org/) | Lake Victoria basin | WWF | Free use with attribution |
| [JRC Global Surface Water](https://global-surface-water.appspot.com/) | Open-water mask | European Commission JRC | Free use with attribution |

**Citations**

- Funk, C. et al. (2015). The climate hazards infrared precipitation with stations — a new environmental record for monitoring extremes. *Scientific Data* 2, 150066.
- Runfola, D. et al. (2020). geoBoundaries: A global database of political administrative boundaries. *PLoS ONE* 15(4), e0231866.
- Lehner, B. & Grill, G. (2013). Global river hydrography and network routing: baseline data and new approaches to study the world's large river systems. *Hydrological Processes* 27(15), 2171–2186.
- Pekel, J.-F. et al. (2016). High-resolution mapping of global surface water and its long-term changes. *Nature* 540, 418–422.

## Methods

- **Trend tests:** OLS linear regression on annual and seasonal totals, checked with the Mann-Kendall (Kendall's tau) test.
- **Droughts:**
  - Standardized monthly anomalies.
  - An SPI-3 approximation (rolling 3-month standardized deficit) to measure how long droughts last.
- **Seasonality and change over time:**
  - Monthly climatology.
  - Comparison of the long rains (MAM) and short rains (SON).
  - Decadal means and coefficient of variation.
  - Trend/seasonal/residual decomposition.
- **Teleconnections:** comparison of El Niño, La Niña and neutral years.
- **Persistence:** autocorrelation of monthly anomalies.
- **Multiple testing:** about 35 tests were run in Part 2, so results near p ≈ 0.04 are treated as suggestive. The key results are checked against a Bonferroni threshold.

## Reproducing the analysis

```bash
git clone https://github.com/TayeRuta/uganda-rainfall-analysis.git
cd uganda-rainfall-analysis
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook notebooks/
```

Run the notebooks from inside `notebooks/`, because the data paths are relative to that folder. The pipeline script can be run from anywhere:

```bash
python scripts/regional_pipeline.py
```

The HTML reports in `reports/` open directly in a browser, or online via the links at the top.

## Limitations

- CHIRPS is a satellite–gauge blend. It is less reliable over open water and complex terrain, and it is not a substitute for station records.
- The four administrative regions stand in for agro-ecological zones.
- The ENSO classification is year-based and coarse. Testing the Indian Ocean Dipole (IOD) index is the obvious next step.

## License

The code and analysis in this repository are released under the [MIT License](LICENSE). The source datasets keep their own terms (see [Data sources](#data-sources)).
