"""Axisymmetric bore of an E-flat tenor saxhorn with a reconstructed mouthpiece."""
from functools import cache
from numbers import Integral

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

from axisymmetric_mesh import annular_mesh
from trumpet import C, ROOT


BORE = ROOT / 'data/tenor_horn_sax_eu4543_fig7_26.csv'
MOUTHPIECE = ROOT / 'data/yamaha_ah38d4_reconstructed.csv'
BORE_SOURCE = 'Adolphe Sax E-flat tenor saxhorn, EU 4543; Campbell et al. Fig. 7.26'
MOUTHPIECE_SOURCE = 'Yamaha AH-38D4 rim and throat dimensions; reconstructed cup and backbore'
BODY_LENGTH_M = 2.030
BELL_RADIUS_M = .105
SHANK_INSERTION_M = .018
RECEIVER_LENGTH_M = .004
THROAT_LIMITS_M = (.0255, .0305)
VALVE_WINDOW_M = (.425, .795)
VALVE_SEMITONES = {1: 2, 2: 1, 3: 3}
EB2_HZ = 440 * 2**((39 - 69) / 12)
NOMINAL_LENGTH_M = C / (2 * EB2_HZ)
LIPS = dict(width=.0086, thickness=.00245, joint=.0049, rest_x=.00127,
            mass_product=2.35, quality=4., cup_area=np.pi * (.0189 / 2)**2)


@cache
def _profiles():
    z, radius = np.loadtxt(BORE, delimiter=',', skiprows=1).T
    mouthpiece = np.loadtxt(MOUTHPIECE, delimiter=',', skiprows=1).T

    # The printed figure stops partway through the bell. Continue the measured
    # slope with a Bessel flare to the assumed body length and modern bell size.
    slope = float(np.polyfit(z[-5:], radius[-5:], 1)[0])
    length = BODY_LENGTH_M - z[-1]
    ratio = BELL_RADIUS_M / radius[-1]
    exponent = brentq(
        lambda m: m * radius[-1] * (1 - ratio**(-1 / m)) / length - slope,
        .02, 10.,
    )
    flare_scale = exponent * radius[-1] / slope
    bell_radius = np.geomspace(radius[-1], BELL_RADIUS_M, 32)[1:]
    bell_z = z[-1] + flare_scale * (1 - (radius[-1] / bell_radius)**(1 / exponent))
    bell_z[-1] = BODY_LENGTH_M
    return (np.r_[z, bell_z], np.r_[radius, bell_radius]), mouthpiece


def valve_extension(valves):
    """Sum the independent first, second and third valve loops."""
    valves = tuple(valves)
    if any(not isinstance(v, Integral) or isinstance(v, bool) or v not in VALVE_SEMITONES
           for v in valves) or len(set(valves)) != len(valves):
        raise ValueError('Select distinct valve numbers from 1 through 3.')
    return NOMINAL_LENGTH_M * sum(2**(VALVE_SEMITONES[v] / 12) - 1 for v in valves)


def profile(valves=(), tuning=0.):
    """Return axial stations and windway radii in metres from the plane of the lips."""
    return _windway(valve_extension(valves) + tuning)


def _windway(extension):
    (zb, rb), (zm, rm) = _profiles()
    first, last = VALVE_WINDOW_M
    if not np.isfinite(extension) or extension <= first - last:
        raise ValueError('Tuning must leave a positive length in the valve section.')
    # The inserted shank replaces the corresponding length of the measured
    # receiver. Keep a short smooth join between the shank exit and leadpipe.
    start = SHANK_INSERTION_M + RECEIVER_LENGTH_M
    body_stations = np.r_[start, zb[zb > start]]
    body_radius = PchipInterpolator(zb, rb)(body_stations)
    valve_fraction = np.clip((body_stations - first) / (last - first), 0., 1.)
    body_z = body_stations + extension * valve_fraction + zm[-1] - SHANK_INSERTION_M
    return np.r_[zm, body_z], np.r_[rm, body_radius]


def refined_tenor_horn_mesh(valves=(), tuning=0., *, axial_scale=1., dr=.006):
    """Discretize the complete mouthpiece, leadpipe, valve block and flare."""
    valve_length = valve_extension(valves)
    return _mesh(valve_length, tuning, axial_scale, dr)


@cache
def _mesh(valve_length, tuning, axial_scale, dr):
    if not all(np.isfinite(value) and value > 0. for value in (axial_scale, dr)):
        raise ValueError('Mesh spacing must be positive and finite.')
    z, radius = _windway(valve_length + tuning)
    mouthpiece_end = float(_profiles()[1][0][-1])
    end = float(z[-1])
    body_offset = mouthpiece_end - SHANK_INSERTION_M
    first, last = VALVE_WINDOW_M
    anchors = np.array([
        0., .006, *THROAT_LIMITS_M, mouthpiece_end, mouthpiece_end + RECEIVER_LENGTH_M,
        body_offset + first, body_offset + last + valve_length + tuning,
        end - .44, end - .14, end - .040, end,
    ])
    spacing = axial_scale * np.array([
        .002, .0024, .0025, .0036, .002, .006, .007, .008, .006, .004, .003,
    ])
    segments = np.ceil(np.diff(anchors) / spacing).astype(int)
    edges = np.r_[np.concatenate([np.linspace(a, b, n + 1)[:-1]
                                  for a, b, n in zip(anchors[:-1], anchors[1:], segments)]), end]
    grid = annular_mesh(edges, PchipInterpolator(z, radius)(edges), dr)
    grid.update(
        bore_profile=BORE.name, mouthpiece_profile=MOUTHPIECE.name,
        bore_source=BORE_SOURCE, mouthpiece_source=MOUTHPIECE_SOURCE,
        mouthpiece_length_m=mouthpiece_end,
        mouthpiece_throat_radius_m=float(radius[z <= mouthpiece_end].min()),
        receiver_length_m=RECEIVER_LENGTH_M, valve_length_m=valve_length, tuning_m=tuning,
    )
    return grid
