"""Utility to draw sinusoidal flat patterns for gored elbows.

This module generates DXF files using ezdxf. The pattern consists of a
sinusoidal wave representing the seam between gores. Two half waves are
used at the ends to represent the half gores typically used in a gored
elbow.
"""

from __future__ import annotations

import argparse
import math

import ezdxf
from ezdxf import units


def draw_gored_elbow(filename: str,
                     diameter: float,
                     clr: float,
                     angle_deg: float,
                     num_gores: int = 5,
                     points_per_gore: int = 40) -> None:
    """Draw a sinusoidal flat pattern for a gored elbow.

    Parameters
    ----------
    filename : str
        Output DXF filename.
    diameter : float
        Diameter of the elbow.
    clr : float
        Center line radius of the elbow.
    angle_deg : float
        Elbow angle in degrees.
    num_gores : int, optional
        Total number of gores including the two half gores at the ends.
    points_per_gore : int, optional
        Number of interpolation points per full gore segment of the
        sinusoidal curve.
    """
    if num_gores < 2:
        raise ValueError("num_gores must be at least 2")

    doc = ezdxf.new()
    doc.units = units.IN
    doc.header['$INSUNITS'] = units.IN
    doc.header['$MEASUREMENT'] = 0
    msp = doc.modelspace()

    # Flat width of the pattern (circumference)
    width = diameter * math.pi
    # Approximate bounding length used in existing GUI logic
    total_length = 2.0 * clr * (angle_deg / 90.0)

    # Length of one full gore along the centerline
    full_gore_length = total_length / (num_gores - 1)
    half_gore_length = full_gore_length / 2.0

    # Simple amplitude heuristic for the sinusoidal edge
    amplitude = diameter / 4.0

    lengths = [half_gore_length] + [full_gore_length] * (num_gores - 2) + [half_gore_length]

    outer = []
    inner = []
    x = 0.0
    for idx, gl in enumerate(lengths):
        steps = max(2, int(points_per_gore * (gl / full_gore_length)))
        for i in range(steps):
            t = i / (steps - 1)
            if idx in (0, num_gores - 1):
                wave_angle = math.pi * t
            else:
                wave_angle = 2.0 * math.pi * t
            offset = amplitude * math.sin(wave_angle)
            outer.append((x + t * gl, width / 2.0 + offset))
            inner.append((x + t * gl, width / 2.0 - offset))
        x += gl

    polyline_points = outer + inner[::-1]
    msp.add_lwpolyline(polyline_points, close=True)
    doc.saveas(filename)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a gored elbow flat pattern DXF")
    parser.add_argument("diameter", type=float, help="Elbow diameter")
    parser.add_argument("clr", type=float, help="Center line radius")
    parser.add_argument("angle", type=float, help="Elbow angle in degrees")
    parser.add_argument("output", help="Output DXF filename")
    parser.add_argument("--gores", type=int, default=5, help="Total number of gores including end halves")
    args = parser.parse_args()
    draw_gored_elbow(args.output, args.diameter, args.clr, args.angle, args.gores)


if __name__ == "__main__":
    main()
