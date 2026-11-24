"""Sweep cold-start playability of the ten published brass instruments."""

from argparse import ArgumentParser
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import cache
import json
from pathlib import Path

from axisymmetric_cuda import Device, Run, TRUMPET_LIPS
import flugelhorn_axisymmetric as flugelhorn
import playability_bore as bore
import playability_lips as lips
import render_euphonium_ophicleide as scales
import render_trombone_detailed_scale as trombone_scale
import render_trumpet_bach5c as trumpet_scale
import render_tuba_scale as tuba_scale
import serpent_axisymmetric as serpent
import trombone_axisymmetric as trombone
import tuba_axisymmetric as tuba
from trumpet import ROOT, np, signal

LABELS = {
    'trumpet': 'トランペット', 'flugelhorn': 'フリューゲルホルン', 'trombone': 'トロンボーン',
    'horn': 'F／B♭ダブルホルン', 'euphonium': 'ユーフォニアム', 'ophicleide': 'B♭管オフィクレイド',
    'tuba': 'BB♭チューバ', 'tenor_horn': 'E♭テナーホルン',
    'keyed_bugle': 'B♭キー付きビューグル', 'serpent': 'C管セルパン',
}
TRIMS = {
    'trumpet': -.023, 'flugelhorn': -.075, 'trombone': -.067, 'horn': {'F': -.10, 'Bb': -.025},
    'euphonium': -.075, 'ophicleide': -.040, 'tuba': -.050, 'tenor_horn': -.050,
    'keyed_bugle': -.090, 'serpent': 0.,
}
SLIDE_POSITIONS = (1, 6, 4, 3, 1, 4, 2, 1, 3, 1, 3, 1, 4, 2, 1)
EXTERIOR_TRANSFER_MODELS = ('trumpet', 'flugelhorn', 'trombone')
DEFAULT_MODEL = dict(thermoviscous=True, radiation_order=2, reservoir_inflow=True)
VALIDATION_NOTES = {
    'trumpet': ('Bb3', 'Bb4', 'Bb5'), 'flugelhorn': ('Bb3', 'Bb4', 'Bb5'),
    'trombone': ('Bb2', 'Bb3', 'Bb4'), 'horn': ('Bb1', 'Bb2', 'Bb3', 'Bb4'),
    'euphonium': ('Bb1', 'Bb2', 'Bb3', 'Bb4'), 'ophicleide': ('Bb1', 'Bb2', 'Bb3', 'Bb4'),
    'tuba': ('Bb1', 'Bb3', 'C4', 'Bb4'), 'tenor_horn': ('Bb2', 'Bb3', 'C4', 'Bb5'),
    'keyed_bugle': ('Bb3', 'C4', 'Bb5'), 'serpent': ('C2', 'D3', 'Bb3', 'C4'),
}


@dataclass(frozen=True)
class Instrument:
    name: str
    notes: dict[str, dict]
    selectors: dict[str, dict]
    geometry: Callable[[tuple], tuple]
    lip_model: dict
    model: dict
    min_pitch_hz: float
    min_peak_hz: float

    def is_planar(self, note):
        return self.name == 'serpent' or (self.name == 'tuba' and note == 'C2')

    def config(self, note):
        return tuple(self.selectors[note].items())

    def directory(self, root):
        if self.name == 'trumpet':
            return root / 'trumpet_playability'
        return root / 'brass_playability' / self.name

    def report_path(self, root):
        name = 'planar' if self.name == 'serpent' else self.name
        return self.directory(root) / f'{name}_playability.json'


