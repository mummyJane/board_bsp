#!/usr/bin/env python3
"""Read the saved ADSB_Test PCB and write the per-page PLACE arrays used by gen_pcb.py.

Run with KiCad's own Python (it needs pcbnew), from the repo root:
    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" boards/adsb-test/hardware/gen/dump_placement.py           # print
    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" boards/adsb-test/hardware/gen/dump_placement.py --write   # update gen_pcb.py

Every part gets a line in its page's list, in the bottom-view coordinates gen_pcb.py uses
("REF", bx, by, rotation): bx, by = footprint origin in mm from the board corner (bx from the left/RF
edge, by down from the top edge); rotation = the orientation KiCad shows.
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
    return "\n".join(lines), placed, parked


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="replace the PLACE block in gen_pcb.py")
    a = ap.parse_args()
    text, placed, parked = block()
    if not a.write:
        print(text)
        return
    src = Path(g.__file__)
    s = src.read_text(encoding="utf-8")
    i, j = s.index(BEGIN), s.index(END) + len(END)
    src.write_text(s[:i] + text + s[j:], encoding="utf-8", newline="\n")
    print(f"PLACE in {src.name}: {placed} placed, {parked} parked (commented out)")


if __name__ == "__main__":
    main()
