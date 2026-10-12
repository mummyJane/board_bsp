#!/usr/bin/env python3
"""Add (or replace) a simple box symbol in a KiCad 10 symbol library.

    from kicad_sym_make import add_box_symbol
    add_box_symbol(lib_path, "AP3032", ref="U", value="AP3032",
                   left=[("6", "IN", "power_in"), ...], right=[("1", "SW", "output"), ...],
                   footprint="Package_TO_SOT_SMD:SOT-23-6", datasheet=url, description="...")

Pins are spaced 2.54 mm; the box width fits the longest pin names. Run
`kicad-cli sym upgrade --force <lib>` afterwards to normalise the formatting.
"""
import re
from pathlib import Path


def _q(s):
    return '"' + s.replace('"', '\\"') + '"'


def _prop(name, value, at, hide=False):
    h = " (hide yes)" if hide else ""
    return f"(property {_q(name)} {_q(value)} (at {at[0]:.2f} {at[1]:.2f} 0){h} (effects (font (size 1.27 1.27))))"


def add_box_symbol(lib_path, name, ref, value, left, right, footprint="", datasheet="", description="",
                   keywords="", step=2.54, length=2.54):
    rows = max(len(left), len(right))
    longest = max([len(p[1]) for p in left + right] + [4])
    half_w = max(5.08, round((longest * 1.27 * 2 + 2.54) / 2 / 2.54) * 2.54)
    top = (rows + 1) * step / 2
    top = round(top / 1.27) * 1.27
    pins = []
    for side, plist in (("L", left), ("R", right)):
        for i, (num, pname, typ) in enumerate(plist):
            y = top - (i + 1) * step
            x, rot = (-half_w - length, 0) if side == "L" else (half_w + length, 180)
            pins.append(f"(pin {typ} line (at {x:.2f} {y:.2f} {rot}) (length {length}) "
                        f"(name {_q(pname)} (effects (font (size 1.27 1.27)))) "
                        f"(number {_q(num)} (effects (font (size 1.27 1.27)))))")
    bottom = top - (rows + 1) * step
    sym = (f"(symbol {_q(name)} (exclude_from_sim no) (in_bom yes) (on_board yes) "
           + _prop("Reference", ref, (-half_w, top + 1.27)) + _prop("Value", value, (half_w - 5, top + 1.27))
           + _prop("Footprint", footprint, (0, 0), True) + _prop("Datasheet", datasheet, (0, 0), True)
           + _prop("Description", description, (0, 0), True) + _prop("ki_keywords", keywords, (0, 0), True)
           + f"(symbol {_q(name + '_0_1')} (rectangle (start {-half_w:.2f} {top:.2f}) (end {half_w:.2f} {bottom:.2f}) "
             "(stroke (width 0.254) (type default)) (fill (type background))))"
           + f"(symbol {_q(name + '_1_1')} " + " ".join(pins) + "))")

    lib_path = Path(lib_path)
    text = lib_path.read_text(encoding="utf-8")
    m = re.search(r'\n\s*\(symbol "%s"\s' % re.escape(name), text)
    if m:   # replace the previous copy (balanced-paren block)
        start = text.index("(", m.start())
        depth = 0
        for k in range(start, len(text)):
            depth += {"(": 1, ")": -1}.get(text[k], 0)
            if depth == 0:
                text = text[:m.start()] + text[k + 1:]
                break
    text = text.rstrip()
    assert text.endswith(")")
    text = text[:-1].rstrip() + "\n\t" + sym + "\n)\n"
    lib_path.write_text(text, encoding="utf-8", newline="\n")