def instrument_notes(name):
    data = ROOT / 'data'
    path = data / f'performance_{name}.json'
    if name == 'trumpet':
        return trumpet_scale.settings()[:15]
    if name == 'trombone':
        return [row | {'position': pos}
                for row, pos in zip(trombone_scale.settings(), SLIDE_POSITIONS)]
    if name == 'tuba':
        return list(tuba_scale.settings(path))
    if name == 'serpent':
        chart = json.loads((data / 'serpent_fingerings.json').read_bytes())['notes']
        played = {row['note']: row for row in json.loads((data / 'performance_serpent_tuned.json').read_bytes())}
        included = played.keys() | {'Bb2', 'Bb3'}
        return [
            row | {'target_hz': 440 * 2**((row['midi']-69)/12)}
            for row in chart if row['note'] in included
        ]
    upper_midi = 82 if name in ('flugelhorn', 'tenor_horn', 'keyed_bugle') else 70
    return [row for row in scales.settings(name, path, extended=name == 'euphonium')
            if row['midi'] <= upper_midi]


def setup_instrument(name):
    notes = {row['note']: row for row in instrument_notes(name)}
    trims = TRIMS[name]
    selector_key = {
        'trumpet': 'valves_semitones', 'trombone': 'position',
        'serpent': 'open_holes', 'keyed_bugle': 'open_holes', 'ophicleide': 'open_holes',
    }.get(name, 'valves')
    selectors = {}
    for note, row in notes.items():
        selector = row[selector_key]
        trim = trims[row['side']] if name == 'horn' else trims
        selectors[note] = {
            selector_key: selector if name == 'trombone' else tuple(sorted(selector)),
            'trim_m': trim,
        }
        if name == 'horn':
            selectors[note]['side'] = row['side']

    if name == 'trumpet':
        lip_model = TRUMPET_LIPS | trumpet_scale.MODEL.get('lip_parameters', {})
    elif name == 'tuba':
        lip_model = tuba_scale.LIPS
    else:
        lip_model = scales.instrument_module(name).LIPS

    @cache
    def geometry(config):
        setup = dict(config)
        selector = setup[selector_key]
        trim = setup['trim_m']
        if name == 'trumpet':
            _, mesh = trumpet_scale.physical_note(dict(valves_semitones=selector, tuning_m=trim))
        elif name == 'flugelhorn':
            mesh = flugelhorn.refined_flugelhorn_mesh(selector, tuning=trim)
        elif name == 'trombone':
            mesh = trombone.refined_trombone_mesh(selector, tuning=trim)
        elif name == 'tuba':
            mesh = tuba.refined_tuba_mesh(selector, tuning=trim, dr=.0075)
        elif name == 'serpent':
            mesh = serpent.refined_serpent_mesh(selector, tuning=trim)
        else:
            mesh = scales.make_grid(name, setup)
        load = scales.instrument_load(name, mesh, setup)
        return mesh, load, lip_model | {'cup_area': float(np.pi * mesh['radius'][0]**2)}

    min_pitch = {'trumpet': 60., 'flugelhorn': 60., 'trombone': 32.}.get(name, 18.)
    min_peak = {'trumpet': 55., 'flugelhorn': 55., 'trombone': 28.}.get(name, 18.)
    model = trumpet_scale.MODEL if name == 'trumpet' else DEFAULT_MODEL
    return Instrument(name, notes, selectors, geometry, lip_model, model, min_pitch, min_peak)


def save_json(path, data):
    pending = path.with_suffix('.writing')
    pending.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    pending.replace(path)


def return_filter(instrument, note, root, gpu):
    directory = instrument.directory(root)
    directory.mkdir(parents=True, exist_ok=True)
    config = instrument.config(note)
    route = tuple(instrument.selectors[note].values())
    ports = route[0]
    selector = str(ports) if isinstance(ports, int) else ('-'.join(map(str, ports)) or 'open')
    side = instrument.selectors[note].get('side', 'open')
    trim = instrument.selectors[note]['trim_m']
    planar = instrument.is_planar(note)
    path = directory / f'return_v1_{side}_{selector}_{trim:+.5f}_{"planar" if planar else "pulse"}.npz'
    if not path.is_file():
        mesh, load, _ = instrument.geometry(config)
        if planar:
            data = bore.plane_wave_response(mesh, load, instrument.min_peak_hz,
                                            tuba_c2=instrument.name == 'tuba')
        else:
            data = bore.weak_pulse_response(gpu(), mesh, load, instrument.min_peak_hz,
                                             trumpet_profile=instrument.name in EXTERIOR_TRANSFER_MODELS)
        pending = path.with_suffix('.pending.npz')
        np.savez(pending, **data)
        pending.replace(path)
    with np.load(path) as data:
        return {key: data[key] for key in data.files}


