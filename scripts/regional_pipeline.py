"""
Uganda regional rainfall pipeline — the national notebook's analysis, run per region.

Usage (from the repo root):
    python scripts/regional_pipeline.py [path/to/input.csv]

Input: the long CSV from scripts/gee/uganda_regional_rainfall_gee.js
       (region, group, date, month, year, rainfall_mm).
       Defaults to data/raw/uganda_rainfall_by_region_1990_2025.csv.
Output (written to data/processed/):
        regional_summary.csv  — one row per region, every headline metric
        regional_droughts.csv — top SPI-3 drought episodes per region
        regional_results.json — everything above plus monthly series, for the report
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'data' / 'processed'

EL_NINO = [1991, 1994, 1997, 2002, 2004, 2006, 2009, 2014, 2015, 2018, 2023]
LA_NINA = [1995, 1998, 1999, 2000, 2005, 2007, 2008, 2010, 2011, 2016, 2017, 2020, 2021, 2022, 2024]


def load(path):
    df = pd.read_csv(path)
    if 'region' not in df.columns:            # the original national export
        df['region'], df['group'] = 'Uganda (national)', 'Reference'
    df = df[['region', 'group', 'date', 'month', 'year', 'rainfall_mm']].copy()
    # geoBoundaries names end in "Region" and the GEE script appends " region"
    df['region'] = df['region'].str.replace(' Region region', '', regex=False)
    df['month'], df['year'] = df.month.astype(int), df.year.astype(int)
    df = df.dropna(subset=['rainfall_mm']).sort_values(['region', 'date'])
    bad = df.groupby('region').size()
    bad = bad[bad != bad.max()]
    if len(bad):
        print('WARNING: regions with missing months:\n', bad)
    return df


def drought_episodes(g):
    s = g.set_index('date')['rainfall_mm']
    r3 = s.rolling(3).sum().to_frame('r3')
    r3['month'] = g['month'].values
    c = r3.groupby('month')['r3'].agg(['mean', 'std'])
    r3 = r3.join(c, on='month')
    r3['spi3'] = (r3.r3 - r3['mean']) / r3['std']
    r3['dry'] = r3.spi3 <= -1
    r3['run'] = (r3.dry != r3.dry.shift()).cumsum()
    ep = (r3[r3.dry].reset_index().groupby('run')
          .agg(start=('date', 'first'), end=('date', 'last'),
               months=('dry', 'sum'), min_spi3=('spi3', 'min'))
          .sort_values(['months', 'min_spi3'], ascending=[False, True]))
    return r3['spi3'], ep


def analyse(g):
    g = g.copy()
    clim = g.groupby('month')['rainfall_mm'].agg(['mean', 'std'])
    g = g.join(clim, on='month')
    g['z'] = (g.rainfall_mm - g['mean']) / g['std']

    full = g.groupby('year').size()
    annual = g[g.year.isin(full[full == 12].index)].groupby('year')['rainfall_mm'].sum()
    lr = stats.linregress(annual.index, annual.values)
    tau, p_tau = stats.kendalltau(annual.index, annual.values)

    mam = g[g.month.isin([3, 4, 5])].groupby('year')['rainfall_mm'].sum()
    son = g[g.month.isin([9, 10, 11])].groupby('year')['rainfall_mm'].sum()
    lm, ls = stats.linregress(mam.index, mam.values), stats.linregress(son.index, son.values)

    g['decade'] = g.year // 10 * 10
    dec = annual.groupby(annual.index // 10 * 10).mean()
    cv = g.groupby('decade')['rainfall_mm'].apply(lambda x: x.std() / x.mean())

    spi3, ep = drought_episodes(g)
    g['spi3'] = spi3.values

    el, la = son[son.index.isin(EL_NINO)], son[son.index.isin(LA_NINA)]
    p_enso = stats.ttest_ind(el, la).pvalue

    a = g['z'].values
    lag1 = np.corrcoef(a[:-1], a[1:])[0, 1]

    top = ep.iloc[0] if len(ep) else None
    summary = dict(
        mean_annual_mm=annual.mean(), annual_cv=annual.std() / annual.mean(),
        trend_mm_per_yr=lr.slope, trend_p=lr.pvalue, kendall_p=p_tau,
        driest_year=int(annual.idxmin()), driest_mm=annual.min(),
        wettest_year=int(annual.idxmax()), wettest_mm=annual.max(),
        mam_mean=mam.mean(), mam_cv=mam.std() / mam.mean(), mam_trend=lm.slope, mam_p=lm.pvalue,
        son_mean=son.mean(), son_cv=son.std() / son.mean(), son_trend=ls.slope, son_p=ls.pvalue,
        wettest_month=int(clim['mean'].idxmax()), most_variable_month=int(clim['std'].idxmax()),
        drought_months_spi3=int((g.spi3 <= -1).sum()),
        drought_episodes=int(len(ep)),
        longest_drought_months=int(top.months) if top is not None else 0,
        longest_drought=f"{top.start} to {top.end}" if top is not None else '',
        worst_spi3=float(ep.min_spi3.min()) if len(ep) else None,
        enso_son_elnino=el.mean(), enso_son_lanina=la.mean(), enso_p=p_enso,
        lag1_autocorr=lag1,
        **{f'decade_{k}s_mm': v for k, v in dec.items()},
        **{f'cv_{k}s': v for k, v in cv.items()},
    )
    series = dict(
        monthly=g[['date', 'year', 'month', 'rainfall_mm', 'z', 'spi3']].round(3).to_dict('records'),
        annual=[dict(y=int(y), v=round(v, 1)) for y, v in annual.items()],
        seasons=[dict(y=int(y), mam=round(mam[y], 1), son=round(son[y], 1)) for y in mam.index],
        clim=clim.round(1).reset_index().to_dict('records'),
        episodes=ep.head(6).round(2).to_dict('records'),
    )
    return summary, series, ep


def main(path):
    df = load(path)
    rows, eps, out = [], [], {}
    for (region, group), g in df.groupby(['region', 'group'], sort=False):
        summ, series, ep = analyse(g)
        rows.append(dict(region=region, group=group, **summ))
        e = ep.head(5).copy(); e.insert(0, 'region', region); eps.append(e)
        out[region] = dict(group=group, summary=summ, **series)

    summary = pd.DataFrame(rows)
    summary.round(3).to_csv(OUT / 'regional_summary.csv', index=False)
    pd.concat(eps).round(2).to_csv(OUT / 'regional_droughts.csv', index=False)
    with open(OUT / 'regional_results.json', 'w') as f:
        json.dump(out, f, default=lambda o: o.item() if hasattr(o, 'item') else str(o))

    cols = ['region', 'mean_annual_mm', 'annual_cv', 'trend_mm_per_yr', 'trend_p',
            'son_trend', 'son_p', 'longest_drought_months', 'longest_drought', 'enso_p']
    with pd.option_context('display.width', 200, 'display.max_columns', 20):
        print(summary[cols].round(3).to_string(index=False))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else RAW / 'uganda_rainfall_by_region_1990_2025.csv')
