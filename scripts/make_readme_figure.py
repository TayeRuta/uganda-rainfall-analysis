"""
README headline figure: annual rainfall and linear trend for Karamoja, the
Eastern region and the national reference, 1990–2025.

Usage (from anywhere):
    python scripts/make_readme_figure.py

Input:  data/processed/regional_results.json (from regional_pipeline.py)
Output: figures/regional_trends_light.png, figures/regional_trends_dark.png
"""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / 'data' / 'processed' / 'regional_results.json'
OUT = ROOT / 'figures'

THEMES = {
    'light': dict(surface='#fcfcfb', ink='#0b0b0b', ink2='#52514e', grid='#e6e5e1',
                  series={'Eastern': '#eb6834', 'Karamoja': '#2a78d6',
                          'Uganda (national)': '#8f8e89'}),
    'dark': dict(surface='#1a1a19', ink='#ffffff', ink2='#c3c2b7', grid='#33332f',
                 series={'Eastern': '#d95926', 'Karamoja': '#3987e5',
                         'Uganda (national)': '#8a8983'}),
}
LABELS = {'Eastern': 'Eastern region', 'Karamoja': 'Karamoja',
          'Uganda (national)': 'Uganda (national)'}


def draw(results, theme, path):
    t = THEMES[theme]
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, ax = plt.subplots(figsize=(10, 5.4), dpi=200)
    fig.patch.set_facecolor(t['surface'])
    ax.set_facecolor(t['surface'])

    for region in ['Uganda (national)', 'Karamoja', 'Eastern']:
        years = np.array([a['y'] for a in results[region]['annual']])
        mm = np.array([a['v'] for a in results[region]['annual']])
        lr = stats.linregress(years, mm)
        c = t['series'][region]
        ax.plot(years, mm, color=c, lw=1.4, alpha=0.45, solid_joinstyle='round')
        ax.plot(years, lr.intercept + lr.slope * years, color=c, lw=2.6,
                solid_capstyle='round')
        ax.plot(years[-1], lr.intercept + lr.slope * years[-1], 'o', ms=6,
                color=c, mec=t['surface'], mew=2)
        sig = f'p = {lr.pvalue:.3f}' if lr.pvalue < 0.05 else 'not significant'
        ax.annotate(f'{LABELS[region]}\n{lr.slope:+.1f} mm/yr ({sig})',
                    (years[-1], lr.intercept + lr.slope * years[-1]),
                    xytext=(12, 0), textcoords='offset points', va='center',
                    fontsize=10, color=t['ink'], linespacing=1.4)

    ax.set_xlim(1989, 2026)
    ax.set_ylim(600, 2050)
    ax.set_yticks(range(600, 2001, 200))
    ax.set_yticklabels([f'{v:,}' for v in range(600, 2001, 200)])
    ax.grid(axis='y', color=t['grid'], lw=1)
    ax.set_axisbelow(True)
    for s in ['top', 'right', 'left']:
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(t['grid'])
    ax.tick_params(colors=t['ink2'], length=0, labelsize=10)
    ax.set_ylabel('Annual rainfall (mm)', color=t['ink2'], fontsize=10)

    fig.text(0.06, 0.95, "Karamoja and Eastern Uganda are getting wetter. The national total isn't.",
             fontsize=14, fontweight='bold', color=t['ink'])
    fig.text(0.06, 0.90, 'Annual rainfall 1990–2025 (faint) with linear trend (bold). '
             'Source: CHIRPS via Google Earth Engine.', fontsize=10, color=t['ink2'])
    fig.subplots_adjust(left=0.09, right=0.76, top=0.85, bottom=0.08)
    fig.savefig(path, facecolor=t['surface'])
    plt.close(fig)


def main():
    results = json.loads(RESULTS.read_text())
    OUT.mkdir(exist_ok=True)
    for theme in THEMES:
        draw(results, theme, OUT / f'regional_trends_{theme}.png')


if __name__ == '__main__':
    main()
