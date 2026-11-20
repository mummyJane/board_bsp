"""Copper helpers for gen_pcb.py (KiCad's Python): keep routing across a rebuild, ground zones, ground vias.

Everything this module generates is tagged so a rebuild can tell it apart from hand / autorouted copper:
  * zones are named "AUTO_..."           -> regenerated, never copied from the old board
  * ground vias + their stubs sit in the group "AUTO_GND_VIAS" -> regenerated, never copied
Every other track, arc, via and zone in the old board is copied into the new one (by net name).
"""
import math

import pcbnew

AUTO_GROUP = "AUTO_GND_VIAS"
AUTO_ZONE = "AUTO_"

mm = pcbnew.FromMM
to_mm = pcbnew.ToMM


# ---------------------------------------------------------------- keep routing
def auto_uuids(board):
    out = set()
    for g in board.Groups():
        if g.GetName() == AUTO_GROUP:
            out |= {it.m_Uuid.AsString() for it in g.GetItems()}
    return out


def keep_routing(old, board, nets, mode="all"):
    """Copy tracks / arcs / vias / zones from `old` into `board`.
    mode: "all" (default), "locked" (only items locked in KiCad), "none". Returns (copied, dropped nets)."""
    if old is None or mode == "none":
        return 0, set()
    skip = auto_uuids(old)
    copied, dropped = 0, set()

    def net_of(item):
        name = item.GetNetname()
        if not name:
            return None
        if name not in nets:
            dropped.add(name)
            return False
        return nets[name]

    for t in old.GetTracks():
        if t.m_Uuid.AsString() in skip or (mode == "locked" and not t.IsLocked()):
            continue
        n = net_of(t)
        if n is False:
            continue
        kind = t.Type()
        if kind == pcbnew.PCB_VIA_T:
            v = pcbnew.PCB_VIA(board)
            v.SetViaType(t.GetViaType())
            v.SetPosition(t.GetPosition())
            v.SetWidth(t.GetWidth(pcbnew.F_Cu))
            v.SetDrill(t.GetDrillValue())
            v.SetLayerPair(t.TopLayer(), t.BottomLayer())
            new = v
        elif kind == pcbnew.PCB_ARC_T:
            a = pcbnew.PCB_ARC(board)
            a.SetStart(t.GetStart())
            a.SetMid(t.GetMid())
            a.SetEnd(t.GetEnd())
            a.SetWidth(t.GetWidth())
            a.SetLayer(t.GetLayer())
            new = a
        else:
            s = pcbnew.PCB_TRACK(board)
            s.SetStart(t.GetStart())
            s.SetEnd(t.GetEnd())
            s.SetWidth(t.GetWidth())
            s.SetLayer(t.GetLayer())
            new = s
        if n:
            new.SetNet(n)
        new.SetLocked(t.IsLocked())
        board.Add(new)
        copied += 1

    for z in old.Zones():
        if z.GetZoneName().startswith(AUTO_ZONE) or (mode == "locked" and not z.IsLocked()):
            continue
        if z.IsOnCopperLayer() and not z.GetIsRuleArea():
            n = net_of(z)
            if n is False:
                continue
        else:
            n = None
        nz = pcbnew.Cast_to_BOARD_ITEM(z.Duplicate(False)).Cast()
        nz.SetParent(board)
        board.Add(nz)
        if n:
            nz.SetNet(n)
        copied += 1
    return copied, dropped


# ---------------------------------------------------------------- zones
def add_zone(board, net, layer_name, name, outline_pts, clearance=0.2, priority=0, min_width=0.2,
             thermal_gap=0.3, spoke=0.4):
    z = pcbnew.ZONE(board)
    z.SetLayer(board.GetLayerID(layer_name))
    z.SetNet(net)
    z.SetZoneName(name)
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(min_width))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)   # thermal spokes: pads stay hand-solderable
    z.SetThermalReliefGap(mm(thermal_gap))
    z.SetThermalReliefSpokeWidth(mm(spoke))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for x, y in outline_pts:
        o.Append(mm(x), mm(y))
    board.Add(z)
    return z


