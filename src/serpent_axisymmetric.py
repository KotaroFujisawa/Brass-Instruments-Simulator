"""Axisymmetric reconstruction of a six-hole bass serpent from bore drawings."""
from functools import cache
from numbers import Integral

from axisymmetric_mesh import annular_mesh
from trumpet import ROOT, np


BORE = ROOT/'data/serpent_bore_fig456.csv'
MOUTHPIECE = ROOT/'data/serpent_mouthpiece_fig755a.csv'
TONEHOLES = ROOT/'data/serpent_toneholes_reconstructed.csv'
BORE_SOURCE = 'Campbell, Gilbert & Myers, The Science of Brass Instruments, Fig. 4.56'
MOUTHPIECE_SOURCE = 'Campbell, Gilbert & Myers, The Science of Brass Instruments, Fig. 7.55(a)'
HOLE_SOURCE = (
    'Fig. 4.56 for hole 1, spacing and nominal diameter reconstructed from '
    'National Music Museum Baudouin NMM 07123; estimated 7 mm axial chimney height'
)
MOUTHPIECE_LENGTH_M = .0438
THROAT_START_M = .0177
THROAT_END_M = .0209
ADAPTER_LENGTH_M = .003
BORE_START_M = MOUTHPIECE_LENGTH_M+ADAPTER_LENGTH_M
DEFAULT_OPEN_HOLES = ()
LIPS = dict(width=.011,thickness=.003,joint=.0060,rest_x=.0014,
            mass_product=4.6,quality=4.5,cup_area=np.pi*.01555**2)


@cache
def _station_data(path):
    return np.loadtxt(path,delimiter=',',skiprows=1).T


def book_profile():
    """The three straight cones of Fig. 4.56, excluding the mouthpiece."""
    return _station_data(BORE).copy()


def _bore_scale(tuning):
    bore_length = _station_data(BORE)[0,-1]
    scale = 1.+tuning/bore_length
    if not np.isfinite(scale) or scale<=0.:
        raise ValueError('Tuning must leave a positive serpent bore length.')
    return scale


def _hole_stations(open_holes):
    columns = _station_data(TONEHOLES)
    ids = tuple(open_holes)
    if len(set(ids))!=len(ids) or any(
            not isinstance(n,Integral) or isinstance(n,bool) or not 1<=n<=len(columns[0])
            for n in ids):
        raise ValueError('Open holes must be distinct numbers from 1 through 6.')
    return columns[1:,np.asarray(sorted(ids),dtype=int)-1].T


def book_toneholes(open_holes=DEFAULT_OPEN_HOLES):
    """Open ports as (centerline from crook entrance, radius, chimney height)."""
    return tuple(tuple(row) for row in _hole_stations(open_holes))


def open_toneholes(open_holes=DEFAULT_OPEN_HOLES,tuning=0., *, opening_fractions=()):
    """Open ports in the complete domain, from the lip plane rather than the crook."""
    open_holes = tuple(sorted(open_holes))
    stations = book_toneholes(open_holes)
    fractions = dict(opening_fractions)
    if len(fractions)!=len(opening_fractions) or fractions.keys()-set(open_holes) or any(
            not 0.<area<=1. for area in fractions.values()):
        raise ValueError('Give at most one positive opening area fraction per open hole, up to 1.')
    scale = _bore_scale(tuning)
    # A circular port of the same area approximates the uncovered part of the hole.
    return tuple((BORE_START_M+scale*z,r*np.sqrt(fractions.get(number,1.)),h)
                 for number,(z,r,h) in zip(open_holes,stations))


def profile(tuning=0.):
    """Mouthpiece, a short adapter and the original piecewise-conical bore."""
    x,r = _station_data(MOUTHPIECE)
    z_bore,r_bore = book_profile()
    return np.r_[x,BORE_START_M+_bore_scale(tuning)*z_bore],np.r_[r,r_bore]


def refined_serpent_mesh(open_holes=DEFAULT_OPEN_HOLES,tuning=0., *, axial_scale=1.,dr=.006,
                         opening_fractions=()):
    """Straighten the centreline and distribute open ports over annular wall faces."""
    open_holes = tuple(open_holes)
    _hole_stations(open_holes)
    fractions = tuple(tuple(item) for item in opening_fractions)
    return _mesh(tuple(sorted(open_holes)),tuning,axial_scale,dr,fractions)


@cache
def _mesh(open_holes,tuning,axial_scale,dr,opening_fractions):
    if not all(np.isfinite(value) and value>0. for value in (axial_scale,dr)):
        raise ValueError('Mesh spacing must be positive and finite.')
    holes = open_toneholes(open_holes,tuning,opening_fractions=opening_fractions)
    x,r = profile(tuning)
    bore_joints = BORE_START_M+_bore_scale(tuning)*_station_data(BORE)[0,1:]
    anchors = np.r_[0.,THROAT_START_M,THROAT_END_M,MOUTHPIECE_LENGTH_M,BORE_START_M,
                    bore_joints[:-1],x[-1]-.16,x[-1]-.04,x[-1]]
    if np.any(np.diff(anchors)<=0.):
        raise ValueError('Tuning must leave sufficient length before the serpent outlet.')
    spacing = axial_scale*np.array([.0025,.0023,.0032,.003,.009,.009,.009,.006,.0045])
    z = np.concatenate([np.linspace(a,b,1+int(np.ceil((b-a)/step)))[:-1]
                        for a,b,step in zip(anchors[:-1],anchors[1:],spacing)]+[[x[-1]]])
    mesh = annular_mesh(z,np.interp(z,x,r),dr,toneholes=holes)
    mesh.update(bore_profile=BORE.name,mouthpiece_profile=MOUTHPIECE.name,
                mouthpiece_length_m=MOUTHPIECE_LENGTH_M,
                mouthpiece_throat_radius_m=float(_station_data(MOUTHPIECE)[1].min()),
                open_hole_numbers=open_holes,tuning_m=tuning)
    return mesh