def metadata(instrument):
    name = instrument.name
    data = dict(
        instrument=name, instrument_label=LABELS[name], selector_by_note=instrument.selectors,
        lip_model=instrument.lip_model, sample_rate_hz=bore.FS, duration_s=lips.DURATION,
        steady_windows_s=lips.WINDOWS, cup_rms_min_pa=lips.CUP_RMS_MIN,
        pitch_tolerance_cents=lips.PITCH_TOLERANCE_CENTS, lowest_pitch_hz=instrument.min_pitch_hz,
        rest_y_m=lips.REST, attack_s=lips.ATTACK, attack_boost=lips.BOOST, attack_decay_s=lips.DECAY,
        tuning_m=TRIMS[name],
    )
    if name == 'serpent':
        data['linear_return_source'] = 'plane-wave transfer matrices with bore and shunt losses, full frequency band'
    else:
        data['linear_return_blended_with_tmm_hz'] = [2500, 5000]
    if name == 'tuba':
        data['C2_filter_correction'] = 'passive plane-wave transfer matrices, full band'
    return data


def map_instrument(instrument, notes, root, workers, gpu):
    path = instrument.report_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep already completed notes when rerunning a subset or resuming a stopped sweep.
    old = json.loads(path.read_bytes()) if path.is_file() else {}
    report = dict(notes=[], rows=[], summaries=[], metadata=metadata(instrument))
    report['rows'].extend(old.get('rows', []))
    report['summaries'].extend(old.get('summaries', []))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for note in notes:
            response = return_filter(instrument, note, root, gpu)
            _, _, physical_lips = instrument.geometry(instrument.config(note))
            fs, zc = int(response['fs']), float(response['zc'])
            target = instrument.notes[note]['target_hz']
            frequencies = [round(float(target * ratio), 5) for ratio in lips.LIP_RATIOS]
            conditions = [(frequency, float(pressure)) for pressure in lips.PRESSURES for frequency in frequencies]

            def run(condition):
                frequency, pressure = condition
                wave = lips.coupled_cup(
                    response['fir'], zc, lips.DURATION, fs, frequency, pressure,
                    lips.REST, lips.ATTACK, lips.BOOST, lips.DECAY,
                    *(physical_lips[key] for key in lips.LIP_KEYS),
                    physical_lips.get('gap_frequency_ratio', 1.),
                    physical_lips.get('gap_cubic_per_m2', 0.),
                )
                return lips.evaluate(note, target, frequency, pressure, wave, fs,
                                     response['peaks'], instrument.min_pitch_hz)

            first = run(conditions[0])
            rows = [first, *pool.map(run, conditions[1:])]
            summary = lips.summarize(note, target, instrument.selectors[note], rows)
            report['rows'] = [row for row in report['rows'] if row['note'] != note] + rows
            report['summaries'] = [row for row in report['summaries'] if row['note'] != note] + [summary]
            completed = {row['note'] for row in report['summaries']}
            report['notes'] = [name for name in instrument.notes if name in completed]
            save_json(path, report)
            print(instrument.name, note, summary['counts'], summary['first_success_pressure_pa'], flush=True)


def choose_validation_trials(rows):
    success = [row for row in rows if row['outcome'] == 'target']
    if not success:
        return [min(rows, key=lambda row: abs(row['lip_frequency_hz']/row['target_hz'] - 1)
                                         + abs(row['blowing_pressure_pa'] - 7000)/5000)]
    pressure = min(row['blowing_pressure_pa'] for row in success)
    first = min((row for row in success if row['blowing_pressure_pa'] == pressure),
                key=lambda row: abs(row['pitch_error_cents']))
    settled_pressure = min((row['blowing_pressure_pa'] for row in success),
                           key=lambda value: abs(value - pressure - 3500))
    at_pressure = [row for row in success if row['blowing_pressure_pa'] == settled_pressure]
    center = min(at_pressure, key=lambda row: abs(row['lip_frequency_hz']
                 - np.median([item['lip_frequency_hz'] for item in at_pressure])))
    return [first, center] if first != center else [first]


