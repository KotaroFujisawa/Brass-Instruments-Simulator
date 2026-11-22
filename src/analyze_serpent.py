"""Evaluate a six-hole serpent before any note-by-note pitch adjustment."""
import argparse
import json
from pathlib import Path

from axisymmetric_cuda import HOLE_RADIATION_RESISTANCE, tonehole_lengths
from render_trumpet_bell import build_load
from serpent_axisymmetric import open_toneholes, refined_serpent_mesh
from trumpet import C, RHO, ROOT, np, signal


OUT = ROOT/'output/serpent_axisymmetric'
CHART = ROOT/'data/serpent_fingerings.json'
ALL_HOLES = tuple(range(1,7))
E3_HOLES = (5,6)
DYNAMICS = {'piano':(1.,.5,.2,.1), 'forte':(1.,1.,.7,.4)}


def chart_notes(path=CHART):
    chart = json.loads(path.read_text(encoding='utf8'))
    rows = chart['notes']
    if len({row['note'] for row in rows})!=len(rows):
        raise ValueError('Each note in the fingering chart must occur once.')
    return chart


def midi_hz(midi):
    return 440.*2**((midi-69)/12)


def cents(actual,reference):
    return float(1200.*np.log2(actual/reference))


def impedance_bank(frequencies, fingerings, *, axial_scale=1.):
    """Linear plane-wave impedance at the lips, normalized by rho*c/cup area.

    Cylindrical transfer matrices approximate the tapered tube on short segments.
    Each open chimney is a shunt using the same inertance and radiation impedance
    as the nonlinear solver. The remainder of the bore stays active downstream.
    """
    fingerings = tuple(dict.fromkeys(tuple(sorted(setting)) for setting in fingerings))
    ports = open_toneholes(ALL_HOLES)
    grid = refined_serpent_mesh(ALL_HOLES,axial_scale=axial_scale)
    z = np.unique(np.r_[grid['z'],[port[0] for port in ports]])
    radius = np.interp(z,grid['z'],grid['radius'])
    by_index = {int(np.searchsorted(z,port[0])):(i,port)
                for i,port in enumerate(ports,1)}
    angular = 2*np.pi*frequencies

    exterior = build_load(grid)
    x = 1j*angular*radius[-1]/C
    sphere = np.column_stack([x*np.polyval(n,x)/np.polyval(d,x) for n,d in exterior.polynomials])
    area_bell = np.pi*radius[-1]**2
    z_bell = RHO*C/area_bell*(sphere@(2*exterior.projection[:,0])**2)
    pressure = np.broadcast_to(z_bell,(len(fingerings),len(frequencies))).copy()
    flow = np.ones_like(pressure)
    for i in range(len(z)-2,-1,-1):
        midpoint_radius = .5*(radius[i]+radius[i+1])
        rv = 632.8*np.sqrt(np.maximum(frequencies,.05))*midpoint_radius
        phase = (1j+(1+1j)*1.045/rv)*angular/C*(z[i+1]-z[i])
        characteristic = RHO*C/(np.pi*midpoint_radius**2)*(1+(1-1j)*.369/rv)
        cosh,sinh = np.cosh(phase),np.sinh(phase)
        pressure,flow = cosh*pressure+characteristic*sinh*flow,sinh/characteristic*pressure+cosh*flow
        if i in by_index:
            number,(_,hole_radius,height) = by_index[i]
            chimney,radiation = tonehole_lengths(hole_radius,height,radius[i])
            response = 1j*angular*radiation/C
            z_hole = RHO*C/(np.pi*hole_radius**2)*(
                1j*angular*chimney/C+HOLE_RADIATION_RESISTANCE*response/(1+response))
            opened = [row for row,setting in enumerate(fingerings) if number in setting]
            flow[opened] += pressure[opened]/z_hole
    z_cup = RHO*C/(np.pi*radius[0]**2)
    return dict(zip(fingerings,pressure/flow/z_cup))


def peaks(frequency, response, *, lo=32., hi=1700.):
    """Find local maxima with quadratic refinement on the evenly spaced grid."""
    indices,_ = signal.find_peaks(response)
    rows = []
    for i in indices:
        if lo<=frequency[i]<=hi:
            left,middle,right = response[i-1:i+2]
            shift = .5*(left-right)/(left-2*middle+right)
            rows.append(dict(hz=float(frequency[i]+shift*(frequency[i+1]-frequency[i])),
                             value=float(middle-.25*(left-right)*shift)))
    return rows


def nearest_mode(modes,target):
    return min(enumerate(modes,1),key=lambda item:abs(cents(item[1]['hz'],target)))


def weighted_sums(frequency,impedance):
    """The two harmonic-weight choices in Campbell et al., Fig. 4.96."""
    fundamental = frequency[frequency<=frequency[-1]/4]
    harmonics = np.array([np.interp(order*fundamental,frequency,impedance.real)
                          for order in range(1,5)])
    return fundamental,{name:np.asarray(weights)@harmonics/4 for name,weights in DYNAMICS.items()}


