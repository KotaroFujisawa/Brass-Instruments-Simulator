"""Draw measured attack grids without interpolating categorical outcomes."""
from collections import Counter
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / '.deps').is_dir():
    sys.path.append(str(ROOT / '.deps'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import (
    FixedLocator, LogLocator, MaxNLocator, MultipleLocator, NullFormatter, StrMethodFormatter,
)
import numpy as np


OUTCOMES = {
    'target': ('目標音程の範囲内', '#167A70'),
    'other': ('目標音程の範囲外', '#DF994B'),
    'no_sustain': ('持続発音なし', '#E6EBF0'),
    'unstable': ('発音が不安定', '#A687C0'),
    'invalid': ('計算・判定不能', '#C74D66'),
}
COLORS = ListedColormap([color for _, color in OUTCOMES.values()])
NORM = BoundaryNorm(np.arange(len(OUTCOMES) + 1) - 0.5, COLORS.N)
INDEX = {state: i for i, state in enumerate(OUTCOMES)}
TEXT = '#17283B'
MUTED = '#4F6173'
RULE = '#CAD4DF'
FONT_PATHS = (
    Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/BIZ-UDGothicR.ttc',
    Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/NotoSansJP-VF.ttf',
    Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),
    Path('/usr/share/fonts/truetype/noto/NotoSansJP-Regular.ttf'),
)
MIDI_BASE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def set_style(font):
    source = Path(font) if font else next((path for path in FONT_PATHS if path.is_file()), None)
    if source is None:
        raise FileNotFoundError('Japanese font missing. Pass the path to a JP font with --font.')
    font_manager.fontManager.addfont(source)
    if source.name == 'BIZ-UDGothicR.ttc':
        bold = source.with_name('BIZ-UDGothicB.ttc')
        if bold.is_file():
            font_manager.fontManager.addfont(bold)
    font_name = font_manager.FontProperties(fname=source).get_name()
    plt.rcParams.update({
        'font.family': font_name, 'text.color': TEXT, 'axes.labelcolor': TEXT,
        'axes.edgecolor': RULE, 'axes.linewidth': 0.7, 'xtick.color': MUTED,
        'ytick.color': MUTED, 'axes.unicode_minus': False, 'svg.fonttype': 'path',
        'savefig.facecolor': 'white',
    })


def label(note):
    return note.replace('b', '♭').replace('#', '♯')


def pitch(note):
    midi = 12 * (int(note[-1]) + 1) + MIDI_BASE[note[0]] + note.count('#') - note.count('b')
    return 440.0 * 2.0**((midi - 69) / 12)


def borders(knots):
    if len(knots) < 2:
        raise ValueError('The map requires at least two different values on each axis.')
    middle = (knots[:-1] + knots[1:]) / 2
    return np.concatenate(([2 * knots[0] - middle[0]], middle, [2 * knots[-1] - middle[-1]]))


def panel_data(note, trials):
    frequencies = sorted({float(row['lip_frequency_hz']) for row in trials})
    pressures = sorted({float(row['blowing_pressure_pa']) / 1000.0 for row in trials})
    if not all(math.isfinite(value) and value > 0 for value in (*frequencies, *pressures)):
        raise ValueError(f'Invalid coordinate in {note}.')
    x_lookup = {f: i for i, f in enumerate(frequencies)}
    y_lookup = {p: i for i, p in enumerate(pressures)}
    values = np.full((len(pressures), len(frequencies)), np.nan)
    for row in trials:
        x = x_lookup[float(row['lip_frequency_hz'])]
        y = y_lookup[float(row['blowing_pressure_pa']) / 1000.0]
        if np.isfinite(values[y, x]):
            raise ValueError(f'Duplicate trial for {note}, {frequencies[x]} Hz, {pressures[y]} kPa.')
        values[y, x] = INDEX[row['outcome']]
    return borders(np.array(frequencies)), borders(np.array(pressures)), values


def set_log_ticks(axis):
    axis.set_xscale('log')
    axis.xaxis.set_major_locator(FixedLocator([40, 60, 100, 200, 400, 800, 1200]))
    axis.xaxis.set_major_formatter(StrMethodFormatter('{x:g}'))
    axis.xaxis.set_minor_locator(LogLocator(base=10, subs=range(2, 10)))
    axis.xaxis.set_minor_formatter(NullFormatter())


def draw_target_marker(axis, target_hz):
    axis.axvline(target_hz, color=TEXT, linestyle=(0, (3.3, 2.7)), linewidth=.9,
                 alpha=.92, zorder=5)


def draw(payload, notes, prefix, panel_columns, subtitle, validation=(), *,
         shared_axes=False, limits=None, title='トランペットの発音範囲',
         panel_details=None, x_tick_hz=200, log_hz=False):
    selected = {note: [] for note in notes}
    for trial in payload['rows']:
        if trial['note'] in selected:
            selected[trial['note']].append(trial)
    panels = {note: panel_data(note, selected[note]) for note in notes}
    pressures = [axis_y for _, axis_y, _ in panels.values()]
    ymin = max(0.0, min(axis[0] for axis in pressures))
    ymax = max(axis[-1] for axis in pressures)
    if shared_axes:
        xmin = 50 * math.floor(min(x[0] for x, _, _ in panels.values()) / 50)
        xmax = 50 * math.ceil(max(x[-1] for x, _, _ in panels.values()) / 50)
        ymin, ymax = 0., math.ceil(ymax)
        if limits is not None:
            (xmin, xmax), (ymin, ymax) = limits
            # The final measured center sits on the right edge in the log view.
            if log_hz:
                if not all(xmin <= row['lip_frequency_hz'] <= xmax
                           for rows in selected.values() for row in rows):
                    raise ValueError('A measured frequency is outside the shared log limits.')
            elif not all(xmin <= x[0] < x[-1] <= xmax for x, _, _ in panels.values()):
                raise ValueError('A measured cell is outside the shared frequency limits.')
            if not all(ymin <= y[0] < y[-1] <= ymax for _, y, _ in panels.values()):
                raise ValueError('A measured cell is outside the shared pressure limits.')
    count = len(notes)
    nrows = math.ceil(count / panel_columns)
    subsequence = count == 3
    size = (12.5, 5.30) if subsequence else (15.75, 10.05)
    if nrows > 3:
        size = (max(size[0], 3.0*panel_columns), size[1] + 2.8*(nrows-3))
    fig, axs = plt.subplots(nrows, panel_columns, figsize=size, sharex=shared_axes, sharey=True, squeeze=False)
    fig.subplots_adjust(left=.068, right=.984, top=.713 if subsequence else .826,
                        bottom=.205 if subsequence else .120, wspace=.15, hspace=.59)
    fig.text(.068, .956, title, fontsize=23, fontweight='bold', va='top')
    fig.text(.068, .872 if subsequence else .910,
             subtitle, fontsize=10.5, color=MUTED, va='top')

    for axis, note in zip(axs.flat, notes):
        x, y, values = panels[note]
        axis.pcolormesh(x, y, values, cmap=COLORS, norm=NORM, shading='flat',
                        edgecolors='none' if shared_axes else '#FFFFFF',
                        linewidth=0. if shared_axes else .32, antialiased=False)
        points = [row for row in validation if row['note']==note]
        for hit, mark in ((True,'o'),(False,'x')):
            subset = [row for row in points if (row['outcome']=='target')==hit]
            if not subset:
                continue
            xs = [row['lip_frequency_hz'] for row in subset]
            ys = [row['blowing_pressure_pa']/1000 for row in subset]
            if hit:
                axis.scatter(xs,ys,s=15,marker=mark,facecolor='white',edgecolor=TEXT,
                             linewidth=1.0,zorder=3)
            else:
                axis.scatter(xs,ys,s=14,marker=mark,color='white',linewidth=2.7,zorder=3)
                axis.scatter(xs,ys,s=14,marker=mark,color=TEXT,linewidth=1.15,zorder=4)
        if log_hz:
            set_log_ticks(axis)
        axis.set_xlim((xmin, xmax) if shared_axes else (x[0], x[-1]))
        axis.set_ylim(ymin, ymax)
        if log_hz:
            target_hz = selected[note][0]['target_hz']
            draw_target_marker(axis, target_hz)
        axis.set_facecolor('white')
        counted = Counter(row['outcome'] for row in selected[note])
        detail = (panel_details or {}).get(note)
        heading_y = 1.145 if detail else 1.066
        axis.text(0., heading_y, f'{label(note)}  ·  {pitch(note):.0f} Hz',
                  transform=axis.transAxes, ha='left', fontsize=11.1, fontweight='bold', va='bottom')
        axis.text(1., heading_y, f'{counted["target"]}/{len(selected[note])}',
                  transform=axis.transAxes, fontsize=9.6, ha='right', color=MUTED, va='bottom')
        if detail:
            axis.text(0., 1.042, detail, transform=axis.transAxes,
                      fontsize=8.4, color=MUTED, ha='left', va='bottom')
        if shared_axes:
            if not log_hz:
                axis.xaxis.set_major_locator(MultipleLocator(x_tick_hz))
            axis.yaxis.set_major_locator(MultipleLocator(5))
            axis.tick_params(axis='x', labelbottom=True)
            axis.set_axisbelow(True)
            axis.grid(color='#E9EDF2', linewidth=.6)
        else:
            axis.xaxis.set_major_locator(MaxNLocator(nbins=5, steps=(1, 2, 2.5, 3, 4, 5, 6, 8, 10), integer=True))
            axis.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=(1, 2, 2.5, 5, 10)))
        axis.xaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))
        axis.tick_params(axis='both', labelsize=9.3, length=3.0, pad=3.5)
        # The labels above the panel show the equal-tempered sounding pitch;
        # the horizontal coordinate always denotes the model lip frequency.

    for axis in list(axs.flat)[count:]:
        axis.set_visible(False)

    xlabel = '唇の固有振動数（Hz、対数軸）' if log_hz else '唇の固有振動数（Hz）'
    fig.supxlabel(xlabel, y=.114 if subsequence else .068, fontsize=12.2)
    fig.supylabel('定常吹奏圧（kPa）', x=.012, fontsize=12.2)
    states_present = {row['outcome'] for rows in selected.values() for row in rows}
    handles = [
        Patch(facecolor=color, edgecolor='none', label=description)
        for state, (description, color) in OUTCOMES.items() if state in states_present
    ]
    if shared_axes or any(np.isnan(values).any() for _, _, values in panels.values()):
        handles.append(Patch(facecolor='#FFFFFF', edgecolor=RULE, label='未計算'))
    if validation:
        handles.extend([
            Line2D([],[],linestyle='none',marker='o',markerfacecolor='white',
                   markeredgecolor=TEXT,markersize=5.4,label='非線形計算で目標音'),
            Line2D([],[],linestyle='none',marker='x',color=TEXT,markersize=5.4,
                   label='非線形計算で目標外'),
        ])
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(.066, .829 if subsequence else .892),
               borderaxespad=0., ncol=len(handles), frameon=False, fontsize=9.6,
               handlelength=1.25, handleheight=.9, columnspacing=1.65)
    footer = ('白は未計算。右上は緑の試行数／全試行数。すべて同じ軸範囲と目盛りです。' if shared_axes else
              '1マスは1試行。右上は緑の試行数／全試行数。横軸の周波数範囲は音ごとに異なります。')
    fig.text(.068, .032 if subsequence else .018, footer, fontsize=9.0, color=MUTED)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    for format in ('png', 'svg'):
        fig.savefig(prefix.with_suffix('.' + format), dpi=230)
    plt.close(fig)
