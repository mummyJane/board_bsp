#!/usr/bin/env python3
"""Closed-form trace impedance for an outer layer over its inner ground plane (starting values; the fab's
impedance control does the final tuning).

  microstrip   IPC-2141 (with copper thickness) and Hammerstad-Jensen (thin strip) side by side
  diff pair    edge-coupled microstrip, IPC-2141: Zd = 2 Z0 (1 - 0.48 exp(-0.96 S/H))
  CPWG         coplanar waveguide with bottom ground, Wadell (conformal mapping, thin strip)

Solder mask lowers all of these by roughly 2-3 ohm (not modelled).

Usage: python tools/impedance.py [--h 0.1855] [--er 4.74] [--t 0.035]
Defaults = PCBWay standard 4-layer 1.6 mm (L1-L2 7628 prepreg 0.1855 mm after lamination, Dk 4.74, 1 oz outer).
"""
import argparse
import math


def ellipk(k):
    """Complete elliptic integral of the first kind K(k) via the arithmetic-geometric mean."""
    a, b = 1.0, math.sqrt(1 - k * k)
    while abs(a - b) > 1e-15:
        a, b = (a + b) / 2, math.sqrt(a * b)
    return math.pi / (2 * a)


def ms_ipc(w, h, er, t):
    return 87 / math.sqrt(er + 1.41) * math.log(5.98 * h / (0.8 * w + t))


def ms_hj(w, h, er):
    u = w / h
    a = 1 + math.log((u ** 4 + (u / 52) ** 2) / (u ** 4 + 0.432)) / 49 + math.log(1 + (u / 18.1) ** 3) / 18.7
    b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
    ee = (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a * b)
    f = 6 + (2 * math.pi - 6) * math.exp(-(30.666 / u) ** 0.7528)
    return 60 / math.sqrt(ee) * math.log(f / u + math.sqrt(1 + (2 / u) ** 2))


def diff_ipc(w, s, h, er, t):
    return 2 * ms_ipc(w, h, er, t) * (1 - 0.48 * math.exp(-0.96 * s / h))


def cpwg(w, g, h, er):
    k = w / (w + 2 * g)
    k3 = math.tanh(math.pi * w / (4 * h)) / math.tanh(math.pi * (w + 2 * g) / (4 * h))
    r1 = ellipk(math.sqrt(1 - k * k)) / ellipk(k)
    r3 = ellipk(k3) / ellipk(math.sqrt(1 - k3 * k3))
    ee = (1 + er * r3 * r1) / (1 + r3 * r1)        # Wadell: eeff = (1 + er K(k')/K(k) K(k3)/K(k3')) / (1 + ...)
    return 60 * math.pi / math.sqrt(ee) / (1 / r1 + r3)


def solve(f, target, lo=0.05, hi=1.5):
    """Width where f(width) == target (f falls as the width grows)."""
    for _ in range(80):
        mid = (lo + hi) / 2
        if f(mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--h", type=float, default=0.1855, help="dielectric to the reference plane, mm")
    ap.add_argument("--er", type=float, default=4.74)
    ap.add_argument("--t", type=float, default=0.035, help="copper thickness, mm")
    a = ap.parse_args()
    h, er, t = a.h, a.er, a.t
    print(f"H = {h} mm, Er = {er}, T = {t} mm\n")
    w = solve(lambda x: ms_ipc(x, h, er, t), 50)
    print(f"50 ohm microstrip:  W = {w:.3f} mm (IPC-2141); Hammerstad-Jensen gives {ms_hj(w, h, er):.1f} ohm at that W")
    for name, zd, gaps in (("90 ohm diff (USB)", 90, (0.127, 0.15, 0.2)),
                           ("100 ohm diff (MIPI, Ethernet)", 100, (0.127, 0.15, 0.2))):
        for s in gaps:
            w = solve(lambda x: diff_ipc(x, s, h, er, t), zd)
            print(f"{name:30s} S = {s:.3f} -> W = {w:.3f} mm")
    for g in (0.15, 0.2, 0.25):
        w = solve(lambda x: cpwg(x, g, h, er), 50, lo=0.05, hi=3.0)
        print(f"50 ohm CPWG (RF)               G = {g:.3f} -> W = {w:.3f} mm")


if __name__ == "__main__":
    main()
