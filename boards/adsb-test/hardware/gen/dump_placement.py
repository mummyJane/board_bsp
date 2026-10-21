#!/usr/bin/env python3
"""Read the saved ADSB_Test PCB and write the per-page PLACE arrays used by gen_pcb.py.

Run with KiCad's own Python (it needs pcbnew), from the repo root:
    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" boards/adsb-test/hardware/gen/dump_placement.py           # print
    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" boards/adsb-test/hardware/gen/dump_placement.py --write   # update gen_pcb.py in place
    ... dump_placement.py --rebuild   # rewrite the whole PLACE block (after adding parts to the schematic)

Every part gets a line in its page's list, in gen_pcb.py's coordinates ("REF", x, y, rot): footprint
origin in mm from the board's top-right corner as seen in KiCad's normal view (x to the left, y down),
rot = the orientation KiCad shows. --write also refreshes the numbers in BIG and EDGE_*.
* Parts on the board are written uncommented (gen_pcb.py places them).
* Parts off the board (parked) are written commented out, with their current position.
* Parts placed by EDGE_* / BIG and the corner holes get a reference comment only.
Use it after moving parts in KiCad (save first), so re-running gen_pcb.py keeps the moves.
"""
import argparse
import re
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_pcb as g  # noqa: E402

BEGIN, END = "# >>> PLACE", "# <<< PLACE"
ORDER = ["U", "Q", "D", "L", "FB", "Y", "J", "SW", "BT", "SH", "RS", "R", "C", "TP", "JP", "H"]


def ref_key(ref):
    pre, num = re.match(r"([A-Z]+)(\d+)", ref).groups()
    return (ORDER.index(pre) if pre in ORDER else 99, int(num))