def validate(instrument, notes, root, gpu):
    report_path = instrument.report_path(root)
    if not report_path.exists():
        raise ValueError(f'Sweep required before validation: {report_path}')
    data = json.loads(report_path.read_bytes())
    missing = set(notes) - set(data['notes'])
    if missing:
        raise ValueError(f'Sweep required before validation: {", ".join(sorted(missing))}')
    path = report_path.with_name(report_path.stem.removesuffix('_playability') + '_validation.json')
    validation = json.loads(path.read_bytes())['validation'] if path.is_file() else []
    for note in notes:
        response = return_filter(instrument, note, root, gpu)
        mesh, load, physical_lips = instrument.geometry(instrument.config(note))
        model = instrument.model | {'lip_parameters': physical_lips}
        rows = [row for row in data['rows'] if row['note'] == note]
        for trial in choose_validation_trials(rows):
            frequency = trial['lip_frequency_hz']
            pressure = trial['blowing_pressure_pa']
            guard = 1.63 if pressure < 8000 else 1.85 if pressure < 14000 else 2.08
            trace_fs = 96000
            for attempt in range(2):
                try:
                    with Run(gpu(), mesh, lips.DURATION, lip_hz=frequency, pressure=pressure,
                             rest_y=lips.REST, attack=lips.ATTACK, attack_boost=lips.BOOST,
                             attack_decay=lips.DECAY, guard=guard, hold=lips.DURATION,
                             trace_fs=trace_fs, exterior_load=load, **model) as sim:
                        sim.until()
                        cup = signal.resample_poly(sim.history()[:, 0], 1, trace_fs//bore.FS)
                    break
                except (RuntimeError, ValueError) as error:
                    if attempt or not any(term in str(error).lower() for term in ('guard', 'speed')):
                        raise
                    guard += .4
            result = lips.evaluate(note, trial['target_hz'], frequency, pressure, cup, bore.FS,
                                   response['peaks'], instrument.min_pitch_hz)
            result.update(predicted_outcome=trial['outcome'], predicted_frequency_hz=trial['audio_frequency_hz'])
            coordinates = ('note', 'lip_frequency_hz', 'blowing_pressure_pa')
            validation = [old for old in validation if not all(old[key] == result[key] for key in coordinates)]
            validation.append(result)
            save_json(path, dict(validation=validation, device=gpu().name))
            print(instrument.name, note, frequency, pressure, trial['outcome'], result['outcome'], flush=True)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('instrument', choices=(*LABELS, 'all'))
    parser.add_argument('--phase', choices=('sweep', 'validate'), default='sweep')
    parser.add_argument('--notes', nargs='+', metavar='NOTE', help='Use sounding note names such as Bb3 or C4.')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--output-root', type=Path, default=ROOT / 'output')
    args = parser.parse_args()
    if args.workers < 1:
        parser.error('--workers must be positive')
    if args.notes and (args.instrument == 'all' or len(set(args.notes)) != len(args.notes)):
        parser.error('--notes requires one instrument and distinct notes')

    @cache
    def gpu():
        return Device()

    for name in (LABELS if args.instrument == 'all' else (args.instrument,)):
        instrument = setup_instrument(name)
        defaults = VALIDATION_NOTES[name] if args.phase == 'validate' else instrument.notes
        notes = args.notes or tuple(defaults)
        unknown = set(notes) - instrument.notes.keys()
        if unknown:
            parser.error(f'{name}: unknown notes {", ".join(sorted(unknown))}')
        if args.phase == 'validate':
            validate(instrument, notes, args.output_root, gpu)
        else:
            map_instrument(instrument, notes, args.output_root, args.workers, gpu)


if __name__ == '__main__':
    main()