def evaluate(chart, frequency, bank):
    modes = {holes:peaks(frequency,np.abs(impedance)) for holes,impedance in bank.items()}
    _,closed_c2 = nearest_mode(modes[()],midi_hz(36))
    reference = closed_c2['hz']
    offset = cents(reference,midi_hz(36))
    notes,excluded = [],[]
    for note in chart['notes']:
        if note.get('half_open_holes'):
            excluded.append(note['note'])
            continue
        nominal = midi_hz(note['midi'])
        holes = tuple(sorted(note['open_holes']))
        transposed = reference*2**((note['midi']-36)/12)
        ordinal,mode = nearest_mode(modes[holes],transposed)
        alternatives = []
        for setting in note.get('alternates',()):
            alternative_number,alternative = nearest_mode(modes[tuple(sorted(setting))],transposed)
            alternatives.append(dict(open_holes=setting,nearest_mode_number=alternative_number,
                                     nearest_mode_hz=alternative['hz'],
                                     residual_after_c2_reference_cents=cents(alternative['hz'],transposed)))
        notes.append(note | dict(nominal_hz=nominal,comparison_hz=transposed,
                                 nearest_mode_hz=mode['hz'],nearest_mode_number=ordinal,
                                 mode_magnitude_z0=mode['value'],
                                 deviation_a440_cents=cents(mode['hz'],nominal),
                                 residual_after_c2_reference_cents=cents(mode['hz'],transposed),
                                 alternative_modes=alternatives))
    comparison = {}
    for label,holes in (('closed',()),('first_open',(1,)),('lowest_two_open',E3_HOLES)):
        comparison[label] = [row | {'mode':number,
            'cents_from_closed_mode':cents(row['hz'],modes[()][number-1]['hz'])}
            for number,row in enumerate(modes[holes][:8],1)]
    f_sum,sums = weighted_sums(frequency,bank[E3_HOLES])
    candidates = {label:peaks(f_sum,curve,lo=122.,hi=192.) for label,curve in sums.items()}
    report = dict(
        instrument='six-hole C serpent',geometry_trim_m=0.,reference_a4_hz=440.,
        fingering_source=chart['source'],closed_c2_reference_hz=reference,
        closed_c2_offset_cents=offset,notes=notes,excluded_half_hole_notes=excluded,
        mode_comparison=comparison,
        e3_two_open=dict(open_holes=E3_HOLES,nominal_hz=midi_hz(52),weighting=DYNAMICS,
                         peaks=candidates),
    )
    return report,f_sum,sums


def plot(path,frequency,bank,report,f_sum,sums, *, font=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    if font is not None:
        font_manager.fontManager.addfont(font)
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=font).get_name()
    plt.rcParams['axes.unicode_minus'] = False
    figure,axes = plt.subplots(3,1,figsize=(10,10),layout='constrained')
    labels = ('全閉','第1孔を開く','ベル側2孔を開く') if font else ('All closed','Hole 1 open','Holes 5 and 6 open')
    for holes,label,color in zip(((),(1,),E3_HOLES),labels,('#224b8d','#a76822','#27816c')):
        axes[0].plot(frequency,20*np.log10(np.abs(bank[holes])),label=label,color=color)
    axes[0].set(xlim=(35,650),ylabel='|Z / Z₀| (dB)',xlabel='周波数 (Hz)' if font else 'Frequency (Hz)')
    axes[0].legend(frameon=False,loc='best')

    for (name,curve),color in zip(sums.items(),('#224b8d','#b34442')):
        axes[1].plot(f_sum,curve,label=name,color=color)
    axes[1].axvline(midi_hz(52),color='.45',ls=':',label='E3 (A4 = 440 Hz)')
    axes[1].set(xlim=(126,187),xlabel='基音候補 (Hz)' if font else 'Candidate fundamental (Hz)',
                ylabel='共鳴の加重和 / Z₀' if font else 'Weighted resonance sum / Z₀')
    axes[1].legend(frameon=False,loc='best')

    notes = [row for row in report['notes'] if 36<=row['midi']<=60
             and row['midi']%12 in (0,2,4,5,7,9,11)]
    error = [row['residual_after_c2_reference_cents'] for row in notes]
    axes[2].axhline(0,color='.5',lw=.9)
    axes[2].bar([row['note'] for row in notes],error,
                color=['#397595' if value>=0 else '#b65c4e' for value in error])
    axes[2].set(ylabel='C2を基準にした共鳴のずれ (cent)' if font else 'Resonance deviation relative to C2 (cent)')
    for axis in axes:
        axis.spines[['right','top']].set_visible(False)
        axis.grid(axis='y',alpha=.16)
        axis.set_axisbelow(True)
    figure.savefig(path,dpi=160)
    plt.close(figure)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',type=Path,default=OUT)
    parser.add_argument('--axial-scale',type=float,default=1.)
    parser.add_argument('--plot-font',type=Path)
    args = parser.parse_args(argv)
    chart = chart_notes()
    frequency = np.arange(24.,2100.01,.25)
    settings = [(),(1,),E3_HOLES]
    for note in chart['notes']:
        if not note.get('half_open_holes'):
            settings.extend([tuple(note['open_holes']),*map(tuple,note.get('alternates',()))])
    bank = impedance_bank(frequency,settings,axial_scale=args.axial_scale)
    report,f_sum,sums = evaluate(chart,frequency,bank)
    report['linear_axial_scale'] = args.axial_scale
    args.out_dir.mkdir(parents=True,exist_ok=True)
    (args.out_dir/'serpent_impedance.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    plot(args.out_dir/'serpent_intonation.png',frequency,bank,report,f_sum,sums,font=args.plot_font)
    print(f"C2 closed: {report['closed_c2_reference_hz']:.2f} Hz")
    for label,rows in report['mode_comparison'].items():
        print(label,[(round(row['hz'],1),round(row['cents_from_closed_mode'])) for row in rows[:6]])
    print('E3',report['e3_two_open']['peaks'])


if __name__=='__main__':
    main()
