# Uganda Rainfall Variability & Drought Analysis (1990–2025)

An analysis of 36 years of monthly rainfall over Uganda using CHIRPS satellite precipitation data. It covers long-term trends, drought episodes, the two rainy seasons, decadal shifts and ENSO links, first at the national level and then for six regions.

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
│   ├── raw/                     # CHIRPS monthly rainfall exported from Google Earth Engine
│   │   ├── uganda_monthly_rainfall.csv                # national average, 1990–2025
│   │   └── uganda_rainfall_by_region_1990_2025.csv    # 6 regions + national reference
│   └── processed/
│       ├── uganda_rainfall_regional_summary.csv    # per-region stats (written by notebook 02)
│       ├── uganda_rainfall_regional_droughts.csv   # top 3 droughts per region (written by notebook 02)
│       ├── regional_report_summary.csv             # full per-region metrics behind the regional report
│       └── regional_report_droughts.csv            # top 5 droughts per region, as in the report
├── notebooks/
│   ├── 01_national_analysis.ipynb   # Part 1: national trends, droughts, seasons, ENSO
│   └── 02_regional_analysis.ipynb   # Part 2: the same pipeline, per region
├── reports/
│   ├── national_report.html     # standalone write-up of Part 1
│   └── regional_report.html     # standalone write-up of Part 2
└── requirements.txt
```

## Data

- **Source:** [CHIRPS Daily Precipitation](https://www.chc.ucsb.edu/data/chirps) (Climate Hazards Center, UC Santa Barbara), summed to monthly totals and averaged over each boundary in Google Earth Engine.
- **Period:** January 1990 to December 2025, with 432 months per series and no gaps.
- **Regions:**
  - **Karamoja:** FAO GAUL 2015 districts.
  - **Lake Victoria basin:** HydroBASINS level-6 sub-basins, clipped to Uganda.
  - **Central, Eastern, Northern, Western:** geoBoundaries level 1.
- **Masking:** permanent open water (JRC occurrence ≥ 50%) is masked in the regional dataset because CHIRPS is weak over lakes. As a result, the national figures differ slightly between Part 1 and Part 2.

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

Run the notebooks from inside `notebooks/`, because the data paths are relative to that folder. The HTML reports in `reports/` open directly in a browser.

## Limitations

- CHIRPS is a satellite–gauge blend. It is less reliable over open water and complex terrain, and it is not a substitute for station records.
- The four administrative regions stand in for agro-ecological zones.
- The ENSO classification is year-based and coarse. Testing the Indian Ocean Dipole (IOD) index is the obvious next step.
