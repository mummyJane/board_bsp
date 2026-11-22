#!/usr/bin/env python3
"""Route the critical nets of ADSB_Test on B.Cu (KiCad's Python):

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" boards/adsb-test/hardware/gen/route_critical.py [nets...]

* RF feeds (RF_50R, 0.32 mm, no vias) + a ground-via fence either side
* crystal nets (0.2 mm, no vias)
* every PWR_HI net (0.8 mm, necking down into fine-pitch pins), short nets first

Everything it adds is LOCKED and in the group ROUTED_BY_SCRIPT: running it again first deletes that group's items
(so it re-routes from scratch after placement changes); gen_pcb.py keeps the group across a rebuild. Give net names
(short form) to route only those. Run gen_pcb.py first; close the board in KiCad (or reload it afterwards).
Nets that do not fit are listed at the end: route those by hand.
"""
import json
import math
import sys
import time
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import copper  # noqa: E402
import gen_pcb as g  # noqa: E402
import router  # noqa: E402

GROUP = "ROUTED_BY_SCRIPT"
RF = ["RF_ADSB_ANT", "WIFI_ANT", "GPS_RF", "M1421_RF_1090", "M1421_RF_978"]
RF_W, RF_FENCE_PITCH, RF_FENCE_OFFSET = 0.32, 1.0, 0.9        # mm; offset = track centre to fence via centre
CRYSTALS = ["ETH_XI", "ETH_XO", "HUB_XI", "HUB_XO", "FT_XI", "FT_XO", "RP_XI", "RP_XO", "RP_XO_R",
            "XTAL32_P", "XTAL32_N"]
XTAL_W = 0.2
PWR_HI_W = 0.8
# power order: switch nodes, then each stage's input before its output (an output routed first walls the input in);
# PWR_HI nets not listed go last, shortest first
PWR_ORDER = ["BL_SW", "B5V_SW", "B3V3_SW", "CHG_SW1", "CHG_SW2", "AVDD_SW", "CHG_PMID", "VSYS_CHG", "VBAT_CHG",
             "VSYS", "VBUS_USER_RAW", "VBUS_USER", "VBUS_CHG", "BAT_PACK", "3V3_BUCK", "5V"]
PWR_HI_NECK = 3.0          # mm round each pad where a power track may neck down
CLEARANCE = 0.2
LAYER = pcbnew.B_Cu
FM, TM = pcbnew.FromMM, pcbnew.ToMM


def short(n):
    return n.split("/")[-1]


