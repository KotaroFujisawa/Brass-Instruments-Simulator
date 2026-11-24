"""Draw the ten published instruments on common pressure and lip-frequency axes."""

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import json
import math
from pathlib import Path
from typing import NamedTuple

import playability_maps as mapplot
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
WIDTH_PRESSURE_KPA = 12.
INSTRUMENTS = (
    ('trumpet', 'トランペット', 15),
    ('flugelhorn', 'フリューゲルホルン', 15),
    ('trombone', 'トロンボーン', 15),
    ('horn', 'F／B♭ダブルホルン', 22),
    ('euphonium', 'ユーフォニアム', 22),
    ('ophicleide', 'B♭管オフィクレイド', 22),
    ('tuba', 'BB♭チューバ', 22),
    ('tenor_horn', 'E♭テナーホルン', 22),
    ('keyed_bugle', 'B♭キー付きビューグル', 15),
    ('serpent', 'C管セルパン', 17),
)
LIMITS = ((35., 1300.), (0., 23.))
X_TICK_HZ = 200.
COMPARE = ('F3', 'Bb3', 'C4')
SUBTITLE = ('緑は持続部の音程が目標から±75セント以内。'
            '全楽器で横軸35〜1,300 Hz、縦軸0〜23 kPa。')


class IncompleteSweep(ValueError):
    """A data file is present but has not finished recording."""

class PlayabilityMeasure(NamedTuple):
    onset_kpa: float
    width_cents: float
    width_touches_edge: bool = False
    width_calculated: bool = True


def measure_band(rows):
    successful = [row['blowing_pressure_pa'] for row in rows if row['outcome'] == 'target']
    onset_kpa = min(successful, default=math.nan) / 1000
    same_pressure = sorted(
        (row for row in rows if math.isclose(row['blowing_pressure_pa'], 1000 * WIDTH_PRESSURE_KPA)),
        key=lambda row: row['lip_frequency_hz'],
    )
    if not same_pressure:
        return PlayabilityMeasure(onset_kpa, math.nan, width_calculated=False)
    bands = []
    low = high = None
    for row in same_pressure:
        if row['outcome'] == 'target':
            high = row['lip_frequency_hz']
            if low is None:
                low = high
        elif low is not None:
            bands.append((low, high))
            low = high = None
    if low is not None:
        bands.append((low, high))
    if not bands:
        return PlayabilityMeasure(onset_kpa, math.nan)
    low, high = max(bands, key=lambda band: math.log2(band[1] / band[0]))
    touches_edge = (low == same_pressure[0]['lip_frequency_hz']
                    or high == same_pressure[-1]['lip_frequency_hz'])
    return PlayabilityMeasure(onset_kpa, 1200 * math.log2(high / low), touches_edge)

def legacy_panel_details(instrument, payload):
    if instrument not in ('horn', 'ophicleide'):
        return {}
    selectors = payload.get('metadata', {}).get('selector_by_note', {})
    summaries = {row['note']: row for row in payload.get('summaries', ())}
    out = {}
    for note in payload['notes']:
        choice = selectors.get(note)
        summary = summaries.get(note, {})
        if instrument == 'horn':
            side = summary.get('side')
            if side is None and isinstance(choice, dict):
                side = choice.get('side')
            if side is None and isinstance(choice, (list, tuple)) and choice:
                side = choice[0]
            if side in ('F', 'Bb', 'B♭'):
                out[note] = f'{mapplot.label(side)}管'
        else:
            holes = summary.get('open_holes')
            if holes is None and isinstance(choice, dict):
                holes = choice.get('open_holes')
            if holes is None and isinstance(choice, (list, tuple)):
                holes = choice
            if (isinstance(holes, (list, tuple)) and len(holes) == 1
                    and isinstance(holes[0], (list, tuple))):
                holes = holes[0]
            if isinstance(holes, (list, tuple)) and all(isinstance(n, int) for n in holes):
                holes_text = '・'.join(map(str, holes)) if holes else 'なし'
                out[note] = f'開孔 {holes_text}'
    return out

def load(path, expected):
    data = json.loads(path.read_bytes())
    check_grid(data, expected, path.name)
    return data


def check_grid(data, expected, label):
    notes = set(data['notes'])
    if len(notes) != expected or len(data['notes']) != expected:
        raise IncompleteSweep(f'{label}: expected {expected} notes, found {len(notes)}')
    counts = Counter(row['note'] for row in data['rows'])
    if set(counts) != notes or set(counts.values()) != {768}:
        raise IncompleteSweep(f'{label}: the grid is incomplete')
    if data.get('metadata', {}).get('pitch_tolerance_cents', 75.) != 75.:
        raise ValueError(f'{label}: the plot requires the shared ±75-cent tolerance')



