"""
Compute every number shown in the Part 3 report and the synthesis report, and
inject it into the HTML pages so they stay in sync with the data.

Usage (from anywhere):
    python scripts/build_report_data.py

Inputs:  data/raw/uganda_rainfall_by_region_1990_2025.csv
         data/external/dmi_monthly.csv, data/external/oni_seasonal.csv
Outputs: data/processed/iod_report_data.json, data/processed/synthesis_data.json
         and the <script id="report-data"> block inside
         reports/iod_report.html and reports/synthesis_report.html
"""
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent.parent
RAW, EXT, OUT, REPORTS = (ROOT / 'data' / 'raw', ROOT / 'data' / 'external',
                          ROOT / 'data' / 'processed', ROOT / 'reports')

ORDER = ['Karamoja', 'Eastern', 'Northern', 'Central', 'Western', 'Lake Victoria basin', 'Uganda (national)']
REGIONS = ORDER[:-1]
YEARS = list(range(1990, 2026))
IOD_THRESHOLD = 0.4


# ---------------------------------------------------------------- load
def load():
    df = pd.read_csv(RAW / 'uganda_rainfall_by_region_1990_2025.csv')
    df['region'] = df['region'].str.replace(' Region region', '', regex=False)
    df['month'], df['year'] = df['month'].astype(int), df['year'].astype(int)
    dmi = pd.read_csv(EXT / 'dmi_monthly.csv')
    oni = pd.read_csv(EXT / 'oni_seasonal.csv')
    return df, dmi, oni


def season_rain(df, months):
    return (df[df['month'].isin(months)].groupby(['year', 'region'])['rainfall_mm']
            .sum().unstack()[ORDER].loc[YEARS])


def season_dmi(dmi, months):
    return dmi[dmi['month'].isin(months)].groupby('year')['dmi'].mean().loc[YEARS]


def season_oni(oni, code):
    return oni[oni['season'] == code].set_index('year')['oni'].loc[YEARS]


def pearson(x, y):
    r, p = stats.pearsonr(np.asarray(x, float), np.asarray(y, float))
    return float(r), float(p)


def partial_r(y, x, control):
    rx = sm.OLS(np.asarray(x, float), sm.add_constant(np.asarray(control, float))).fit().resid
    ry = sm.OLS(np.asarray(y, float), sm.add_constant(np.asarray(control, float))).fit().resid
    return pearson(rx, ry)


def pct(s):
    return 100 * (s / s.mean() - 1)


def r4(v):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), 4)


# ---------------------------------------------------------------- shared pieces
def corr_block(rain, dmi_s, oni_s):
    out = {}
    for r in ORDER:
        rd, pd_ = pearson(dmi_s, rain[r])
        ro, po = pearson(oni_s, rain[r])
        out[r] = {'r_dmi': r4(rd), 'p_dmi': r4(pd_), 'r_oni': r4(ro), 'p_oni': r4(po)}
    return out


def monthly_dmi_corr(df, dmi):
    z = df.copy()
    z['z'] = z.groupby(['region', 'month'])['rainfall_mm'].transform(lambda x: (x - x.mean()) / x.std())
    d = dmi.set_index(['year', 'month'])['dmi']
    out = {}
    for r in ORDER:
        g = z[z['region'] == r].set_index(['year', 'month'])['z']
        out[r] = []
        for m in range(1, 13):
            rr, p = pearson(g.xs(m, level=1).loc[YEARS], d.xs(m, level=1).loc[YEARS])
            out[r].append({'r': r4(rr), 'p': r4(p)})
    return out


def trend_control(rain, dmi_s):
    out = {}
    for r in ORDER:
        y = rain[r].values.astype(float)
        yrs = np.array(YEARS, float)
        base = sm.OLS(y, sm.add_constant(yrs)).fit()
        ctrl = sm.OLS(y, sm.add_constant(np.column_stack([yrs, dmi_s.values]))).fit()
        out[r] = {'trend': r4(base.params[1]), 'p': r4(base.pvalues[1]),
                  'trend_ctrl': r4(ctrl.params[1]), 'p_ctrl': r4(ctrl.pvalues[1]),
                  'r2': r4(base.rsquared), 'r2_ctrl': r4(ctrl.rsquared)}
    return out


