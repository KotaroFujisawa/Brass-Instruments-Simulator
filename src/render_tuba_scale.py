"""Render a three-octave forte B-flat major scale on a BB-flat tuba."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from functools import cache

from axisymmetric_cuda import Device, Run
from compare_trumpet_bell import harmonic_rms, write_wav
from render_bidirectional import measure_audio
from render_trumpet_bell import build_load
from tuba_axisymmetric import refined_tuba_mesh
from trumpet import C, RHO, ROOT, measure, np, signal

OUT = ROOT/'output/tuba_axisymmetric'
PRESET = ROOT/'data/performance_tuba.json'
WAV_NAME = 'BBb_tuba_Bb1_Bb4_major_f_strong_attack.wav'
AUDIO_FS = 48000
TRACE_FS = 192000
GAP = .09
PITCH_RANGE = dict(min_hz=26.,max_hz=1100.)
NOTES = ('Bb1',)+tuple(f'{name}{octave}' for octave in range(2,5)
                       for name in ('C','D','Eb','F','G','A','Bb'))
MIDI = tuple(34+12*octave+semitone for octave in range(3)
             for semitone in (0,2,4,5,7,9,11))+(70,)
LIPS = dict(width=.0145,thickness=.0038,joint=.0078,rest_x=.00185,
            mass_product=6.6,quality=3.5)
MODEL = dict(thermoviscous=True,radiation_order=2,reservoir_inflow=True)


def settings(path):
    parameters = json.loads(path.read_text())
    by_name = {note['note']:note for note in parameters}
    if len(parameters)!=len(NOTES) or set(by_name)!=set(NOTES):
        raise ValueError('The performance preset must contain the 22 B-flat major notes.')
    for name,midi in zip(NOTES,MIDI):
        note = by_name[name]
        yield dict(attack_s=.0075,attack_boost=.40,attack_decay_s=.028,
                   rest_y_m=0.,trim_m=0.,wave_speed_reserve=1.58,lip_parameters={}) | note | {
            'midi':midi, 'target_hz':440*2**((midi-69)/12),
        }


@cache
def solver_signature():
    names = (
        'axisymmetric_cuda.py','axisymmetric_euler.cu','thermoviscous.py','bell_exterior.py',
        'render_trumpet_bell.py','axisymmetric_mesh.py','tuba_axisymmetric.py','render_tuba_scale.py',
        'trumpet.py','render_bidirectional.py','compare_trumpet_bell.py',
    )
    return hashlib.sha256(b''.join((ROOT/'src'/name).read_bytes() for name in names)).digest()


def inspect(note, trace, wave, duration, cup_area, *, pitch_range=PITCH_RANGE):
    end = duration-.18 if duration>.8 else duration
    start = max(.18,end-.24)
    audio = measure_audio(wave,start,end,**pitch_range)
    pitch = period = audio['frequency']
    odd_to_even = None
    if .48<pitch/note['target_hz']<.52:
        lo,hi = (round(t*AUDIO_FS) for t in (start,end))
        lines = harmonic_rms(wave[lo:hi],AUDIO_FS,pitch,14)
        odd = max((line['rms_pa'] for line in lines if line['order']%2),default=0.)
        even = max((line['rms_pa'] for line in lines if not line['order']%2),default=0.)
        if even:
            odd_to_even = odd/even
            if odd_to_even<.15:
                pitch *= 2
    steady = trace[round(start*TRACE_FS):round(end*TRACE_FS)]
    residual = steady[:,0]-steady[:,8]-(RHO*C/cup_area)*steady[:,1]
    early = wave[round(.018*AUDIO_FS):round(.105*AUDIO_FS)]
    return dict(
        note=note['note'],target_hz=note['target_hz'],audio_frequency_hz=pitch or None,
        audio_period_frequency_hz=period or None,subharmonic_odd_to_even=odd_to_even,
        cents=float(1200*np.log2(pitch/note['target_hz'])) if pitch else None,
        periodicity=audio['periodicity'],radiated_rms_pa=audio['rms'],
        mouthpiece_rms_pa=float(np.std(steady[:,0])),
        incoming_characteristic_rms_pa=float(np.std(steady[:,8])),
        boundary_residual_pa=float(np.max(abs(residual))),
        attack_rms_pa=float(np.std(early)),peak_blowing_pressure_pa=float(np.max(trace[:,6])),
        preset=note,duration_s=duration,sustained_window_s=[start,end],
    )


def solve(device, note, duration, initial_check=True):
    grid = refined_tuba_mesh(
        tuple(note['valves']),tuning=note['trim_m'],axial_scale=note.get('axial_scale',1.),
        dr=note.get('radial_spacing_m',.0075),
    )
    cup_area = float(np.pi*grid['radius'][0]**2)
    lips = LIPS | note['lip_parameters'] | {'cup_area':cup_area}
    key = hashlib.sha256(solver_signature()+json.dumps([note,lips,duration,MODEL],sort_keys=True).encode())
    for component in ('z','radius','rings'):
        key.update(grid[component].tobytes())
    filename = OUT/'cache'/f"{note['note']}_{key.hexdigest()[:16]}.npz"
    if filename.exists():
        with np.load(filename) as cached:
            return cached['wave'],json.loads(str(cached['row']))

    began = time.perf_counter()
    load = build_load(grid)
    with Run(device,grid,duration,lip_hz=note['lip_frequency_hz'],
             pressure=note['blowing_pressure_pa'],rest_y=note['rest_y_m'],
             attack=note['attack_s'],attack_boost=note['attack_boost'],
             attack_decay=note['attack_decay_s'],guard=note['wave_speed_reserve'],
             hold=duration-.16 if duration>.8 else duration,release=.078,
             lip_parameters=lips,exterior_load=load,record_bell=True,**MODEL) as run:
        if initial_check and duration>.8:
            run.until(.44)
            pilot = measure(run.history(),fs=TRACE_FS,start=.28,**PITCH_RANGE)
            relative = pilot['frequency']/note['target_hz']
            if .47<relative<.53:
                relative *= 2
            if pilot['rms']<25 or not .953<relative<1.047:
                raise ValueError(f"Attack reached {pilot['frequency']:.2f} Hz, {pilot['rms']:.1f} Pa cup RMS")
        run.until()
        trace,velocity = run.history(),run.bell_history()
        details = dict(cells=len(grid['cells']),axial_cells=len(grid['z'])-1,
                       time_step_s=run.dt,steps=run.steps,bell_rings=int(grid['rings'][-1]),
                       bore_length_m=float(grid['z'][-1]),bell_radius_m=float(grid['radius'][-1]),
                       reconstruction_fallbacks=int(run.fallbacks),
                       compute_wall_s=time.perf_counter()-began)
    if not (np.isfinite(trace).all() and np.isfinite(velocity).all()):
        raise RuntimeError('Nonfinite solver output')
    areas = grid['faces'][grid['bell']:]['area']
    details['bell_flux_residual_m3_s'] = float(np.max(abs(velocity@areas-trace[:,9])))
    if details['bell_flux_residual_m3_s']>=5e-7:
        raise RuntimeError('Bell flow does not match the annular velocities')
    modal = velocity@(load.basis*load.weights[:,None])
    pressure = load.radiate(modal,TRACE_FS,angles_deg=(0.,),distance_m=1.)[:,0]
    wave = signal.resample_poly(pressure,AUDIO_FS,TRACE_FS)
    row = inspect(note,trace,wave,duration,cup_area) | details
    with tempfile.NamedTemporaryFile(dir=filename.parent,suffix='.npz',delete=False) as file:
        temporary = file.name
        np.savez(file,wave=wave,row=json.dumps(row,allow_nan=False))
    os.replace(temporary,filename)
    return wave,row


def render(preset, only, probe, initial_check):
    os.makedirs(OUT/'cache',exist_ok=True)
    device = Device()
    rows,errors,waves = [],[],[]
    offset = 0
    for note in settings(preset):
        name = note['note']
        if only and name not in only:
            continue
        duration = probe or (1.65 if name=='Bb4' else 1.08)
        try:
            wave,row = solve(device,note,duration,initial_check)
        except (RuntimeError,ValueError) as error:
            print(f'{name}: {error}',flush=True)
            errors.append(dict(note=name,error=str(error),preset=note))
            continue
        rows.append(row | {'start_s':offset/AUDIO_FS})
        waves.append(wave)
        offset += len(wave)+round(GAP*AUDIO_FS)
        pitch = row['audio_frequency_hz'] or 0.
        print(f"{name:>3}  {pitch:.2f} Hz  {row['cents']} cents  "
              f"p={row['periodicity']:.3f}  bell={row['radiated_rms_pa']:.3f} Pa  "
              f"cup={row['mouthpiece_rms_pa']:.0f} Pa  {row['compute_wall_s']:.1f} s",flush=True)
        if not only and not probe:
            (OUT/'progress.json').write_text(json.dumps(dict(notes=rows,errors=errors),indent=2)+'\n')
    if probe or only:
        suffix = '_'.join(only) if only else 'all'
        label = f'probe_{probe:g}' if probe else 'part'
        (OUT/f'{label}_{suffix}.json').write_text(json.dumps(
            dict(notes=rows,errors=errors),indent=2,allow_nan=False)+'\n')
        return
    failed = [row['note'] for row in rows if row['cents'] is None or abs(row['cents'])>16
              or row['periodicity']<.90 or row['radiated_rms_pa']<.025]
    if errors or failed or len(rows)!=22:
        raise RuntimeError(f"Review these notes: {', '.join([error['note'] for error in errors]+failed)}")
    gap = np.zeros(round(GAP*AUDIO_FS))
    release = .5+.5*np.cos(np.linspace(0.,np.pi,round(.008*AUDIO_FS)))
    for wave in waves:
        wave[-len(release):] *= release
    audio = np.concatenate([part for wave in waves for part in (wave,gap)])
    if len(audio)!=1262880 or not np.isfinite(audio).all() or np.max(abs(audio))==0:
        raise RuntimeError('Invalid assembled scale')
    gain = float(.92/np.max(abs(audio)))
    write_wav(OUT,WAV_NAME,audio,gain)
    (OUT/'measurements.json').write_text(json.dumps(dict(
        instrument='BB-flat contrabass tuba',gpu=device.name,duration_s=len(audio)/AUDIO_FS,
        bore='Alexander contrabass tuba profile reconstructed and adapted to BB-flat',
        mouthpiece='Yamaha BB-67C4 reconstructed from a measured cross section and nominal dimensions',
        sample_rate_hz=AUDIO_FS,bit_depth=16,channels=1,common_gain_fs_per_pa=gain,
        output_tail_fade_s=.008,bell='coupled spherical exterior; receiver at 0 deg and 1 m',
        max_sustained_pitch_error_cents=max(abs(row['cents']) for row in rows),notes=rows,
    ),indent=2,allow_nan=False)+'\n')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preset',type=Path,default=PRESET)
    parser.add_argument('--only',nargs='+',choices=NOTES)
    parser.add_argument('--probe',type=float)
    parser.add_argument('--no-initial-check',action='store_true')
    args = parser.parse_args()
    if args.probe is not None and not .30<=args.probe<=.8:
        parser.error('--probe duration must be between .30 s and .8 s')
    render(args.preset,args.only,args.probe,not args.no_initial_check)
