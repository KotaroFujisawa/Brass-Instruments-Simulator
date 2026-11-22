"""Profile of the B-flat Červený flugelhorn, with a reconstructed FH-11F4."""
from functools import cache
from numbers import Integral

from axisymmetric_mesh import annular_mesh
from trumpet import C, ROOT, np, optimize
from scipy.interpolate import PchipInterpolator


BORE = ROOT/'data/flugelhorn_cerveny_eu3664_fig7_20.csv'
MOUTHPIECE = ROOT/'data/yamaha_fh11f4_reconstructed.csv'
BORE_SOURCE = 'Červený B-flat flugelhorn, EU 3664; Campbell et al. Fig. 7.20, Myers Appendix I'
MOUTHPIECE_SOURCE = 'Yamaha FH-11F4 rim and throat specifications, estimated U cup and backbore'
BODY_LENGTH_M = 1.340
BELL_RADIUS_M = .0695
MOUTHPIECE_LENGTH_M = .0720
THROAT_START_M = .0225
THROAT_END_M = .0270
SHANK_INSERTION_M = .018
ADAPTER_LENGTH_M = .004
VALVE_WINDOW_M = (.105,.235)
VALVE_SEMITONES = {1:2, 2:1, 3:3, 4:3}
NOMINAL_LENGTH_M = C/(2*440*2**((46-69)/12))
LIPS = dict(width=.0075,thickness=.0022,joint=.0043,rest_x=.00118,
            mass_product=1.85,quality=4.,cup_area=np.pi*.00823**2)


@cache
def _profiles():
    z,r = np.loadtxt(BORE,delimiter=',',skiprows=1).T
    zm,rm = np.loadtxt(MOUTHPIECE,delimiter=',',skiprows=1).T

    # Fig. 7.20 omits the wide part of the flare. Fit a Bessel continuation
    # matching the digitized terminal slope and the independently reported
    # axial length and bell diameter of the same instrument.
    slope = float(np.polyfit(z[-5:],r[-5:],1)[0])
    length = BODY_LENGTH_M-z[-1]
    ratio = BELL_RADIUS_M/r[-1]
    exponent = optimize.brentq(lambda m:m*r[-1]*(1.-ratio**(-1./m))/length-slope,.02,10.)
    apex_distance = exponent*r[-1]/slope
    bell_z = np.linspace(z[-1],BODY_LENGTH_M,35)[1:]
    bell_r = r[-1]*(1.-(bell_z-z[-1])/apex_distance)**(-exponent)
    bell_r[-1] = BELL_RADIUS_M
    return np.r_[z,bell_z],np.r_[r,bell_r],zm,rm


def valve_extension(valves=()):
    """Add the independent tuning loops for the selected valve numbers."""
    valves = tuple(valves)
    if len(set(valves))!=len(valves) or any(
            not isinstance(v,Integral) or isinstance(v,bool) or v not in VALVE_SEMITONES
            for v in valves):
        raise ValueError('Select distinct valve numbers from 1 through 4.')
    return NOMINAL_LENGTH_M*sum(2**(VALVE_SEMITONES[v]/12)-1 for v in valves)


def profile(valves=(),tuning=0.):
    """Return the windway radius at axial stations measured from the lips."""
    z,r,zm,rm = _profiles()
    first,last = VALVE_WINDOW_M
    added_length = valve_extension(valves)+tuning
    if not np.isfinite(added_length) or added_length<=first-last:
        raise ValueError('Tuning must leave a positive length through the valve section.')
    # The mouthpiece shank occupies the front of the receiver. The insertion
    # and the short transition to the measured body are estimates.
    start = SHANK_INSERTION_M+ADAPTER_LENGTH_M
    body_stations = np.unique(np.r_[start,first,last,z[z>start]])
    body_radius = PchipInterpolator(z,r)(body_stations)
    body_z = body_stations+added_length*np.clip((body_stations-first)/(last-first),0.,1.)
    body_z += MOUTHPIECE_LENGTH_M-SHANK_INSERTION_M
    return np.r_[zm,body_z],np.r_[rm,body_radius]


def refined_flugelhorn_mesh(valves=(),tuning=0., *, axial_scale=1.,dr=.006):
    """Refine the mouthpiece, rotor section and flare on a concentric mesh."""
    return _mesh(tuple(sorted(valves)),tuning,axial_scale,dr)


@cache
def _mesh(valves,tuning,axial_scale,dr):
    if not all(np.isfinite(value) and value>0. for value in (axial_scale,dr)):
        raise ValueError('Mesh spacing must be positive and finite.')
    z,r = profile(valves,tuning)
    end = float(z[-1])
    valve_start = MOUTHPIECE_LENGTH_M-SHANK_INSERTION_M+VALVE_WINDOW_M[0]
    valve_end = MOUTHPIECE_LENGTH_M-SHANK_INSERTION_M+VALVE_WINDOW_M[1]+valve_extension(valves)+tuning
    anchors = np.array([0.,.006,THROAT_START_M,THROAT_END_M,MOUTHPIECE_LENGTH_M,
                        MOUTHPIECE_LENGTH_M+ADAPTER_LENGTH_M,valve_start,valve_end,
                        end-.34,end-.155,end-.035,end])
    spacing = axial_scale*np.array([.0015,.0017,.0023,.0036,.002,.0052,.0065,.0065,
                                    .005,.0039,.0027])
    count = np.ceil(np.diff(anchors)/spacing).astype(int)
    edges = np.r_[np.concatenate([np.linspace(a,b,n+1)[:-1]
                                 for a,b,n in zip(anchors[:-1],anchors[1:],count)]),end]
    radius = PchipInterpolator(z,r)(edges)
    grid = annular_mesh(edges,radius,dr)
    grid.update(bore_profile=BORE.name,bore_source=BORE_SOURCE,
                mouthpiece_profile=MOUTHPIECE.name,mouthpiece_source=MOUTHPIECE_SOURCE,
                mouthpiece_length_m=MOUTHPIECE_LENGTH_M,
                mouthpiece_throat_radius_m=float(np.min(r[z<=MOUTHPIECE_LENGTH_M])),
                valve_length_m=valve_extension(valves),tuning_m=tuning)
    return grid
