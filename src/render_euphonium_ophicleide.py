"""Render forte B-flat major scales with coupled lips, bore, bell, and side holes."""
import argparse
from functools import cache
import hashlib
import importlib
import json
import os
from pathlib import Path
import tempfile
import time

from axisymmetric_cuda import Device, Run
from compare_trumpet_bell import harmonic_rms, write_wav
from render_trumpet_bell import build_load
from render_tuba_scale import AUDIO_FS, GAP, MODEL, PITCH_RANGE, TRACE_FS, inspect
from trumpet import C, RHO, ROOT, measure, np, signal

HIGH_BRASS = ('flugelhorn','keyed_bugle')
NAMES = ('euphonium','ophicleide','horn',*HIGH_BRASS)
RANGES = dict(euphonium=(2,5),ophicleide=(1,4),horn=(1,5),flugelhorn=(3,6),keyed_bugle=(3,6))
SELECTOR = dict(euphonium='valves',ophicleide='open_holes',horn='valves',
                flugelhorn='valves',keyed_bugle='open_holes')
HIGH_BRASS_PITCH_RANGE = dict(min_hz=46.,max_hz=2450.)
RADIAL_STEP = .006
START_PILOT_S = .44
NOTE_DURATION_S = 1.08
LAST_DURATION_S = 1.65
EUPHONIUM_PEDALS = ROOT/'data/performance_euphonium_pedal.json'


def note_names(instrument, *, extended=False):
    bottom,top = RANGES[instrument]
    if extended:
        bottom = 1
    return (f'Bb{bottom}',)+tuple(f'{name}{octave}' for octave in range(bottom+1,top+1)
                                  for name in ('C','D','Eb','F','G','A','Bb'))


def settings(instrument,preset, *, extended=False):
    notes = note_names(instrument,extended=extended)
    rows = json.loads(preset.read_text(encoding='utf-8'))
    if extended and len(rows)==len(note_names(instrument)):
        rows = json.loads(EUPHONIUM_PEDALS.read_text(encoding='utf-8'))+rows
    by_name = {row['note']:row for row in rows}
    if len(rows)!=len(notes) or set(notes)!=set(by_name):
        raise ValueError(f'Use exactly the {len(notes)} notes in the B-flat major scale.')
    bottom_midi = 22+12*int(notes[0][-1])
    octaves = len(notes)//7
    intervals = tuple(12*octave+step for octave in range(octaves)
                      for step in (0,2,4,5,7,9,11))+(12*octaves,)
    for name,semitones in zip(notes,intervals):
        midi = bottom_midi+semitones
        yield dict(attack_s=.0065,attack_boost=.45,attack_decay_s=.028,rest_y_m=0.,
                   trim_m=0.,wave_speed_reserve=1.66,lip_parameters={}) | by_name[name] | {
            'midi':midi,'target_hz':440*2**((midi-69)/12),
        }


@cache
def instrument_module(instrument):
    return importlib.import_module(f'{instrument}_axisymmetric')


def output_dir(instrument):
    return ROOT/'output'/f'{instrument}_axisymmetric'


@cache
def signature(instrument):
    names = (
        'axisymmetric_cuda.py','axisymmetric_euler.cu','axisymmetric_mesh.py','thermoviscous.py',
        'bell_exterior.py','render_trumpet_bell.py','render_tuba_scale.py','trumpet.py',
        'render_bidirectional.py','compare_trumpet_bell.py','render_euphonium_ophicleide.py',
        f'{instrument}_axisymmetric.py',
    )
    if instrument=='horn':
        names += ('horn_bell.py',)
    return hashlib.sha256(b''.join((ROOT/'src'/name).read_bytes() for name in names)).digest()


def make_grid(instrument,note):
    model = instrument_module(instrument)
    mesh = getattr(model,f'refined_{instrument}_mesh')
    selector = 'open_holes' if instrument=='serpent' else SELECTOR[instrument]
    fingers = (tuple(note[selector]),)
    if instrument=='horn':
        fingers = (note['side'],)+fingers
    partial_holes = {'opening_fractions':note['opening_fractions']} if (
        instrument=='serpent' and note.get('opening_fractions')) else {}
    return mesh(*fingers,tuning=note['trim_m'],**partial_holes,
                axial_scale=note.get('axial_scale',1.),dr=note.get('radial_spacing_m',RADIAL_STEP))


def instrument_load(instrument,grid,note):
    if instrument=='horn':
        from horn_bell import build_horn_load

        if 'open_area_fraction' in note:
            return build_horn_load(grid,open_area_fraction=note['open_area_fraction'])
        return build_horn_load(grid)
    return build_load(grid)


def higher_harmonic(wave,fs,period,target):
    """Resolve a near-target carrier if a weaker multi-cycle modulation is present."""
    if not period:
        return None
    factor = round(target/period)
    if factor not in (2,3,4) or not .96<factor*period/target<1.04:
        return None
    harmonics = harmonic_rms(wave,fs,period,8*factor)
    target_level = max((h['rms_pa'] for h in harmonics if h['order']%factor==0),default=0.)
    other = max((h['rms_pa'] for h in harmonics if h['order']%factor),default=0.)
    if target_level and other/target_level<.15:
        return other/target_level
    return None