def remove_previous(board, only=None):
    """Delete the tracks / vias of the previous run (the ROUTED_BY_SCRIPT group), only those nets' if given (RF
    fence vias go with their RF net). The group itself is kept and re-used."""
    ids = set()
    for grp in board.Groups():
        if grp.GetName() == GROUP:
            ids |= {it.m_Uuid.AsString() for it in grp.GetItems()}
    doomed = [t for t in board.GetTracks() if t.m_Uuid.AsString() in ids]
    if only:
        doomed = [t for t in doomed if short(t.GetNetname()) in only or (
            t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND" and only & set(RF))]
    for t in doomed:
        board.Delete(t)
    if not only:
        for grp in [x for x in board.Groups() if x.GetName() == GROUP]:
            board.Delete(grp)
    return len(doomed)


def auto_items(board):
    """uuid -> item for the generated fan-out vias / stubs (gen_pcb.py's AUTO_* groups): critical nets win."""
    ids = set()
    for grp in board.Groups():
        if grp.GetName().startswith("AUTO_"):
            ids |= {it.m_Uuid.AsString() for it in grp.GetItems()}
    return {t.m_Uuid.AsString(): t for t in board.GetTracks() if t.m_Uuid.AsString() in ids}


def clear_conflicts(board, segs, auto):
    """Delete generated fan-out vias / stubs that the new segments run into (gen_pcb.py puts them back elsewhere)."""
    gone = 0
    for uid, t in list(auto.items()):
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = TM(t.GetPosition().x), TM(t.GetPosition().y)
            geom, half = (x, y, x, y), TM(t.GetWidth(pcbnew.F_Cu)) / 2
        else:
            geom, half = (TM(t.GetStart().x), TM(t.GetStart().y), TM(t.GetEnd().x), TM(t.GetEnd().y)),                 TM(t.GetWidth()) / 2
        for s in segs:
            if router.seg_dist(geom, s[:4]) < half + s[4] / 2 + CLEARANCE:
                board.Delete(t)
                del auto[uid]
                gone += 1
                break
    return gone


def escapes(board, net_names, length=0.8):
    """net -> [rect]: a short straight exit out of every long (IC-pin) pad of those nets, along the pad, away from
    its part's centre. Reserved for that net while the others are routed, so nobody crosses a pin's way out."""
    out = {}
    for f in board.GetFootprints():
        fc = f.GetPosition()
        for p in f.Pads():
            n = short(p.GetNetname())
            if n not in net_names or not p.IsOnLayer(LAYER):
                continue
            x0, y0, x1, y1 = router.pad_rect(p)
            w, h = x1 - x0, y1 - y0
            if max(w, h) < 1.5 * min(w, h):
                continue
            px, py = TM(p.GetPosition().x), TM(p.GetPosition().y)
            if w > h:
                r = (x1, y0, x1 + length, y1) if px > TM(fc.x) else (x0 - length, y0, x0, y1)
            else:
                r = (x0, y1, x1, y1 + length) if py > TM(fc.y) else (x0, y0 - length, x1, y0)
            out.setdefault(n, []).append(r)
    return out


def fence(board, gnd, segs, group):
    """Ground vias either side of the RF track, every RF_FENCE_PITCH mm, where they fit."""
    obs = copper.Obstacles()
    vias = []
    for f in board.GetFootprints():
        for p in f.Pads():
            obs.add("rect", "PAD", copper.pad_rect(p))           # never on a pad, whatever its net
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            vias.append((TM(t.GetPosition().x), TM(t.GetPosition().y)))
            if t.GetNetname() != "GND":
                obs.add("circle", t.GetNetname(), (TM(t.GetPosition().x), TM(t.GetPosition().y), 0.3))
        else:
            obs.add("seg", t.GetNetname(), (TM(t.GetStart().x), TM(t.GetStart().y), TM(t.GetEnd().x),
                                            TM(t.GetEnd().y), TM(t.GetWidth()) / 2))
    for k in g.board_keepouts():
        obs.add("rect", "PAD", k)
    added = 0
    for x0, y0, x1, y1, _ in segs:
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 0.5:
            continue
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        k = 0.5
        while k <= L - 0.3:
            px, py = x0 + ux * k, y0 + uy * k
            for side in (1, -1):
                vx, vy = px - uy * RF_FENCE_OFFSET * side, py + ux * RF_FENCE_OFFSET * side
                if any(math.hypot(vx - a, vy - b) < 0.8 for a, b in vias):
                    continue
                if not copper._clear(obs, "GND", vx, vy, 0.3, CLEARANCE):
                    continue
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(FM(vx), FM(vy)))
                v.SetWidth(FM(0.6))
                v.SetDrill(FM(0.3))
                v.SetNet(gnd)
                v.SetLocked(True)
                board.Add(v)
                group.AddItem(v)
                vias.append((vx, vy))
                added += 1
            k += RF_FENCE_PITCH
    return added


def main():
    only = set(sys.argv[1:])
    pro = g.PCB.with_suffix(".kicad_pro")
    net_settings = json.loads(pro.read_text(encoding="utf-8")).get("net_settings")
    board = pcbnew.LoadBoard(str(g.PCB))
    nets = {short(str(n)): ni for n, ni in board.GetNetsByName().items() if str(n)}
    removed = remove_previous(board, only)
    group = next((x for x in board.Groups() if x.GetName() == GROUP), None)
    if group is None:
        group = pcbnew.PCB_GROUP(board)
        group.SetName(GROUP)
        board.Add(group)
    gnd = nets["GND"]
    box = (g.OX, g.OY, g.OX + g.W, g.OY + g.H)
    keep = g.board_keepouts()

    pwr_hi = [n for n, ni in nets.items() if "PWR_HI" in ni.GetNetClassName()]

    def spread(n):
        ps = [p.GetPosition() for f in board.GetFootprints() for p in f.Pads() if short(p.GetNetname()) == n]
        return max(TM(a.x - b.x) ** 2 + TM(a.y - b.y) ** 2 for a in ps for b in ps) if ps else 0

    jobs = [(n, RF_W, True) for n in RF] + [(n, XTAL_W, False) for n in CRYSTALS] + \
           [(n, PWR_HI_W, False) for n in sorted(pwr_hi, key=lambda n: (PWR_ORDER.index(n) if n in PWR_ORDER
                                                                         else 99, spread(n)))]
    print(f"removed {removed} items from the previous run; routing {len(jobs)} nets on B.Cu")
    failed, fence_vias, bumped = [], 0, 0
    auto = auto_items(board)
    pending = {n for n, _, _ in jobs if not only or n in only}
    esc = escapes(board, pending)
    def run(n, w, is_rf, reserved):
        segs, bad = router.route_net(board, nets[n].GetNetname(), LAYER, w, CLEARANCE, keep + reserved, box,
                                     margin=6.0 if not is_rf else 4.0, ignore=frozenset(auto),
                                     neck_radius=PWR_HI_NECK if w == PWR_HI_W else 1.5,
                                     fallback=(0.5, 0.3) if w == PWR_HI_W else (), neck_clearance=0.15)
        return segs, bad

    done = {}                                          # net -> (segs, bad, items)
    for n, w, is_rf in jobs:
        if only and n not in only:
            continue
        if n not in nets:
            print(f"  {n:16s} not on the board")
            continue
        t0 = time.time()
        pending.discard(n)
        segs, bad = run(n, w, is_rf, [r for m in pending for r in esc.get(m, [])])
        bumped += clear_conflicts(board, segs, auto)
        items = router.add_segments(board, nets[n], LAYER, segs, group)
        done[n] = (segs, bad, items, w, is_rf)
        length = sum(math.hypot(s[2] - s[0], s[3] - s[1]) for s in segs)
        msg = f"  {n:16s} {len(segs):3d} segments {length:6.1f} mm  {time.time() - t0:5.1f} s"
        if is_rf:
            k = fence(board, gnd, segs, group)
            fence_vias += k
            msg += f"  fence {k} vias"
        if bad:
            msg += "  incomplete (" + " ".join(f"{p.GetParentFootprint().GetReference()}.{p.GetNumber()}" for p in bad) + ")"
        print(msg)

    # pass 2: nets left incomplete are ripped up and re-routed with nothing reserved; keep the better result
    for n, (segs, bad, items, w, is_rf) in list(done.items()):
        if not bad or is_rf:
            continue
        for t in items:
            board.Delete(t)
        segs2, bad2 = run(n, w, is_rf, [])
        if len(bad2) < len(bad):
            bumped += clear_conflicts(board, segs2, auto)
            items2 = router.add_segments(board, nets[n], LAYER, segs2, group)
            done[n] = (segs2, bad2, items2, w, is_rf)
            print(f"  {n:16s} pass 2: {len(bad)} -> {len(bad2)} pads left")
        else:
            done[n] = (segs, bad, router.add_segments(board, nets[n], LAYER, segs, group), w, is_rf)
    for n, (segs, bad, items, w, is_rf) in done.items():
        if bad:
            failed.append((n, [f"{p.GetParentFootprint().GetReference()}.{p.GetNumber()}" for p in bad]))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(g.PCB), board)
    if net_settings:                                   # SaveBoard rewrites the project file: keep the net classes
        d = json.loads(pro.read_text(encoding="utf-8"))
        d["net_settings"] = net_settings
        pro.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8", newline="\n")
    g.add_stackup()
    print(f"{bumped} generated fan-out vias/stubs were in the way and removed: re-run gen_pcb.py to put them back")
    print(f"saved; {fence_vias} RF fence vias; route by hand: " + ("; ".join(f"{n} ({' '.join(p)})" for n, p in failed)
                                                                   if failed else "nothing"))


if __name__ == "__main__":
    main()
