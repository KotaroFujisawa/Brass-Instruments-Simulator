"""Seven-key Halari C bugle reconstruction with a B-flat terminal crook."""
from functools import cache
from numbers import Integral

from axisymmetric_mesh import annular_mesh
from trumpet import C, ROOT, np
from scipy.interpolate import PchipInterpolator


BORE = ROOT/'data/keyed_bugle_halari_eu907.csv'
PORTS = ROOT/'data/keyed_bugle_toneholes_06872.csv'
BORE_SOURCE = (
    'Halari keyed bugle EU907: Campbell, Gilbert & Myers Fig. 7.20; '
    '1205 mm length from Myers instrument catalogue; modeled flare to 148 mm bell'
)
PORT_SOURCE = (
    'National Music Museum C seven-key bugle NMM 06872: measured offsets from the bell '
    'and aperture diameters transferred to the Halari bore; chimney heights estimated'
)
MOUTHPIECE_SOURCE = (
    'Funnel and backbore approximated from Birmingham City University collection 13.3'
)
MOUTHPIECE_LENGTH_M = .070
CUP_DEPTH_M = .0142
THROAT_END_M = .0174
THROAT_RADIUS_M = .002
ADAPTER_LENGTH_M = .004
CROOK_LENGTH_M = .5*C*(1/(440*2**((46-69)/12))-1/(440*2**((48-69)/12)))
DEFAULT_OPEN_HOLES = (1,)
LIPS = dict(width=.0075,thickness=.0021,joint=.0043,rest_x=.001,
            mass_product=1.75,quality=4.2,cup_area=np.pi*.0081**2)


@cache
def _bore():
    return np.loadtxt(BORE,delimiter=',',skiprows=1,usecols=(0,1)).T


@cache
def _ports():
    return np.loadtxt(PORTS,delimiter=',',skiprows=1)[:,1:]


def _crook_end(tuning):
    length = CROOK_LENGTH_M+tuning
    if not np.isfinite(length) or length<=.015:
        raise ValueError('Keyed-bugle tuning must leave at least 15 mm of crook.')
    return MOUTHPIECE_LENGTH_M+ADAPTER_LENGTH_M+length


def open_toneholes(open_holes=DEFAULT_OPEN_HOLES, tuning=0.):
    """Return open ports as (location from lips, radius, chimney height)."""
    numbers = tuple(open_holes)
    if (len(set(numbers))!=len(numbers) or any(
            not isinstance(n,Integral) or isinstance(n,bool) or not 1<=n<=len(_ports())
            for n in numbers)):
        raise ValueError('Open holes must be distinct numbers from 1 through 7.')
    bell = _crook_end(tuning)+_bore()[0][-1]
    return tuple((bell-offset,r,h) for offset,r,h in
                 (_ports()[number-1] for number in sorted(numbers)))


def profile(tuning=0.):
    """Return the complete pipe profile, beginning at the mouthpiece rim."""
    z_bore,r_bore = _bore()
    end = _crook_end(tuning)
    z_mouth = np.array([0.,.0012,.0035,.0060,.0090,.0115,.0131,CUP_DEPTH_M,
                        THROAT_END_M,.027,.040,.055,MOUTHPIECE_LENGTH_M])
    r_mouth = np.array([.0081,.0077,.0067,.0056,.0043,.0032,.0025,THROAT_RADIUS_M,
                        THROAT_RADIUS_M,.00215,.0027,.00345,.0043])
    return (np.r_[z_mouth,MOUTHPIECE_LENGTH_M+ADAPTER_LENGTH_M,end+z_bore],
            np.r_[r_mouth,r_bore[0],r_bore])


def refined_keyed_bugle_mesh(open_holes=DEFAULT_OPEN_HOLES, tuning=0., *, axial_scale=1.,dr=.006):
    """Straighten the axial curve and embed the physical aperture wall patches."""
    return _mesh(tuple(sorted(open_holes)),tuning,axial_scale,dr)


@cache
def _mesh(open_holes,tuning,axial_scale,dr):
    if not all(np.isfinite(value) and value>0. for value in (axial_scale,dr)):
        raise ValueError('Mesh spacing must be positive and finite.')
    holes = open_toneholes(open_holes,tuning)
    x,r = profile(tuning)
    end = float(x[-1])
    anchors = [0.,CUP_DEPTH_M,THROAT_END_M,MOUTHPIECE_LENGTH_M,
               MOUTHPIECE_LENGTH_M+ADAPTER_LENGTH_M,_crook_end(tuning),
               end-.25,end-.080,end-.026,end]
    spacing = np.array([.0028,.0017,.0034,.004,.008,.008,.006,.004,.0028])*axial_scale
    pieces = [np.linspace(a,b,1+int(np.ceil((b-a)/step)))[:-1]
              for a,b,step in zip(anchors[:-1],anchors[1:],spacing)]
    z = np.concatenate([*pieces,[end]])
    radius = PchipInterpolator(x,r)(z)
    radius[-1] = r[-1]
    mesh = annular_mesh(z,radius,dr,toneholes=holes)
    mesh.update(bore_profile=BORE.name,mouthpiece_profile=MOUTHPIECE_SOURCE,
                mouthpiece_length_m=MOUTHPIECE_LENGTH_M,mouthpiece_throat_radius_m=THROAT_RADIUS_M,
                open_hole_numbers=open_holes,nominal_crook_length_m=CROOK_LENGTH_M,tuning_m=tuning)
    return mesh