def panel_details(instrument, data):
    if instrument in ('horn', 'ophicleide'):
        return legacy_panel_details(instrument, data)
    if instrument not in ('keyed_bugle', 'serpent'):
        return {}
    selectors = data.get('metadata', {}).get('selector_by_note', {})
    summaries = {row['note']: row for row in data.get('summaries', ())}
    labels = {}
    for note in data['notes']:
        selection = selectors.get(note)
        if isinstance(selection, dict):
            detail = summaries.get(note, {}) | selection
        else:
            detail = summaries.get(note, {})
        holes = detail.get('open_holes')
        if not isinstance(holes, (list, tuple)) or not all(isinstance(n, int) for n in holes):
            continue
        fractions = dict(detail.get('opening_fractions') or ())
        ports = [f'{n}({round(100*fractions.get(n, fractions.get(str(n), 1.)))}%)'
                 if n in fractions or str(n) in fractions else str(n) for n in holes]
        labels[note] = '開孔 ' + ('・'.join(ports) if ports else 'なし')
    return labels


def group_notes(data):
    by_note = defaultdict(list)
    for row in data['rows']:
        by_note[row['note']].append(row)
    return by_note


def measures(datasets):
    metrics = {}
    for key, _, _ in INSTRUMENTS:
        groups = group_notes(datasets[key])
        metrics[key] = {note: measure_band(groups[note]) if note in groups else None
                        for note in COMPARE}
    return metrics


def save(fig, path):
    for extension in ('png', 'svg'):
        fig.savefig(path.with_suffix('.' + extension), dpi=230)
    mapplot.plt.close(fig)


def draw_summary(data, path):
    plt = mapplot.plt
    np = mapplot.np
    fig, axes = plt.subplots(1, 2, figsize=(12.3, 7.4), sharey=True)
    fig.subplots_adjust(left=.278, right=.963, top=.745, bottom=.159, wspace=.20)
    fig.text(.058, .948, '10楽器を同じ実音で比較', fontsize=23, fontweight='bold', va='top')
    fig.text(.058, .865, '全楽器で計算したB♭3とC4に、低いF3を加えました。',
             fontsize=11, color=mapplot.MUTED, va='top')

    metric_titles = ('最初に目標音が出た吹奏圧（kPa）',
                     f'{WIDTH_PRESSURE_KPA:g} kPaでの最長連続幅（セント）')
    for metric, (axis, title, palette) in enumerate(zip(axes, metric_titles, ('YlOrBr','BuGn'))):
        items = [[data[key][note] for note in COMPARE] for key, _, _ in INSTRUMENTS]
        values = np.array([[np.nan if item is None else item[metric] for item in line] for line in items])
        present = values[np.isfinite(values)]
        upper = max(float(present.max()), 1.) if present.size else 1.
        coloring = plt.get_cmap(palette)
        for i, row in enumerate(items):
            for j, item in enumerate(row):
                if item is None or (metric == 1 and not item.width_calculated):
                    caption, color, ink = '※', '#FFFFFF', mapplot.MUTED
                elif not math.isfinite(item[metric]):
                    caption, color, ink = '—', '#F0F3F6', mapplot.MUTED
                else:
                    value = item[metric]
                    shade = .12 + .56 * value/upper
                    color = coloring(shade)
                    luminous = .2126*color[0] + .7152*color[1] + .0722*color[2]
                    ink = 'white' if luminous < .48 else mapplot.TEXT
                    suffix = '*' if metric == 1 and item.width_touches_edge else ''
                    caption = f'{value:g}' if metric == 0 else (f'{value:.0f}' if value else '1点') + suffix
                axis.add_patch(Rectangle((j-.49, i-.47), .98, .94, facecolor=color,
                                         edgecolor='#E8EDF2', linewidth=.55))
                axis.text(j, i, caption, ha='center', va='center', color=ink, fontsize=11)
        axis.set_xlim(-.5, len(COMPARE)-.5)
        axis.set_ylim(len(INSTRUMENTS)-.5, -.5)
        axis.spines[:].set_visible(False)
        axis.set_xticks(range(len(COMPARE)), [mapplot.label(note) for note in COMPARE])
        axis.xaxis.tick_top()
        axis.tick_params(axis='x', length=0, pad=7, labelsize=11)
        axis.tick_params(axis='y', length=0, pad=8, labelsize=10.2, labelleft=metric==0)
        if metric == 0:
            axis.set_yticks(range(len(INSTRUMENTS)), [label for _, label, _ in INSTRUMENTS])
        axis.set_title(title, fontsize=12.6, pad=25, fontweight='bold')
        axis.axhline(5.5, color=mapplot.RULE, linewidth=1.2, zorder=4)

    fig.text(.058, .109,
             '濃い色ほど数値が大きくなります。圧力は掃引格子での最小値。幅は目標の±75セント以内に入った連続格子点から算出。',
             fontsize=9.5, color=mapplot.MUTED, va='top')
    fig.text(.058, .070,
             '「※」は未計算、「—」は発音点なし、「1点」は幅0。* は区間が掃引範囲の端に到達。',
             fontsize=9.5, color=mapplot.MUTED, va='top')
    save(fig, path)


