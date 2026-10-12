#!/usr/bin/env python3
"""Make hand-solderable variants of KiCad footprints.

- Edge pads are lengthened outward (away from the body) by EXTEND mm, so a
  soldering-iron tip can touch the pad and the solder can wick underneath.
  Only rect/roundrect pads without rotation, sitting on the outer ring of pads
  and elongated perpendicular to their edge, are changed.
- Optionally, bottom/exposed pads get plated through-holes so they can be
  soldered (or heated) from the back of the board.
- The courtyard is rebuilt around the new pads and the body (F.Fab).

Usage (library):
    from kicad_fp_handsolder import make_handsolder
    make_handsolder(src, dst, name, extend=0.5, holes={"25": [(0, 0, 1.0)]})
holes: {pad name: [(x, y, drill_mm), ...]}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kicad_sch_gen import parse, dump, find, q, unq, uid  # noqa: E402


def _num(v):
    return float(v)


def _fmt(v):
    v = round(v, 4)
    return str(int(v)) if v == int(v) else repr(v)


def make_handsolder(src, dst, name, extend=0.5, holes=None, only_pads=None, descr_note=""):
    tree = parse(Path(src).read_text(encoding="utf-8"))[0]
    tree[1] = q(name)
    pads = find(tree, "pad")

    # outer ring of pads: use the extreme pad centres
    centres = []
    for p in pads:
        at = find(p, "at")[0]
        centres.append((_num(at[1]), _num(at[2])))
    max_x = max(abs(x) for x, _ in centres)
    max_y = max(abs(y) for _, y in centres)

    changed = 0
    for p in pads:
        pname = unq(p[1])
        if not pname or (only_pads is not None and pname not in only_pads):
            continue
        if p[3] not in ("rect", "roundrect"):
            continue
        at = find(p, "at")[0]
        if len(at) > 3 and _num(at[3]) % 180 != 0:
            continue
        x, y = _num(at[1]), _num(at[2])
        size = find(p, "size")[0]
        sx, sy = _num(size[1]), _num(size[2])
        if len(at) > 3 and _num(at[3]) % 180 == 0 and _num(at[3]) != 0:
            pass  # 180 deg: same axes
        if abs(x) >= 0.85 * max_x and sx > sy and abs(x) > 0.5:      # left/right edge pad
            s = 1 if x > 0 else -1
            at[1] = _fmt(x + s * extend / 2)
            size[1] = _fmt(sx + extend)
            changed += 1
        elif abs(y) >= 0.85 * max_y and sy > sx and abs(y) > 0.5:    # top/bottom edge pad
            s = 1 if y > 0 else -1
            at[2] = _fmt(y + s * extend / 2)
            size[2] = _fmt(sy + extend)
            changed += 1

    for pname, spots in (holes or {}).items():
        for (hx, hy, drill) in spots:
            ring = drill + 0.5
            tree.append(["pad", q(pname), "thru_hole", "circle", ["at", _fmt(hx), _fmt(hy)],
                         ["size", _fmt(ring), _fmt(ring)], ["drill", _fmt(drill)],
                         ["layers", '"*.Cu"', '"*.Mask"'], ["uuid", uid()]])

    # rebuild the courtyard around pads + body
    xs, ys = [], []
    for p in find(tree, "pad"):
        at = find(p, "at")[0]
        sz = find(p, "size")[0]
        x, y, w, h = _num(at[1]), _num(at[2]), _num(sz[1]), _num(sz[2])
        if len(at) > 3 and _num(at[3]) % 180 != 0:
            w, h = h, w
        xs += [x - w / 2, x + w / 2]
        ys += [y - h / 2, y + h / 2]
    for g in [x for x in tree if isinstance(x, list) and x and x[0] in ("fp_line", "fp_rect")]:
        layer = find(g, "layer")
        if layer and unq(layer[0][1]) == "F.Fab":
            for k in ("start", "end"):
                pt = find(g, k)
                if pt:
                    xs.append(_num(pt[0][1]))
                    ys.append(_num(pt[0][2]))
    tree[:] = [x for x in tree if not (isinstance(x, list) and x and x[0] in ("fp_line", "fp_rect", "fp_poly", "fp_circle", "fp_arc")
                                       and find(x, "layer") and unq(find(x, "layer")[0][1]) == "F.CrtYd")]
    m = 0.25
    tree.append(["fp_rect", ["start", _fmt(min(xs) - m), _fmt(min(ys) - m)], ["end", _fmt(max(xs) + m), _fmt(max(ys) + m)],
                 ["stroke", ["width", "0.05"], ["type", "solid"]], ["fill", "no"], ["layer", '"F.CrtYd"'], ["uuid", uid()]])

    descr = find(tree, "descr")
    note = f"Hand-solder variant: edge pads +{extend} mm outward" + (", plated holes in bottom pads" if holes else "") + \
           (f". {descr_note}" if descr_note else "")
    if descr:
        descr[0][1] = q(unq(descr[0][1]) + " | " + note)
    else:
        tree.insert(2, ["descr", q(note)])
    Path(dst).write_text(dump(tree) + "\n", encoding="utf-8", newline="\n")
    return changed