def block():
    comps, _ = g.netlist()
    sheet_of = {c["ref"]: c["sheet"] for c in comps}
    value_of = {c["ref"]: c["value"] for c in comps}
    board = pcbnew.LoadBoard(str(g.PCB))
    pos = {}
    for fp in board.GetFootprints():
        p = fp.GetPosition()
        x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        bx, by = g.OX + g.W - x, y - g.OY
        on_board = 0 <= bx <= g.W and 0 <= by <= g.H
        pos[fp.GetReference()] = (bx, by, round(fp.GetOrientationDegrees(), 1) % 360, on_board)

    pages = {}
    for ref, sheet in sheet_of.items():
        num = int(re.sub(r"\D", "", ref) or 0)
        pages.setdefault(sheet, []).append(ref)
    page_no = {s: min(int(re.sub(r"\D", "", r) or 0) // 100 for r in refs) for s, refs in pages.items()}

    lines = [BEGIN + " (rewritten by dump_placement.py --write; edit freely, keep the markers)", "PLACE = {"]
    placed = parked = 0
    for sheet in sorted(pages, key=lambda s: (page_no[s], s)):
        lines.append(f"    # ------------------------------------------------ page {page_no[sheet]}: {sheet}")
        lines.append(f'    "{sheet}": [')
        for ref in sorted(pages[sheet], key=ref_key):
            val = value_of.get(ref, "")
            if ref in g.EDGE:
                lines.append(f"        # {ref}: placed by EDGE_{ {'L': 'LEFT', 'R': 'RIGHT', 'T': 'TOP'}[g.EDGE[ref][0]] }"
                             f"  ({val})")
                continue
            if ref in g.BIG:
                lines.append(f"        # {ref}: placed by BIG  ({val})")
                continue
            if ref.startswith("H16"):
                lines.append(f"        # {ref}: corner mounting hole")
                continue
            if ref not in pos:
                lines.append(f"        # {ref}: not on the PCB yet (run gen_pcb.py)  ({val})")
                continue
            bx, by, rot, on_board = pos[ref]
            entry = f'("{ref}", {bx:.2f}, {by:.2f}, {rot:g}),'
            if on_board:
                lines.append(f"        {entry:<36} # {val}")
                placed += 1
            else:
                lines.append(f"        # {entry:<34} # {val}")
                parked += 1
        lines.append("    ],")
    lines += ["}", END]
    return "\n".join(lines), placed, parked, pos


def fmt(v):
    """Short number: 33.0, 34.75, 180 (rotation)."""
    s = f"{v:.2f}".rstrip("0")
    return s + "0" if s.endswith(".") else s


def same(text_numbers, values):
    """True when the numbers already written equal the board's (to 0.01 mm / 0.1 deg)."""
    try:
        old = [float(t) for t in re.findall(r"-?\d+(?:\.\d+)?", text_numbers)]
    except ValueError:
        return False
    return len(old) == len(values) and all(abs(a - b) < 0.006 or abs((a - b) % 360) < 0.06 for a, b in zip(old, values))


def update_big_and_edges(src, pos):
    """Refresh the numbers in BIG and EDGE_* in place, only where they changed (comments and layout kept)."""
    n = 0
    for ref in g.BIG:
        if ref in pos and pos[ref][3]:
            x, y, rot, _ = pos[ref]
            m = re.search(rf'("{ref}":\s*)\(([^)]*)\)', src)
            if m and not same(m.group(2), (x, y, rot)):
                src = src[:m.start()] + f"{m.group(1)}({fmt(x)}, {fmt(y)}, {rot:g})" + src[m.end():]
                n += 1
    for ref, (side, _) in g.EDGE.items():
        if ref in pos and pos[ref][3]:
            v = pos[ref][0] if side == "T" else pos[ref][1]
            m = re.search(rf'\("{ref}",\s*([-\d.]+)\)', src)
            if m and not same(m.group(1), (v,)):
                src = src[:m.start()] + f'("{ref}", {fmt(v)})' + src[m.end():]
                n += 1
    return src, n


def update_place(src, pos):
    """Edit the PLACE lines in place, only where something changed: new numbers, commented out when off the
    board, uncommented when on it. Spacing, blank lines and trailing comments are kept.
    Returns (text, changed, placed, refs not found)."""
    i, j = src.index(BEGIN), src.index(END)
    body = src[i:j]
    changed = placed = 0
    missing = []
    for ref, (x, y, rot, on_board) in pos.items():
        if ref in g.EDGE or ref in g.BIG or ref.startswith("H16"):
            continue
        pat = re.compile(rf'^(?P<ind>[ \t]*)(?P<hash>#[ \t]*)?\("{ref}",(?P<nums>[^)]*)\),?(?P<rest>.*)$', re.M)
        m = pat.search(body)
        if not m:
            missing.append(ref)
            continue
        placed += on_board
        if not on_board and m["hash"]:
            continue                                     # still parked: parking spots shift, leave the line alone
        if on_board and not m["hash"] and same(m["nums"], (x, y, rot)):
            continue                                     # already right: leave the line exactly as written
        entry = f'("{ref}", {fmt(x)}, {fmt(y)}, {rot:g}),'
        line = f"{m['ind']}{'' if on_board else '# '}{entry}{m['rest']}"
        body = body[:m.start()] + line + body[m.end():]
        changed += 1
    return src[:i] + body + src[j:], changed, placed, missing


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true",
                    help="update gen_pcb.py in place: numbers in PLACE, BIG and EDGE_*, comment state of PLACE lines")
    ap.add_argument("--rebuild", action="store_true",
                    help="rewrite the whole PLACE block (needed after parts are added to the schematic; "
                         "loses hand formatting in PLACE)")
    a = ap.parse_args()
    text, placed, parked, pos = block()
    if not (a.write or a.rebuild):
        print(text)
        return
    src = Path(g.__file__)
    s = src.read_text(encoding="utf-8")
    if a.rebuild:
        i, j = s.index(BEGIN), s.index(END) + len(END)
        s = s[:i] + text + s[j:]
        missing, changed = [], "all"
    else:
        s, changed, placed, missing = update_place(s, pos)
    s, n = update_big_and_edges(s, pos)
    src.write_text(s, encoding="utf-8", newline="\n")
    print(f"{src.name}: {placed} parts placed by PLACE ({changed} PLACE lines changed), "
          f"{n} BIG/EDGE entries changed")
    if missing:
        print("  not in PLACE (new parts? run with --rebuild):", " ".join(sorted(missing, key=ref_key)))


if __name__ == "__main__":
    main()