def hole_pressure(flows,positions,bell_z,bell_r):
    """Free-field monopoles with arrival times referred to the bell receiver."""
    samples = np.arange(len(flows))/TRACE_FS
    pressure = np.zeros(len(samples))
    for column,z in enumerate(positions):
        distance = 1.+bell_z-z
        delay = (distance-1.+bell_r)/C
        derivative = np.gradient(flows[:,column],1/TRACE_FS)
        pressure += RHO/(4*np.pi*distance)*np.interp(samples-delay,samples,derivative,left=0.)
    return pressure


def solve(device,instrument,note,duration,initial_check=True):
    grid = make_grid(instrument,note)
    cup_area = float(np.pi*grid['radius'][0]**2)
    lips = instrument_module(instrument).LIPS | note['lip_parameters'] | {'cup_area':cup_area}
    holes = grid.get('toneholes',())
    path = output_dir(instrument)/'cache'
    os.makedirs(path,exist_ok=True)
    key = hashlib.sha256(signature(instrument)+json.dumps([note,lips,MODEL,duration],sort_keys=True).encode())
    for name in ('z','radius','rings'):
        key.update(grid[name].tobytes())
    if len(holes):
        key.update(np.asarray(holes).tobytes())
    cache_file = path/f"{note['note']}_{key.hexdigest()[:16]}.npz"
    if cache_file.exists():
        with np.load(cache_file) as saved:
            return saved['wave'],json.loads(str(saved['row']))

    began = time.perf_counter()
    pitch_range = HIGH_BRASS_PITCH_RANGE if instrument in HIGH_BRASS else PITCH_RANGE
    load = instrument_load(instrument,grid,note)
    side_channels = {'record_toneholes':True} if len(holes) else {}
    with Run(device,grid,duration,lip_hz=note['lip_frequency_hz'],
             pressure=note['blowing_pressure_pa'],rest_y=note['rest_y_m'],
             attack=note['attack_s'],attack_boost=note['attack_boost'],
             attack_decay=note['attack_decay_s'],guard=note['wave_speed_reserve'],
             hold=duration-.16 if duration>.8 else duration,release=.078,
             lip_parameters=lips,exterior_load=load,record_bell=True,**MODEL,**side_channels) as run:
        if initial_check and duration>.8:
            run.until(START_PILOT_S)
            trace = run.history()
            pilot = measure(trace,fs=TRACE_FS,start=.27,**pitch_range)
            frequency = pilot['frequency']
            if higher_harmonic(trace[round(.27*TRACE_FS):,0],TRACE_FS,frequency,note['target_hz']) is not None:
                frequency *= round(note['target_hz']/frequency)
            if pilot['rms']<24. or not .952<frequency/note['target_hz']<1.049:
                raise ValueError(f"Attack reached {frequency:.2f} Hz, {pilot['rms']:.1f} Pa cup RMS")
        run.until()
        trace,velocities = run.history(),run.bell_history()
        flows = run.tonehole_history() if len(holes) else np.empty((len(trace),0))
        details = dict(cells=len(grid['cells']),axial_cells=len(grid['z'])-1,
                       time_step_s=run.dt,steps=run.steps,bell_rings=int(grid['rings'][-1]),
                       bore_length_m=float(grid['z'][-1]),bell_radius_m=float(grid['radius'][-1]),
                       reconstruction_fallbacks=int(run.fallbacks))
    if not all(np.isfinite(array).all() for array in (trace,velocities,flows)):
        raise RuntimeError('Nonfinite solver output')
    modal = velocities@(load.basis*load.weights[:,None])
    bell = load.radiate(modal,TRACE_FS,angles_deg=(0.,),distance_m=1.)[:,0]
    hole_sound = hole_pressure(flows,[float(hole[0]) for hole in holes],
                              float(grid['z'][-1]),float(grid['radius'][-1]))
    wave = signal.resample_poly(bell+hole_sound,AUDIO_FS,TRACE_FS)
    row = inspect(note,trace,wave,duration,cup_area,pitch_range=pitch_range) | details
    if row['audio_frequency_hz']==row['audio_period_frequency_hz'] and row['audio_frequency_hz']:
        a,b = [round(t*AUDIO_FS) for t in row['sustained_window_s']]
        period = row['audio_frequency_hz']
        ratio = higher_harmonic(wave[a:b],AUDIO_FS,period,note['target_hz'])
        if ratio is not None:
            pitch = period*round(note['target_hz']/period)
            row.update(audio_frequency_hz=pitch,cents=float(1200*np.log2(pitch/note['target_hz'])),
                       subharmonic_peak_ratio=ratio)
    a,b = [round(t*TRACE_FS) for t in row['sustained_window_s']]
    row.update(bell_rms_pa=float(np.std(bell[a:b])),tonehole_rms_pa=float(np.std(hole_sound[a:b])),
               open_toneholes=[list(map(float,hole)) for hole in holes],
               compute_wall_s=time.perf_counter()-began)
    with tempfile.NamedTemporaryFile(dir=path,suffix='.npz',delete=False) as file:
        temp = file.name
        np.savez(file,wave=wave,row=json.dumps(row,allow_nan=False))
    os.replace(temp,cache_file)
    return wave,row


