"""Construct weak-pulse or full-band transfer-matrix bore return filters."""

from axisymmetric_cuda import HOLE_RADIATION_RESISTANCE, Run, tonehole_lengths
from bell_exterior import exterior_model
from trumpet import C, RHO, np, signal

PULSE_FS = 192000
FS = 32000
NFFT = 16384
FIR_SECONDS = .18
PULSE_SECONDS = .255
PULSE_AMPLITUDE = 40.


def impedance(mesh, load, f):
    """Evaluate the lossy plane-wave input impedance with open-hole shunts."""
    f=np.maximum(f,.001)
    omega=2*np.pi*f
    bell=getattr(load,'aperture',load)
    ka=1j*omega*bell.radius_m/C
    radial=np.column_stack([ka*np.polyval(n,ka)/np.polyval(d,ka) for n,d in bell.polynomials])
    p=RHO*C/(np.pi*bell.radius_m**2)*(radial@(2*bell.projection[:,0])**2)
    u=np.ones_like(p)
    z,r=mesh['z'],mesh['radius']
    holes=mesh.get('toneholes',())
    if len(holes):
        stations=np.unique(np.r_[z,[h[0] for h in holes]])
        r=np.interp(stations,z,r)
        z=stations
    shunts = {int(np.searchsorted(z,h[0])): h for h in holes}
    for i in range(len(z)-2,-1,-1):
        length=z[i+1]-z[i]
        radius=(r[i]+r[i+1])*.5
        rv=632.8*np.sqrt(f.clip(min=.05))*radius
        phase=(1j+(1+1j)*1.045/rv)*omega/C*length
        zc=RHO*C/(np.pi*radius**2)*(1+(1-1j)*.369/rv)
        cosh,sinh=np.cosh(phase),np.sinh(phase)
        p,u=cosh*p+zc*sinh*u,sinh*p/zc+cosh*u
        if i in shunts:
            _,radius_h,chimney=shunts[i]
            inertance,radiation=tonehole_lengths(radius_h,chimney,r[i])
            s=1j*omega*radiation/C
            zh=RHO*C/(np.pi*radius_h**2)*(1j*omega*inertance/C+HOLE_RADIATION_RESISTANCE*s/(1+s))
            u+=p/zh
    return p/u


def trumpet_impedance(mesh, f):
    z = mesh['z']
    radius = mesh['radius']
    bell = exterior_model(np.linspace(0., radius[-1], mesh['rings'][-1] + 1))
    x = 2j*np.pi*f*radius[-1]/C
    diagonal = np.column_stack([x*np.polyval(n,x)/np.polyval(d,x)
                                for n,d in bell.polynomials])
    p = RHO*C/(np.pi*radius[-1]**2) * (diagonal @ (2*bell.projection[:, 0])**2)
    u = np.ones_like(p)
    k = 2*np.pi*f/C
    for length, a in zip(np.diff(z)[::-1], ((radius[:-1]+radius[1:])/2)[::-1]):
        rv = 632.8*np.sqrt(np.maximum(f,.05))*a
        phase = (1j+(1+1j)*1.045/rv)*k*length
        zc = RHO*C/(np.pi*a*a)*(1+(1-1j)*.369/rv)
        cosh, sinh = np.cosh(phase), np.sinh(phase)
        p,u = cosh*p+zc*sinh*u, sinh*p/zc+cosh*u
    return p/u


