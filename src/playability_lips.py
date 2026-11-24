"""Two-axis lips coupled to a frequency-dependent bore return."""

from collections import Counter
import math

from trumpet import RHO, measure, njit, np

DURATION = .48
CUP_RMS_MIN = 40.
PITCH_TOLERANCE_CENTS = 75.
WINDOWS = ((.24, .36), (.36, .48))
PRESSURES = 1000 * np.array([
    .5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7, 8, 9, 10, 11,
    12, 13, 14, 15, 16, 18, 20, 22,
])
LIP_RATIOS = np.round(np.arange(.72, 1.3401, .02), 2)
LIP_KEYS = ('width', 'thickness', 'joint', 'rest_x', 'mass_product', 'quality', 'cup_area')
REST = .000027
ATTACK = .014
BOOST = .22
DECAY = .027


@njit(cache=True,nogil=True,fastmath={'reassoc','contract'})
def coupled_cup(response, impedance, duration, fs, frequency, pressure, rest, attack, boost, decay,
                width, thickness, joint, rest_x, mass_product, quality, cup_area, gap_ratio, cubic):
    """Centered-difference two-axis lip motion with nonlinear inertial/Bernoulli flow."""
    count = round(duration*fs)
    trace = np.empty(count)
    taps = len(response)
    outgoing = np.zeros(2*taps)
    cursor = taps-1
    dt = 1/fs
    omega=2*np.pi*frequency
    ax_scale=dt**2*omega**2/(mass_product*frequency)*2*width
    x_stiffness=(omega*dt)**2
    y_stiffness=x_stiffness*gap_ratio**2
    x_old=x=rest_x
    y_old=y=rest
    mouthpiece_p=gap_p=jet=0.
    immediate_z = impedance*(1+response[0])/(1-response[0])
    for n in range(count):
        t=n*dt
        rise=.5-.5*np.cos(np.pi*t/attack) if t<attack else 1.
        if t<attack+decay:
            rise*=1+.5*boost*(1+np.cos(np.pi*max(0.,t-attack)/decay))
        mouth_p=pressure*rise
        delta_p=mouth_p-mouthpiece_p
        damping=.5*omega*dt/(quality if y>0. else .5)
        damping_y=damping*gap_ratio
        displacement=y-rest
        force_x=ax_scale*delta_p*(joint-y)-x_stiffness*(x-rest_x)
        force_y=ax_scale*(delta_p*x+thickness*gap_p)-y_stiffness*displacement*(1+cubic*displacement**2)
        if y<0.:
            force_y-=6*y_stiffness*y
        next_x=(2*x-(1-damping)*x_old+force_x)/(1+damping)
        next_y=(2*y-(1-damping_y)*y_old+force_y)/(1+damping_y)
        swept=width*(x*(next_y-y_old)-(y-joint)*(next_x-x_old))/(2*dt)
        x_old,y_old=x,y
        x,y=next_x,next_y
        area=2*width*y
        returning=0.
        for j in range(1,min(n+1,taps)):
            returning+=response[j]*outgoing[cursor+j]
        returning/=1-response[0]
        if area>1e-12:
            quadratic=RHO*(.5/area**2-1/(cup_area*area)+1/cup_area**2)
            inertia=RHO*thickness/(area*dt)
            linear=inertia+immediate_z
            drive=mouth_p-returning-immediate_z*swept+inertia*jet
            jet=2*drive/(linear+np.sqrt(linear**2+4*quadratic*abs(drive)))
            mouthpiece_p=returning+immediate_z*(jet+swept)
            gap_p=mouthpiece_p-RHO*jet*abs(jet)*(1/(cup_area*area)-1/cup_area**2)
        else:
            jet=0.
            mouthpiece_p=returning+immediate_z*swept
            gap_p=mouthpiece_p
        if not np.isfinite(mouthpiece_p) or abs(mouthpiece_p)>3e5 or abs(x)>.05 or abs(y)>.02:
            return trace[:n]
        traveling=mouthpiece_p+impedance*(jet+swept)
        outgoing[cursor]=traveling
        outgoing[cursor+taps]=traveling
        cursor=taps-1 if cursor==0 else cursor-1
        trace[n]=mouthpiece_p
    return trace