# ---------------------------------------------------------------- Part 3 report
def iod_data(df, dmi, oni):
    seasons = [('SON', [9, 10, 11]), ('OND', [10, 11, 12]), ('MAM', [3, 4, 5]), ('JJA', [6, 7, 8])]
    rain = {s: season_rain(df, m) for s, m in seasons}
    dmi_s = {s: season_dmi(dmi, m) for s, m in seasons}
    oni_s = {s: season_oni(oni, s) for s, _ in seasons}

    d_ond, o_ond = dmi_s['OND'], oni_s['OND']
    phase = pd.Series('neutral', index=d_ond.index)
    phase[d_ond >= IOD_THRESHOLD] = 'positive'
    phase[d_ond <= -IOD_THRESHOLD] = 'negative'

    keep = ~np.isin(YEARS, [1997, 2019])
    top3_jja = dmi_s['JJA'].sort_values().index[-3:]
    keep_jja = ~dmi_s['JJA'].index.isin(top3_jja)
    partial, partial_jja, robust, comp = {}, {}, {}, {}
    for r in ORDER:
        y = rain['OND'][r]
        a, pa = partial_r(y, d_ond, o_ond)
        b, pb = partial_r(y, o_ond, d_ond)
        partial[r] = {'dmi_given_oni': r4(a), 'p_dmi': r4(pa), 'oni_given_dmi': r4(b), 'p_oni': r4(pb)}
        yj = rain['JJA'][r]
        a, pa = partial_r(yj, dmi_s['JJA'], oni_s['JJA'])
        b, pb = partial_r(yj, oni_s['JJA'], dmi_s['JJA'])
        partial_jja[r] = {'dmi_given_oni': r4(a), 'p_dmi': r4(pa), 'oni_given_dmi': r4(b), 'p_oni': r4(pb),
                          'r_without_top3': r4(pearson(dmi_s['JJA'][keep_jja], yj[keep_jja])[0])}
        rho, prho = stats.spearmanr(d_ond, y)
        rex, pex = pearson(d_ond[keep], y[keep])
        robust[r] = {'spearman': r4(rho), 'p_spearman': r4(prho), 'r_without': r4(rex), 'p_without': r4(pex)}
        an = pct(y)
        comp[r] = {k: r4(an[phase == k].mean()) for k in ['positive', 'neutral', 'negative']}
        comp[r]['p_pos_vs_neutral'] = r4(stats.ttest_ind(y[phase == 'positive'], y[phase == 'neutral'],
                                                         equal_var=False).pvalue)

    return {
        'order': ORDER, 'years': YEARS, 'threshold': IOD_THRESHOLD,
        'dmi_ond': [r4(v) for v in d_ond], 'oni_ond': [r4(v) for v in o_ond],
        'phase': phase.tolist(),
        'dmi_oni_r': r4(pearson(d_ond, o_ond)[0]),
        'dmi_trend_decade': r4(stats.linregress(YEARS, d_ond).slope * 10),
        'dmi_trend_p': r4(stats.linregress(YEARS, d_ond).pvalue),
        'corr': {s: corr_block(rain[s], dmi_s[s], oni_s[s]) for s in ['SON', 'OND', 'MAM', 'JJA']},
        'partial': partial, 'partial_jja': partial_jja, 'top3_jja': sorted(int(y) for y in top3_jja),
        'jja_share': {r: r4(rain['JJA'][r].mean() / season_rain(df, list(range(1, 13)))[r].mean()) for r in ORDER}, 'robust': robust, 'composite': comp,
        'ond_pct': {r: [r4(v) for v in pct(rain['OND'][r])] for r in ORDER},
        'son_pct': {r: [r4(v) for v in pct(rain['SON'][r])] for r in ORDER},
        'monthly_dmi': monthly_dmi_corr(df, dmi),
        'trend_control': {s: trend_control(rain[s], dmi_s[s]) for s in ['SON', 'OND']},
    }


