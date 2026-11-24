"""Plot sustained cup-pressure oscillation frequencies from the archived sweep."""
from collections import defaultdict
import math

from matplotlib import colormaps
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, StrMethodFormatter
import numpy as np

import playability_maps as maps


PRESSURE_CMAP = colormaps['cividis']
PRESSURE_NORM = Normalize(vmin=0.5, vmax=22.0)
REFERENCE_STYLE = dict(color=maps.TEXT, linestyle=(0, (4, 3)), linewidth=1.0)
LEGEND_HANDLES = (
    Line2D([], [], marker='o', linestyle='none', markersize=4, color=maps.TEXT,
           label='目標音程の範囲内'),
    Line2D([], [], marker='^', linestyle='none', markersize=4, color=maps.TEXT,
           label='目標音程の範囲外'),
    Line2D([], [], label='目標音と同じ唇固有振動数', **REFERENCE_STYLE),
)


def add_pressure_key(fig, bounds):
    axis = fig.add_axes(bounds)
    scale = ScalarMappable(norm=PRESSURE_NORM, cmap=PRESSURE_CMAP)
    key = fig.colorbar(scale, cax=axis, orientation='horizontal', ticks=[0.5, 5, 10, 15, 22])
    key.ax.xaxis.set_major_formatter(StrMethodFormatter('{x:g}'))
    key.ax.set_title('吹奏圧（kPa）', loc='left', fontsize=9, color=maps.MUTED, pad=3)
    key.ax.tick_params(labelsize=8.3, width=.55, length=2.4, pad=2.7)
    key.outline.set_linewidth(.55)
    return key


def stable_trials(rows):
    for row in rows:
        if row['outcome'] in ('target', 'other'):
            frequency = row['audio_frequency_hz']
            if frequency is None or not math.isfinite(frequency) or frequency <= 0.:
                raise ValueError(f"A stable {row['note']} trial is missing a positive measured frequency.")
            yield row


def draw_panel(axis, rows, target_hz, xlim, *, ylim=None):
    """Draw each sustained trial at its own lip and measured frequency."""
    positions = defaultdict(list)
    for row in stable_trials(rows):
        positions[row['outcome']].append((
            row['lip_frequency_hz'], row['audio_frequency_hz'], row['blowing_pressure_pa'] / 1000,
        ))

    maps.set_log_ticks(axis)
    axis.set_xlim(*xlim)
    axis.set_axisbelow(True)
    axis.grid(color='#E9EDF2', linewidth=.62)
    axis.tick_params(axis='both', labelsize=8.8, length=3, pad=3)
    axis.tick_params(axis='x', which='minor', length=1.8)
    axis.yaxis.set_major_locator(MaxNLocator(nbins=4))
    axis.axvline(target_hz, zorder=2.5, **REFERENCE_STYLE)
    for outcome, marker, size, opacity in (('other', '^', 6., .73), ('target', 'o', 6., .88)):
        if positions[outcome]:
            x, y, pressure = np.asarray(positions[outcome], dtype=float).T
            axis.scatter(x, y, c=pressure, cmap=PRESSURE_CMAP, norm=PRESSURE_NORM,
                         marker=marker, s=size, linewidths=0, alpha=opacity, zorder=3)
    if ylim is None:
        values = [point[1] for run in positions.values() for point in run] + [target_hz]
        low, high = min(values), max(values)
        margin = max(3., .055 * (high - low))
        ylim = (max(0., low - margin), high + margin)
    axis.set_ylim(*ylim)
    return sum(map(len, positions.values()))


def group_rows(datasets):
    grouped = defaultdict(list)
    for key in datasets:
        for row in datasets[key]['rows']:
            grouped[key, row['note']].append(row)
    return grouped