def onset_time(wave, fs, pitch, steady_rms):
    window = round(fs*max(.005,1/pitch))
    dwell = round(fs*.012)
    energy = np.r_[0.,np.cumsum(wave**2)]
    rms = np.sqrt(np.maximum(0.,(energy[window:]-energy[:-window])/window))
    consecutive = np.r_[0,np.cumsum(rms>=.5*steady_rms)]
    onset = np.flatnonzero(consecutive[dwell:]-consecutive[:-dwell]==dwell)
    return float(1000*(onset[0]+.5*window)/fs) if len(onset) else None


def evaluate(name, target, lip_frequency, pressure, wave, fs, peaks, min_pitch_hz):
    duration = DURATION
    output=dict(note=name,target_hz=target,lip_frequency_hz=lip_frequency,blowing_pressure_pa=pressure,
                target_passive_peak_hz=float(peaks[np.argmin(abs(np.log(peaks/target)))]),
                audio_frequency_hz=None,periodicity=None,pitch_error_cents=None,onset_50_percent_ms=None,
                sustained_cup_rms_pa=None,other_passive_peak_hz=None)
    if len(wave)<round(duration*fs)-1 or not np.isfinite(wave).all():
        return output | {'outcome':'invalid'}
    windows=WINDOWS if duration==DURATION else ((duration-.24,duration-.12),(duration-.12,duration))
    data=np.broadcast_to(wave[:,None],(len(wave),4))
    fits=[]
    for start,end in windows:
        try:
            fit=measure(data,fs,start=start,end=end,min_hz=min_pitch_hz,max_hz=2450)
        except IndexError:
            # The legacy estimator has no selected lag if all correlation peaks are nonpositive.
            fit=dict(frequency=0.,rms=float(np.std(wave[round(start*fs):round(end*fs)])),periodicity=0.)
        fits.append(fit)
    early,late=fits
    output.update(sustained_cup_rms_pa=late['rms'],periodicity=late['periodicity'])
    if late['rms']<CUP_RMS_MIN or early['rms']<CUP_RMS_MIN and late['rms']<=2*CUP_RMS_MIN:
        return output | {'outcome':'no_sustain'}
    pitch=late['frequency']
    previous=early['frequency']
    if (not pitch or not previous or min(early['periodicity'],late['periodicity'])<.90
        or late['rms']<.65*early['rms'] or abs(1200*math.log2(pitch/previous))>30):
        return output | {'outcome':'unstable','audio_frequency_hz':pitch or None}
    cents=1200*math.log2(pitch/target)
    mode=float(peaks[np.argmin(abs(np.log(peaks/pitch)))])
    onset=onset_time(wave,fs,pitch,late['rms'])
    match=abs(cents)<=PITCH_TOLERANCE_CENTS
    return output | {'outcome':'target' if match else 'other','audio_frequency_hz':pitch,
                     'pitch_error_cents':cents,'onset_50_percent_ms':onset,'other_passive_peak_hz':mode}


def longest_range(rows):
    groups=[]
    active=[]
    for row in rows:
        if row['outcome']=='target':
            active.append(row['lip_frequency_hz'])
        elif active:
            groups.append(active)
            active=[]
    if active:
        groups.append(active)
    if not groups:
        return None
    chosen=max(groups,key=lambda candidates:math.log(candidates[-1]/candidates[0]))
    return dict(min_hz=chosen[0],max_hz=chosen[-1],count=len(chosen),
                width_cents=1200*math.log2(chosen[-1]/chosen[0]),intervals=len(groups))


def summarize(name, target, selector, rows):
    passed = [row for row in rows if row['outcome']=='target']
    widths = {str(int(p)):longest_range([row for row in rows if row['blowing_pressure_pa']==p])
              for p in PRESSURES}
    pressure_min=min((row['blowing_pressure_pa'] for row in passed),default=None)
    minimum=[row['lip_frequency_hz'] for row in passed if row['blowing_pressure_pa']==pressure_min]
    onset=[row['onset_50_percent_ms'] for row in passed if row['onset_50_percent_ms'] is not None]
    return dict(note=name, **selector,target_hz=target,
                acoustic_mode_hz=rows[0]['target_passive_peak_hz'], trials=len(rows),
                counts=dict(Counter(row['outcome'] for row in rows)),
                first_success_pressure_pa=pressure_min,first_success_lip_hz=minimum,
                nearest_50c_count=sum(row['pitch_error_cents'] is not None and abs(row['pitch_error_cents'])<=50 for row in rows),
                nearest_100c_count=sum(row['pitch_error_cents'] is not None and abs(row['pitch_error_cents'])<=100 for row in rows),
                onset_median_ms=float(np.median(onset)) if onset else None, width_by_pressure_pa=widths)