# ---------------------------------------------------------------- synthesis report
def loo_skill(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(y)
    pred, clim = np.empty(n), np.empty(n)
    for i in range(n):
        m = np.ones(n, bool)
        m[i] = False
        b = np.polyfit(x[m], y[m], 1)
        pred[i], clim[i] = np.polyval(b, x[i]), y[m].mean()
    t1, t2 = np.quantile(y, [1 / 3, 2 / 3])
    cat = lambda v: np.digitize(v, [t1, t2])
    return {'cv_r': r4(pearson(pred, y)[0]),
            'mse_skill': r4(1 - ((pred - y) ** 2).mean() / ((clim - y) ** 2).mean()),
            'tercile_hit': r4((cat(pred) == cat(y)).mean())}


def synthesis_data(df, dmi, oni):
    annual = df.groupby(['year', 'region'])['rainfall_mm'].sum().unstack()[ORDER].loc[YEARS]
    mam = season_rain(df, [3, 4, 5])
    jja = season_rain(df, [6, 7, 8])
    son = season_rain(df, [9, 10, 11])
    ond = season_rain(df, [10, 11, 12])
    djf = season_rain(df, [12, 1, 2])

    summary = {}
    for r in ORDER:
        a = annual[r]
        lr = stats.linregress(YEARS, a)
        tau_p = stats.kendalltau(YEARS, a).pvalue
        seas = {}
        for name, s in [('MAM', mam), ('JJA', jja), ('SON', son), ('OND', ond)]:
            t = stats.linregress(YEARS, s[r])
            seas[name] = {'mean': r4(s[r].mean()), 'cv': r4(s[r].std() / s[r].mean()),
                          'trend': r4(t.slope), 'p': r4(t.pvalue)}
        summary[r] = {
            'mean': r4(a.mean()), 'cv': r4(a.std() / a.mean()), 'trend': r4(lr.slope), 'p': r4(lr.pvalue),
            'kendall_p': r4(tau_p), 'driest': int(a.idxmin()), 'wettest': int(a.idxmax()),
            'season': seas,
            'share': {k: r4(s[r].mean() / a.mean()) for k, s in [('MAM', mam), ('JJA', jja), ('SON', son), ('DJF', djf)]},
        }

    def corr_matrix(t):
        c = t[REGIONS].corr()
        off = c.values[np.triu_indices(len(REGIONS), 1)]
        return {'m': [[r4(v) for v in row] for row in c.values],
                'mean': r4(off.mean()), 'min': r4(off.min()), 'max': r4(off.max())}

    coherence = {k: corr_matrix(t) for k, t in [('annual', annual), ('MAM', mam), ('OND', ond)]}

    coupling = {}
    for r in ORDER:
        a, pa = pearson(mam[r], ond[r])
        b, pb = pearson(ond[r].iloc[:-1].values, mam[r].iloc[1:].values)
        coupling[r] = {'mam_ond': r4(a), 'p_mam_ond': r4(pa), 'ond_next_mam': r4(b), 'p_ond_next_mam': r4(pb)}

    # Lead predictability of Oct–Dec rain from indices known by the end of September
    sep_dmi = season_dmi(dmi, [9])
    ja_dmi = season_dmi(dmi, [7, 8])
    predictors = {'Aug DMI': season_dmi(dmi, [8]), 'Sep DMI': sep_dmi,
                  'Jul–Sep ONI': season_oni(oni, 'JAS'), 'Oct–Dec DMI (same season)': season_dmi(dmi, [10, 11, 12])}
    lead = {k: {r: dict(zip(['r', 'p'], map(r4, pearson(x, ond[r])))) for r in ORDER} for k, x in predictors.items()}
    skill = {'Jul–Aug': {r: loo_skill(ja_dmi, ond[r]) for r in ORDER},
             'Sep': {r: loo_skill(sep_dmi, ond[r]) for r in ORDER}}

    # Outcomes after a strong July–August IOD (known by early September, before most planting)
    hi, lo = ja_dmi >= IOD_THRESHOLD, ja_dmi <= -IOD_THRESHOLD
    conditional = {}
    for r in ORDER:
        y = ond[r]
        t1, t2, med = y.quantile(1 / 3), y.quantile(2 / 3), y.median()
        conditional[r] = {
            'pos_n': int(hi.sum()), 'pos_above_median': r4((y[hi] > med).mean()),
            'pos_upper_tercile': r4((y[hi] > t2).mean()), 'pos_lower_tercile': r4((y[hi] < t1).mean()),
            'neg_n': int(lo.sum()), 'neg_below_median': r4((y[lo] < med).mean()),
            'neutral_above_median': r4((y[~hi & ~lo] > med).mean()),
        }

    monthly_trend = {}
    for r in ORDER:
        monthly_trend[r] = []
        for m in range(1, 13):
            s = df[(df['region'] == r) & (df['month'] == m)].set_index('year')['rainfall_mm'].loc[YEARS]
            t = stats.linregress(YEARS, s)
            monthly_trend[r].append({'slope': r4(t.slope), 'p': r4(t.pvalue)})

    # Failed seasons: totals below each region's own 20th percentile, counted per decade
    failed = {}
    for name, t in [('MAM', mam), ('OND', ond)]:
        f = t < t.quantile(0.2)
        failed[name] = {r: {str(d): int(f[r][(f.index // 10) * 10 == d].sum()) for d in [1990, 2000, 2010, 2020]}
                        for r in ORDER}

    return {
        'order': ORDER, 'regions': REGIONS, 'years': YEARS,
        'annual': {r: [r4(v) for v in annual[r]] for r in ORDER},
        'mam': {r: [r4(v) for v in mam[r]] for r in ORDER},
        'ond': {r: [r4(v) for v in ond[r]] for r in ORDER},
        'summary': summary, 'coherence': coherence, 'coupling': coupling,
        'lead': lead, 'skill': skill, 'conditional': conditional,
        'sep_dmi': [r4(v) for v in sep_dmi], 'ja_dmi': [r4(v) for v in ja_dmi],
        'monthly_trend': monthly_trend, 'monthly_dmi': monthly_dmi_corr(df, dmi),
        'failed': failed,
        'drivers': {
            'OND': corr_block(ond, season_dmi(dmi, [10, 11, 12]), season_oni(oni, 'OND')),
            'SON': corr_block(son, season_dmi(dmi, [9, 10, 11]), season_oni(oni, 'SON')),
            'MAM': corr_block(mam, season_dmi(dmi, [3, 4, 5]), season_oni(oni, 'MAM')),
            'JJA': corr_block(jja, season_dmi(dmi, [6, 7, 8]), season_oni(oni, 'JJA')),
        },
        'trend_control': {'SON': trend_control(son, season_dmi(dmi, [9, 10, 11])),
                          'OND': trend_control(ond, season_dmi(dmi, [10, 11, 12]))},
    }


# ---------------------------------------------------------------- inject
DATA_TAG = re.compile(r'(<script id="report-data" type="application/json">)(.*?)(</script>)', re.S)


def inject(html_path, data):
    if not html_path.exists():
        print(f'skip (not found): {html_path.name}')
        return
    s = html_path.read_text()
    payload = json.dumps(data, separators=(',', ':')).replace('</', '<\\/')
    s, n = DATA_TAG.subn(lambda m: m.group(1) + payload + m.group(3), s)
    if n != 1:
        raise SystemExit(f'{html_path.name}: expected one report-data block, found {n}')
    html_path.write_text(s)
    print(f'updated {html_path.relative_to(ROOT)}')


def main():
    df, dmi, oni = load()
    iod = iod_data(df, dmi, oni)
    syn = synthesis_data(df, dmi, oni)
    syn['partial'] = {'OND': iod['partial'], 'JJA': iod['partial_jja']}
    (OUT / 'iod_report_data.json').write_text(json.dumps(iod, indent=1))
    (OUT / 'synthesis_data.json').write_text(json.dumps(syn, indent=1))
    inject(REPORTS / 'iod_report.html', iod)
    inject(REPORTS / 'synthesis_report.html', syn)


if __name__ == '__main__':
    main()
