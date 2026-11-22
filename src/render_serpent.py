"""Render a six-hole serpent with fixed geometry and optional embouchure presets."""
import argparse
import json
from pathlib import Path

from analyze_serpent import E3_HOLES, OUT, chart_notes, midi_hz
from axisymmetric_cuda import Device
from compare_trumpet_bell import write_wav
from render_euphonium_ophicleide import solve
from render_tuba_scale import AUDIO_FS, GAP
from trumpet import np


SCALE = ('C2','D2','E2','F2','G2','A2','B2','C3','D3','E3','F3','G3','A3','B3','C4')
SCALE_NAME = 'serpent_C2_C4_untuned.wav'
TUNED_NAME = 'serpent_C2_C4_tuned.wav'
PRESSURE_NAME = 'serpent_E3_pressure_comparison.wav'
REFERENCE_PRESSURE = 2850.
E3_WEAKER_TAKES = {'E3-piano':1450.,'E3-medium':2150.}
LIP_RATIO = 1.12
PITCH_TOLERANCE_CENTS = 15.


def trials(chart):
    by_note = {row['note']:row for row in chart['notes']}
    for name in (*SCALE,*E3_WEAKER_TAKES):
        source = by_note['E3' if name in E3_WEAKER_TAKES else name]
        pitch = midi_hz(source['midi'])
        if source.get('half_open_holes'):
            raise ValueError('This experiment requires fully open or closed ports.')
        yield dict(
            note=name,midi=source['midi'],open_holes=source['open_holes'],target_hz=pitch,
            trim_m=0.,lip_frequency_hz=LIP_RATIO*pitch,
            blowing_pressure_pa=E3_WEAKER_TAKES.get(name,REFERENCE_PRESSURE),
            rest_y_m=16e-6,lip_parameters={},attack_s=.012,attack_boost=.18,
            attack_decay_s=.028,wave_speed_reserve=1.66,
        )


def tuned_trials(chart,preset_path):
    """Apply recorded embouchure settings while keeping the same bore geometry."""
    presets = json.loads(preset_path.read_text(encoding='utf8'))
    by_name = {row['note']:row for row in presets}
    if len(presets)!=len(SCALE) or set(by_name)!=set(SCALE):
        raise ValueError('The embouchure preset must contain one row per scale note.')
    allowed = {'note','lip_frequency_hz','blowing_pressure_pa','rest_y_m',
               'lip_parameters','open_holes','opening_fractions','attack_s','attack_boost','attack_decay_s'}
    for base in trials(chart):
        if base['note'] not in by_name:
            continue
        controls = by_name[base['note']]
        if controls.keys()-allowed:
            raise ValueError(f"Unexpected embouchure control for {base['note']}.")
        yield base | controls


def playback(waves,names):
    """Apply only a short tail fade and insert the same gap after every take."""
    fade = .5+.5*np.cos(np.linspace(0.,np.pi,round(.008*AUDIO_FS)))
    gap = np.zeros(round(GAP*AUDIO_FS))
    segments = []
    for name in names:
        sound = waves[name].copy()
        sound[-len(fade):] *= fade
        segments.extend((sound,gap))
    return np.concatenate(segments)


def render(duration,only=None,preset_path=None):
    chart = chart_notes()
    out = OUT
    out.mkdir(parents=True,exist_ok=True)
    device = Device()
    rows,waves = [],{}
    settings = tuned_trials(chart,preset_path) if preset_path else trials(chart)
    periodicity_minimum = .94 if preset_path else .86
    for preset in settings:
        name = preset['note']
        if only and name not in only:
            continue
        wave,row = solve(device,'serpent',preset,duration,initial_check=False)
        row['stable'] = bool(row['periodicity']>=periodicity_minimum and row['audio_period_frequency_hz']
                             and row['mouthpiece_rms_pa']>=20. and row['radiated_rms_pa']>=.004)
        if preset_path:
            fundamental = row['audio_period_frequency_hz']
            error = float(1200*np.log2(fundamental/row['target_hz'])) if fundamental else None
            row['fundamental_error_cents'] = error
            row['within_pitch_tolerance'] = bool(row['stable'] and abs(error)<=PITCH_TOLERANCE_CENTS)
        rows.append(row)
        waves[name] = wave
        frequency = row['audio_frequency_hz'] or 0.
        status = 'periodic' if row['stable'] else 'unsettled'
        print(f"{name:8} {frequency:7.2f} Hz  {str(row['cents']):>18} cent  "
              f"q={row['periodicity']:.3f}  out={row['radiated_rms_pa']:.3f} Pa  "
              f"cup={row['mouthpiece_rms_pa']:.0f} Pa  {status}  {row['compute_wall_s']:.1f} s",flush=True)
    payload = dict(
        instrument='six-hole C serpent',gpu=device.name,duration_per_take_s=duration,sample_rate_hz=AUDIO_FS,
        geometry_trim_m=0.,fingering_source=chart['source'],takes=rows,
        periodicity_minimum=periodicity_minimum,
    )
    if preset_path:
        payload.update(embouchure_preset=preset_path.name,pitch_tolerance_cents=PITCH_TOLERANCE_CENTS,
                       within_pitch_tolerance=sum(row['within_pitch_tolerance'] for row in rows))
    else:
        payload['lip_hz_per_nominal_hz'] = LIP_RATIO
    if only:
        label = ('tuned_' if preset_path else '')+'_'.join(only)
        (out/f'serpent_{label}_probe.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
        return
    if not preset_path and tuple(next(row['preset']['open_holes'] for row in rows if row['note']=='E3'))!=E3_HOLES:
        raise ValueError('The E3 pressure comparison requires the two lowest holes.')
    names = {TUNED_NAME:SCALE} if preset_path else {SCALE_NAME:SCALE,PRESSURE_NAME:(*E3_WEAKER_TAKES,'E3')}
    audio = {output:playback(waves,order) for output,order in names.items()}
    peak = max(float(np.max(np.abs(sequence))) for sequence in audio.values())
    if not np.isfinite(peak) or peak<=0:
        raise RuntimeError('The simulated previews contain no finite radiated sound.')
    gain = .92/peak
    payload.update(common_gain_fs_per_pa=gain,files={})
    for output,sequence in audio.items():
        write_wav(out,output,sequence,gain)
        payload['files'][output] = dict(takes=names[output],duration_s=len(sequence)/AUDIO_FS,
                                        gap_s=GAP)
    report_name = 'serpent_tuned_playing.json' if preset_path else 'serpent_playing.json'
    (out/report_name).write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration',type=float,default=.65)
    parser.add_argument('--preset',type=Path,help='Per-note embouchure settings for the same scale')
    parser.add_argument('--only',nargs='+',choices=(*SCALE,*E3_WEAKER_TAKES))
    args = parser.parse_args(argv)
    if not .40<=args.duration<=1.65:
        parser.error('Use a take duration between 0.40 s and 1.65 s')
    if args.preset and args.only and set(args.only)-set(SCALE):
        parser.error('The embouchure preset applies to the scale notes.')
    render(args.duration,args.only,args.preset)


if __name__=='__main__':
    main()