def style_plate(fig, title, subtitle, *, common_ymax=None):
    fig.text(.071, .968, title, fontsize=23, fontweight='bold', va='top')
    fig.text(.071, .926, subtitle, fontsize=10.3, color=maps.MUTED, va='top')
    fig.legend(handles=LEGEND_HANDLES, loc='upper left', bbox_to_anchor=(.067, .886),
               ncol=3, frameon=False, fontsize=9.3, borderaxespad=0, columnspacing=1.65)
    add_pressure_key(fig, [.735, .875, .234, .015])
    fig.supxlabel('唇の固有振動数（Hz、対数軸）', y=.044, fontsize=12.2)
    fig.supylabel('カップ内圧の発振周波数（Hz）', x=.012, fontsize=12.2)
    if common_ymax is None:
        scale_note = '縦軸の範囲は音ごとに異なります。'
    else:
        scale_note = f'縦軸は全楽器で0〜{common_ymax:g} Hz。'
    footer = scale_note + '点は測定窓で安定した発振のみ。'
    fig.text(.071, .015, footer, fontsize=8.8, color=maps.MUTED)


def save(fig, prefix, *, dpi=220):
    for extension in ('.png', '.svg'):
        fig.savefig(prefix.with_suffix(extension), dpi=dpi)
    maps.plt.close(fig)


def draw_all(datasets, instruments, output, xlim):
    """Save ten per-instrument plates and a common-C4 plate in both formats."""
    output.mkdir(parents=True, exist_ok=True)
    grouped = group_rows(datasets)
    subtitle = (f'横軸は{xlim[0]:g}〜{xlim[1]:,.3f} Hz。縦軸は持続部で測った発振周波数。'
                '目標音程の範囲は±75セント。')
    for key, name, _ in instruments:
        notes = datasets[key]['notes']
        nrow = math.ceil(len(notes) / 5)
        fig, axes = maps.plt.subplots(nrow, 5, figsize=(16.8, 3 + nrow * 2.35),
                                     sharex=True, squeeze=False)
        fig.subplots_adjust(left=.074, right=.983, top=.814, bottom=.101, wspace=.30, hspace=.53)
        style_plate(fig, f'{name}の発振周波数', subtitle)
        for axis, note in zip(axes.flat, notes):
            rows = grouped[key, note]
            target_hz = float(rows[0]['target_hz'])
            count = draw_panel(axis, rows, target_hz, xlim)
            axis.tick_params(axis='x', labelbottom=True)
            axis.set_title(f'{maps.label(note)}  ·  {target_hz:.0f} Hz',
                           loc='left', fontsize=11, fontweight='bold', pad=6)
            axis.set_title(f'{count} 点', loc='right', fontsize=8.3, color=maps.MUTED, pad=6)
        for axis in list(axes.flat)[len(notes):]:
            axis.set_visible(False)
        stem = f'{key}_observed_frequency'
        save(fig, output / stem)

    fig, axes = maps.plt.subplots(2, 5, figsize=(16.8, 7.4), sharex=True, sharey=True)
    fig.subplots_adjust(left=.074, right=.983, top=.807, bottom=.124, wspace=.18, hspace=.52)
    highest_c4 = max((row['audio_frequency_hz'] for key, _, _ in instruments
                      for row in stable_trials(grouped[key, 'C4'])), default=0.)
    ymax = max(450, 50 * math.ceil(highest_c4 / 50))
    style_plate(fig, '実音C4の発振周波数を10楽器で比較', subtitle, common_ymax=ymax)
    for axis, (key, name, _) in zip(axes.flat, instruments):
        rows = grouped[key, 'C4']
        target_hz = float(rows[0]['target_hz'])
        draw_panel(axis, rows, target_hz, xlim, ylim=(0, ymax))
        axis.tick_params(axis='x', labelbottom=True)
        axis.set_title(name, loc='left', fontsize=10.7, fontweight='bold', pad=6)
    stem = 'allbrass_c4_observed_frequency'
    save(fig, output / stem)