# ---------------------------------------------------------------- ground vias
class Obstacles:
    """Copper on B.Cu / F.Cu / through-holes in a coarse grid, for quick clearance checks (all in mm)."""

    def __init__(self, cell=2.0):
        self.cell = cell
        self.grid = {}

    def _cells(self, x0, y0, x1, y1):
        c = self.cell
        for i in range(int(x0 // c), int(x1 // c) + 1):
            for j in range(int(y0 // c), int(y1 // c) + 1):
                yield i, j

    def add(self, kind, net, geom):
        """kind 'rect' geom (x0, y0, x1, y1); kind 'circle' (x, y, r); kind 'seg' (x0, y0, x1, y1, half_width)."""
        if kind == "rect":
            box = geom
        elif kind == "circle":
            x, y, r = geom
            box = (x - r, y - r, x + r, y + r)
        else:
            x0, y0, x1, y1, w = geom
            box = (min(x0, x1) - w, min(y0, y1) - w, max(x0, x1) + w, max(y0, y1) + w)
        item = (kind, net, geom)
        for k in self._cells(*box):
            self.grid.setdefault(k, []).append(item)

    def near(self, x, y, r):
        seen = set()
        for k in self._cells(x - r, y - r, x + r, y + r):
            for it in self.grid.get(k, ()):
                if id(it) not in seen:
                    seen.add(id(it))
                    yield it


def _dist_point(kind, geom, x, y):
    if kind == "rect":
        x0, y0, x1, y1 = geom
        dx = max(x0 - x, 0, x - x1)
        dy = max(y0 - y, 0, y - y1)
        return math.hypot(dx, dy)
    if kind == "circle":
        cx, cy, r = geom
        return math.hypot(x - cx, y - cy) - r
    x0, y0, x1, y1, w = geom
    vx, vy = x1 - x0, y1 - y0
    L2 = vx * vx + vy * vy
    t = 0 if L2 == 0 else max(0, min(1, ((x - x0) * vx + (y - y0) * vy) / L2))
    return math.hypot(x - (x0 + t * vx), y - (y0 + t * vy)) - w


def _clear(obs, net, x, y, r, clearance):
    for kind, n, geom in obs.near(x, y, r + clearance + 1):
        if n == net and kind != "hole":
            continue
        if _dist_point(kind, geom, x, y) < r + clearance:
            return False
    return True


def _seg_clear(obs, net, x0, y0, x1, y1, w, clearance):
    L = math.hypot(x1 - x0, y1 - y0)
    steps = max(1, int(L / 0.05))
    for i in range(steps + 1):
        t = i / steps
        if not _clear(obs, net, x0 + t * (x1 - x0), y0 + t * (y1 - y0), w / 2, clearance):
            return False
    return True


def pad_rect(p):
    b = p.GetBoundingBox()
    return (to_mm(b.GetLeft()), to_mm(b.GetTop()), to_mm(b.GetRight()), to_mm(b.GetBottom()))


def gnd_vias(board, gnd, inside, keepouts, via=(0.6, 0.3), stub=0.3, clearance=0.2, max_pad_area=4.0):
    """One via beside every SMD ground pad on B.Cu, joined by a short stub (B.Cu). Pads that already reach the
    other layers (plated holes in the same footprint on that pad, or a GND through-hole pad) are skipped.
    inside(x, y) -> True if the point is on the board; keepouts: [(x0, y0, x1, y1)] mm.
    Returns (vias added, pads with no room)."""
    obs = Obstacles()
    gnd_name = gnd.GetNetname()
    for f in board.GetFootprints():
        for p in f.Pads():
            n = p.GetNetname()
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                x, y = to_mm(p.GetPosition().x), to_mm(p.GetPosition().y)
                hole = max(to_mm(p.GetDrillSize().x), to_mm(p.GetDrillSize().y)) / 2
                obs.add("circle", "" if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else n,
                        (x, y, max(hole, max(to_mm(p.GetSize(pcbnew.B_Cu).x), to_mm(p.GetSize(pcbnew.B_Cu).y)) / 2)))
            else:
                obs.add("rect", n, pad_rect(p))
    for t in board.GetTracks():
        n = t.GetNetname()
        if t.Type() == pcbnew.PCB_VIA_T:
            obs.add("circle", n, (to_mm(t.GetPosition().x), to_mm(t.GetPosition().y), to_mm(t.GetWidth(pcbnew.F_Cu)) / 2))
        else:
            obs.add("seg", n, (to_mm(t.GetStart().x), to_mm(t.GetStart().y), to_mm(t.GetEnd().x), to_mm(t.GetEnd().y),
                               to_mm(t.GetWidth()) / 2))
    for k in keepouts:
        obs.add("rect", "", k)

    group = pcbnew.PCB_GROUP(board)
    group.SetName(AUTO_GROUP)
    board.Add(group)
    vr = via[0] / 2
    added, no_room = 0, []
    for f in board.GetFootprints():
        if not f.IsFlipped():
            continue
        fc = f.GetPosition()
        fx, fy = to_mm(fc.x), to_mm(fc.y)
        gnd_holes = [q for q in f.Pads() if q.GetNetname() == gnd_name and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
        for p in f.Pads():
            if p.GetNetname() != gnd_name or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            x0, y0, x1, y1 = pad_rect(p)
            px, py = (x0 + x1) / 2, (y0 + y1) / 2
            if not inside(px, py):
                continue
            if (x1 - x0) * (y1 - y0) > max_pad_area:
                continue                    # exposed / module pads: the footprint's own holes or several vias by hand
            if any(q.GetNumber() == p.GetNumber() or q.HitTest(p.GetPosition()) for q in gnd_holes):
                continue
            # already a ground via within 1.2 mm of this pad?
            if any(kind == "circle" and n == gnd_name and _dist_point("rect", (x0, y0, x1, y1), g[0], g[1]) < 1.2
                   for kind, n, g in obs.near(px, py, 2.5)):
                continue
            ang0 = math.atan2(py - fy, px - fx) if (px, py) != (fx, fy) else 0.0
            best = None
            for da in (0, 90, -90, 45, -45, 135, -135, 180):
                a = ang0 + math.radians(da)
                ux, uy = math.cos(a), math.sin(a)
                # distance from the pad centre to its edge along (ux, uy)
                hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
                edge = min(hx / abs(ux) if abs(ux) > 1e-6 else 1e9, hy / abs(uy) if abs(uy) > 1e-6 else 1e9)
                for extra in (0.15, 0.35, 0.6, 0.9):
                    d = edge + extra + vr
                    vx, vy = px + ux * d, py + uy * d
                    if not inside(vx, vy):
                        continue
                    if not _clear(obs, gnd_name, vx, vy, vr, clearance):
                        continue
                    if not _seg_clear(obs, gnd_name, px, py, vx, vy, stub, clearance):
                        continue
                    best = (vx, vy)
                    break
                if best:
                    break
            if not best:
                no_room.append(f"{f.GetReference()}.{p.GetNumber()}")
                continue
            vx, vy = best
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy)))
            v.SetWidth(mm(via[0]))
            v.SetDrill(mm(via[1]))
            v.SetNet(gnd)
            board.Add(v)
            group.AddItem(v)
            s = pcbnew.PCB_TRACK(board)
            s.SetStart(p.GetPosition())
            s.SetEnd(v.GetPosition())
            s.SetWidth(mm(stub))
            s.SetLayer(pcbnew.B_Cu)
            s.SetNet(gnd)
            board.Add(s)
            group.AddItem(s)
            obs.add("circle", gnd_name, (vx, vy, vr))
            obs.add("seg", gnd_name, (px, py, vx, vy, stub / 2))
            added += 1
    return added, no_room