def render(instrument,preset,only,probe,initial_check, *, extended=False):
    out = ROOT/'output/euphonium_extended' if extended else output_dir(instrument)
    os.makedirs(out,exist_ok=True)
    device = Device()
    rows,errors,waves = [],[],[]
    offset = 0
    names = note_names(instrument,extended=extended)
    preview = only or probe
    for note in settings(instrument,preset,extended=extended):
        name = note['note']
        if only and name not in only:
            continue
        duration = probe or (LAST_DURATION_S if name==names[-1] else NOTE_DURATION_S)
        try:
            wave,row = solve(device,instrument,note,duration,initial_check)
        except (RuntimeError,ValueError) as error:
            print(f'{name}: {error}',flush=True)
            errors.append(dict(note=name,error=str(error),preset=note))
        else:
            rows.append(row | {'start_s':offset/AUDIO_FS})
            waves.append(wave)
            offset += len(wave)+round(GAP*AUDIO_FS)
            pitch = row['audio_frequency_hz'] or 0.
            print(f"{name:>3} {pitch:.2f} Hz  {row['cents']} c  p={row['periodicity']:.3f}  "
                  f"out={row['radiated_rms_pa']:.3f} Pa  cup={row['mouthpiece_rms_pa']:.0f} Pa  "
                  f"{row['compute_wall_s']:.1f} s",flush=True)
        if not preview:
            (out/'progress.json').write_text(json.dumps(dict(notes=rows,errors=errors),indent=2))
    if preview:
        label = f'probe_{probe:g}' if probe else 'part'
        selected = '_'.join(only or names)
        (out/f'{label}_{selected}.json').write_text(json.dumps(dict(notes=rows,errors=errors),indent=2))
        return
    failed = [r['note'] for r in rows if r['cents'] is None or abs(r['cents'])>16.
              or r['periodicity']<.90 or r['radiated_rms_pa']<.019]
    if errors or failed or len(rows)!=len(names):
        raise RuntimeError(f"Review notes: {', '.join([r['note'] for r in errors]+failed)}")
    gap = np.zeros(round(GAP*AUDIO_FS))
    taper = .5+.5*np.cos(np.linspace(0.,np.pi,round(.008*AUDIO_FS)))
    for wave in waves:
        wave[-len(taper):] *= taper
    audio = np.concatenate([part for wave in waves for part in (wave,gap)])
    expected = ((len(names)-1)*round(NOTE_DURATION_S*AUDIO_FS)
                +round(LAST_DURATION_S*AUDIO_FS)+len(names)*len(gap))
    if len(audio)!=expected or not np.isfinite(audio).all() or np.max(abs(audio))==0:
        raise RuntimeError('Invalid assembled WAV')
    gain = float(.92/np.max(abs(audio)))
    basename = f'{instrument}_{names[0]}_{names[-1]}_major_f_strong_attack.wav'
    write_wav(out,basename,audio,gain)
    report = dict(
        instrument=instrument,gpu=device.name,wav=basename,duration_s=len(audio)/AUDIO_FS,
        sample_rate_hz=AUDIO_FS,bit_depth=16,channels=1,common_gain_fs_per_pa=gain,
        bell=('coupled spherical exterior with equivalent right-hand area load, receiver on axis at 1 m'
              if instrument=='horn' else 'coupled spherical exterior, receiver on axis 1 m beyond the bell'),
        side_holes=('free-field monopoles of the coupled side-hole flows'
                    if instrument in ('ophicleide','keyed_bugle') else None),
        max_sustained_pitch_error_cents=max(abs(row['cents']) for row in rows),notes=rows,
    )
    (out/'measurements.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('instrument',choices=NAMES)
    parser.add_argument('--preset',type=Path)
    parser.add_argument('--only',nargs='+')
    parser.add_argument('--probe',type=float)
    parser.add_argument('--extended',action='store_true')
    parser.add_argument('--no-initial-check',action='store_true')
    args = parser.parse_args(argv)
    if args.extended and args.instrument!='euphonium':
        parser.error('--extended is only available for euphonium')
    if args.only and not set(args.only)<=set(note_names(args.instrument,extended=args.extended)):
        parser.error('--only contains a note outside the scale')
    if args.probe is not None and not .28<=args.probe<=.8:
        parser.error('--probe duration must be between .28 s and .8 s')
    render(args.instrument,args.preset or ROOT/'data'/f'performance_{args.instrument}.json',
           args.only,args.probe,not args.no_initial_check,extended=args.extended)


if __name__=='__main__':
    main()