def draw_tenor_example(data, output, limits):
    xlim, pressure_limits = limits
    note = 'C4'
    rows = [row for row in data['tenor_horn']['rows'] if row['note'] == note]
    target = rows[0]['target_hz']
    lip = 287.78812
    reference_pressures = (3000., 3500.)
    points = sorted(
        (row for row in rows if row['lip_frequency_hz'] == lip
         and row['blowing_pressure_pa'] in reference_pressures),
        key=lambda row: row['blowing_pressure_pa'],
    )
    if [row['outcome'] for row in points] != ['other', 'target']:
        raise ValueError('The archived tenor horn C4 example is missing its two reference trials.')

    fig, (left, right) = maps.plt.subplots(1, 2, figsize=(13.4, 6.15))
    fig.subplots_adjust(left=.09, right=.967, top=.72, bottom=.255, wspace=.26)
    fig.text(.087, .95, 'E♭テナーホルン C4の発音範囲と発振周波数',
             va='top', fontsize=22, fontweight='bold')
    fig.text(.087, .865,
             f'縦の破線は目標音C4（{target:.2f} Hz）。AとBの唇の固有振動数はどちらも{lip:.2f} Hz。',
             va='top', fontsize=10.7, color=maps.MUTED)
    x, y, values = maps.panel_data(note, rows)
    left.pcolormesh(x, y, values, cmap=maps.COLORS, norm=maps.NORM, shading='flat',
                    edgecolors='none', antialiased=False)
    maps.set_log_ticks(left)
    left.set_xlim(*xlim)
    left.set_ylim(*pressure_limits)
    left.yaxis.set_major_locator(maps.MultipleLocator(5))
    left.set_axisbelow(True)
    left.grid(color='#E9EDF2', linewidth=.65)
    left.set_ylabel('定常吹奏圧（kPa）', fontsize=11)
    left.set_title('吹奏圧と発音判定', loc='left', fontsize=13, pad=9, fontweight='bold')
    maps.draw_target_marker(left, target)
    pressure_kpa = [row['blowing_pressure_pa'] / 1000 for row in points]
    left.plot([lip, lip], pressure_kpa, marker='o', color=maps.TEXT, markerfacecolor='white',
              linewidth=1.5, markersize=4, zorder=6)
    middle_pressure = sum(pressure_kpa) / len(pressure_kpa)
    arrow = {'arrowstyle': '-', 'color': maps.MUTED, 'linewidth': 1.}
    text_box = {'fc': 'white', 'ec': 'none', 'alpha': .93, 'pad': 2.}
    left.annotate('A・Bの吹奏圧', (lip, middle_pressure), xytext=(.70, .36),
                  textcoords='axes fraction', arrowprops=arrow, fontsize=10.3, bbox=text_box, zorder=8)

    draw_panel(right, rows, target, xlim, ylim=(0, 450))
    right.set_title('安定発振時の周波数', loc='left', fontsize=13, pad=9, fontweight='bold')
    right.set_ylabel('発振周波数（Hz）', fontsize=11)
    for i, (tag, row) in enumerate(zip(('A', 'B'), points)):
        hz = row['audio_frequency_hz']
        kpa = row['blowing_pressure_pa'] / 1000
        right.scatter([lip], [hz], s=50, marker='s', facecolors='none', edgecolors=maps.TEXT,
                      linewidths=1.2, zorder=9)
        right.annotate(f'{tag}   {kpa:g} kPaで {hz:.2f} Hz', (lip, hz),
                       xytext=(.72, .16 + i * .52), textcoords='axes fraction', zorder=10,
                       fontsize=10.3, arrowprops=arrow, bbox=text_box)
    fig.supxlabel('唇の固有振動数（Hz、対数軸）', y=.162, fontsize=11.8)
    add_pressure_key(fig, [.65, .129, .284, .017])
    fig.text(.087, .036, '左の緑は目標の±75セント以内。右の○は範囲内、△は範囲外。',
             color=maps.MUTED, fontsize=9.7)
    save(fig, output / 'tenor_horn_c4_pressure_and_frequency', dpi=230)