def weak_pulse_response(device, mesh, load, min_peak_hz, *, trumpet_profile=False):
    with Run(device,mesh,PULSE_SECONDS,mode=3,pressure=PULSE_AMPLITUDE,
             guard=1.40,thermoviscous=True,exterior_load=load,
             reservoir_inflow=True,trace_fs=PULSE_FS) as run:
        run.until()
        ret = run.history()[:,8].astype(float)
        time_step=run.dt
    if abs(np.mean(ret[-9000:])) >= .6:
        raise ValueError('The weak-pulse response has a nonzero tail.')
    time_samples = (np.arange(1,len(ret)+1)/PULSE_FS)-time_step
    drive = PULSE_AMPLITUDE*np.exp(-.5*((time_samples-.00045)/.00007)**2)
    fade_len = int(.035*PULSE_FS)
    ret[-fade_len:] *= np.cos(np.linspace(0,np.pi/2,fade_len))**2
    nfull=NFFT*(PULSE_FS//FS)
    incoming = np.fft.rfft(ret,nfull)
    prescribed = 2*np.fft.rfft(drive,nfull)
    f = np.fft.rfftfreq(NFFT, 1/FS)
    zc = RHO*C/(np.pi*mesh['radius'][0]**2)
    zin = (trumpet_impedance(mesh, f.clip(min=.001)) if trumpet_profile
           else impedance(mesh, load, f))
    tmm = (zin-zc)/(zin+zc)
    blend = .5+.5*np.cos(np.pi*np.clip((f-2500.)/2500.,0.,1.))
    low = int(np.searchsorted(f,5000.))
    refl = (1-blend)*tmm
    refl[:low] += blend[:low]*(incoming[:low]/(incoming[:low]+prescribed[:low]))
    refl /= np.maximum(1.,abs(refl))
    refl[0] = -1.
    refl[-1] = refl[-1].real
    response = np.fft.irfft(refl)
    n = round(FIR_SECONDS*FS)
    fir = response[:n].copy()
    taper = round(.025*FS)
    fir[-taper:] *= np.cos(np.linspace(0,np.pi/2,taper))**2
    weights = np.hanning(n)
    weights[:round(.018*FS)] = 0.
    fir += (-1-fir.sum())*weights/weights.sum()
    if not np.isfinite(fir).all() or abs(fir.sum()+1) >= 1e-12:
        raise ValueError('Invalid weak-pulse return filter.')
    implemented = np.fft.rfft(fir,NFFT)
    impedance_values = (1+implemented)/(1-implemented)*zc
    indices,_ = signal.find_peaks(abs(impedance_values),prominence=zc)
    selected = indices[(f[indices]>min_peak_hz)&(f[indices]<1800)]
    return dict(fir=fir, fs=FS, zc=zc, peaks=f[selected],
                peak_magnitudes=abs(impedance_values[selected]))


def plane_wave_response(mesh, load, min_peak_hz, *, tuba_c2=False):
    f = np.fft.rfftfreq(NFFT, 1 / FS)
    zc = RHO * C / (np.pi * mesh['radius'][0]**2)
    zin = impedance(mesh, load, f)
    reflection = (zin-zc) / (zin+zc)
    reflection[0] = -1.
    reflection[-1] = reflection[-1].real
    raw = np.fft.irfft(reflection, NFFT)
    length = round(.24 * FS)
    fir = raw[:length].copy()
    fir[1:] += raw[-1:-length:-1]
    taper = round(.04 * FS)
    fir[-taper:] *= np.cos(np.linspace(0, np.pi / 2, taper))**2
    weights = np.hanning(length)
    weights[:round(.024 * FS)] = 0.
    fir += (-1-fir.sum()) * weights / weights.sum()
    actual = np.fft.rfft(fir, NFFT)
    if not np.isfinite(actual).all() or abs(fir.sum()+1) >= 1e-12:
        raise ValueError('Invalid plane-wave return filter.')
    if tuba_c2:
        if np.max(abs(actual)) > 1.001:
            raise ValueError('The tuba C2 return filter is not passive.')
        with np.errstate(divide='ignore', invalid='ignore'):
            zin = zc * (1+actual) / (1-actual)
        bins, _ = signal.find_peaks(abs(zin), prominence=zc)
    else:
        bins, _ = signal.find_peaks(abs(zin))
    bins = bins[(f[bins] > min_peak_hz) & (f[bins] < 1800)]
    return dict(fir=fir, fs=FS, zc=zc, peaks=f[bins], peak_magnitudes=abs(zin[bins]))