def draw_c4_maps(datasets, path):
    note = 'C4'
    plt = mapplot.plt
    fig, axes = plt.subplots(2, 5, figsize=(15.75, 7.0), sharex=True, sharey=True)
    fig.subplots_adjust(left=.068, right=.984, top=.743, bottom=.174, wspace=.15, hspace=.59)
    fig.text(.068, .948, 'C4の発音範囲を10楽器で比較',
             fontsize=22, fontweight='bold', va='top')
    fig.text(.068, .867, SUBTITLE, fontsize=10.5, color=mapplot.MUTED, va='top')
    handles = [mapplot.Patch(facecolor=color, edgecolor='none', label=title)
               for title, color in mapplot.OUTCOMES.values()]
    handles.append(mapplot.Patch(facecolor='#FFFFFF', edgecolor=mapplot.RULE, label='未計算'))
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(.066, .828),
               borderaxespad=0., ncol=len(handles), frameon=False, fontsize=9.6,
               columnspacing=1.65)
    for axis, (key, title, _) in zip(axes.flat, INSTRUMENTS):
        rows = [row for row in datasets[key]['rows'] if row['note'] == note]
        if rows:
            x, y, values = mapplot.panel_data(note, rows)
            axis.pcolormesh(x, y, values, cmap=mapplot.COLORS, norm=mapplot.NORM,
                            shading='flat', edgecolors='none', antialiased=False)
        axis.set_xlim(*LIMITS[0])
        axis.set_ylim(*LIMITS[1])
        axis.set_axisbelow(True)
        axis.grid(color='#E9EDF2', linewidth=.6)
        axis.xaxis.set_major_locator(mapplot.MultipleLocator(X_TICK_HZ))
        axis.yaxis.set_major_locator(mapplot.MultipleLocator(5))
        axis.xaxis.set_major_formatter(mapplot.StrMethodFormatter('{x:.0f}'))
        axis.tick_params(axis='both', labelsize=9.2, length=3., pad=3.5)
        axis.tick_params(axis='x', labelbottom=True)
        axis.set_title(title, loc='left', fontsize=10.6, pad=6, fontweight='bold')
    fig.supxlabel('唇の固有振動数（Hz）', y=.103, fontsize=12)
    fig.supylabel('定常吹奏圧（kPa）', x=.012, fontsize=12)
    fig.text(.068, .034, '実音C4（約262 Hz）。白は未計算。', fontsize=9.3, color=mapplot.MUTED)
    save(fig, path)

def load_published():
    directory = ROOT / 'docs' / 'results' / 'playability'
    results = json.loads((directory / 'allbrass_playability_results.json').read_bytes())
    datasets = results['comparison']
    for dataset in datasets.values():
        dataset['rows'] = []
    with gzip.open(directory / 'allbrass_playability_trials.csv.gz',
                   mode='rt', encoding='utf-8-sig', newline='') as handle:
        for raw in csv.DictReader(handle):
            datasets[raw['instrument']]['rows'].append({
                'note': raw['note'],
                'lip_frequency_hz': float(raw['lip_frequency_hz']),
                'blowing_pressure_pa': float(raw['blowing_pressure_pa']),
                'outcome': raw['outcome'],
            })
    for key, _, expected in INSTRUMENTS:
        check_grid(datasets[key], expected, key)
    return datasets


def load_sweeps(input_root):
    datasets = {}
    for key, _, expected in INSTRUMENTS:
        if key == 'trumpet':
            directory = input_root / 'trumpet_playability'
        else:
            directory = input_root / 'brass_playability' / key
        prefix = 'planar' if key == 'serpent' else key
        datasets[key] = load(directory / f'{prefix}_playability.json', expected)
    return datasets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--published', action='store_true', help='Use the results committed with the repository.')
    source.add_argument('--input-root', type=Path, help='Use freshly calculated sweep JSON under this path.')
    parser.add_argument('--dest', type=Path, default=ROOT / 'output' / 'playability_figures')
    parser.add_argument('--font', type=Path, help='Path to a Japanese font supported by Matplotlib.')
    args = parser.parse_args()
    data = load_published() if args.published else load_sweeps(args.input_root or ROOT / 'output')
    mapplot.set_style(args.font)
    args.dest.mkdir(parents=True, exist_ok=True)
    for key, title, _ in INSTRUMENTS:
        payload = data[key]
        mapplot.draw(payload, payload['notes'], args.dest / f'{key}_playability_common_axes',
                     5, SUBTITLE, shared_axes=True, limits=LIMITS, title=f'{title}の発音範囲',
                     panel_details=panel_details(key, payload), x_tick_hz=X_TICK_HZ)
        print(key, len(payload['notes']), len(payload['rows']), flush=True)
    draw_summary(measures(data), args.dest / 'allbrass_playability_common_pitch')
    draw_c4_maps(data, args.dest / 'allbrass_playability_c4_maps')


if __name__ == '__main__':
    main()
