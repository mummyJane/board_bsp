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
        if g.GetName().startswith(AUTO_ZONE):            # AUTO_GND_VIAS, AUTO_PWR_VIAS, ...
            out |= {it.m_Uuid.AsString() for it in g.GetItems()}
    return out


def keep_routing(old, board, nets, mode="all"):
    """Copy tracks / arcs / vias / zones from `old` into `board`.
    mode: "all" (default), "locked" (only items locked in KiCad), "none". Returns (copied, dropped nets)."""
    if old is None or mode == "none":
        return 0, set()
    skip = auto_uuids(old)
    copied, dropped = 0, set()
    gmap, groups = {}, {}                     # other named groups (e.g. ROUTED_BY_SCRIPT) are carried over
    for g in old.Groups():
        if g.GetName() and not g.GetName().startswith(AUTO_ZONE):
            for it in g.GetItems():
                gmap[it.m_Uuid.AsString()] = g.GetName()

    def regroup(item, uuid):
        name = gmap.get(uuid)
        if not name:
            return
        if name not in groups:
            grp = pcbnew.PCB_GROUP(board)
            grp.SetName(name)
            board.Add(grp)
            groups[name] = grp
        groups[name].AddItem(item)

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
        regroup(new, t.m_Uuid.AsString())
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
        regroup(nz, z.m_Uuid.AsString())
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
        if _dist_point(kind, geom, x, y) < r + clearance - 1e-4:
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


def rule_areas(board):
    """Bounding boxes (mm) of keep-out rule areas that forbid vias or tracks (board-level and inside footprints)."""
    out = []
    zones = list(board.Zones())
    for f in board.GetFootprints():
        zones += list(f.Zones())
    for z in zones:
        if z.GetIsRuleArea() and (z.GetDoNotAllowVias() or z.GetDoNotAllowTracks()) and                 (z.IsOnLayer(pcbnew.B_Cu) or z.IsOnLayer(pcbnew.F_Cu)):
            b = z.GetBoundingBox()
            out.append((to_mm(b.GetLeft()), to_mm(b.GetTop()), to_mm(b.GetRight()), to_mm(b.GetBottom())))
    return out


def pad_rect(p):
    b = p.GetBoundingBox()
    return (to_mm(b.GetLeft()), to_mm(b.GetTop()), to_mm(b.GetRight()), to_mm(b.GetBottom()))


def gnd_vias(board, gnd, inside, keepouts, **kw):
    return pad_vias(board, gnd, inside, keepouts, AUTO_GROUP, **kw)


def pad_vias(board, gnd, inside, keepouts, group_name, only=None, via=(0.6, 0.3), stub=0.3, clearance=0.18,
             max_pad_area=4.0):
    """One via beside every SMD pad of net `gnd` on B.Cu, joined by a short stub (B.Cu, no wider than the pad).
    Pads that already reach the other layers (plated holes in the same footprint on that pad, or a through-hole
    pad of the net) are skipped. only(pad) -> False skips a pad. inside(x, y) -> True if the point is on the board;
    keepouts: [(x0, y0, x1, y1)] mm. Returns (vias added, pads with no room)."""
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
    for k in keepouts + rule_areas(board):
        obs.add("rect", "", k)
    via_xy = [(to_mm(t.GetPosition().x), to_mm(t.GetPosition().y)) for t in board.GetTracks()
              if t.Type() == pcbnew.PCB_VIA_T]

    group = pcbnew.PCB_GROUP(board)
    group.SetName(group_name)
    board.Add(group)
    vr = via[0] / 2
    added, no_room = 0, []
    grounded, fallback = set(), []                 # pads already reaching the other layers / pads left for later
    key = lambda q: (q.GetParentFootprint().GetReference(), q.GetNumber())
    for f in board.GetFootprints():
        if not f.IsFlipped():
            continue
        fc = f.GetPosition()
        fx, fy = to_mm(fc.x), to_mm(fc.y)
        gnd_holes = [q for q in f.Pads() if q.GetNetname() == gnd_name and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
        for p in f.Pads():
            if p.GetNetname() != gnd_name or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            if only is not None and not only(p):
                continue
            x0, y0, x1, y1 = pad_rect(p)
            px, py = (x0 + x1) / 2, (y0 + y1) / 2
            if not inside(px, py):
                continue
            if (x1 - x0) * (y1 - y0) > max_pad_area:
                continue                    # exposed / module pads: the footprint's own holes or several vias by hand
            if any(q.GetNumber() == p.GetNumber() or q.HitTest(p.GetPosition()) for q in gnd_holes):
                grounded.add(key(p))
                continue
            # already a ground via within 1.2 mm of this pad? (ground only: the fill joins them)
            if group_name == AUTO_GROUP and any(kind == "circle" and n == gnd_name and _dist_point("rect", (x0, y0, x1, y1), g[0], g[1]) < 1.2
                   for kind, n, g in obs.near(px, py, 2.5)):
                continue
            ang0 = math.atan2(py - fy, px - fx) if (px, py) != (fx, fy) else 0.0
            sw = min(stub, 0.9 * min(x1 - x0, y1 - y0))   # stub narrower than the pad (fits 0.4 mm-pitch pins)
            best = None
            angles = [ang0 + math.radians(da) for da in (0, 90, -90, 45, -45, 135, -135, 180)]
            w_, h_ = x1 - x0, y1 - y0
            if max(w_, h_) > 1.5 * min(w_, h_):     # long pad (IC pin): straight out along it first, then in
                ax = 0.0 if w_ > h_ else math.pi / 2
                out_ = ax if math.cos(ax - ang0) >= 0 else ax + math.pi
                angles = [out_, out_ + math.pi] + angles
            for a in angles:
                ux, uy = math.cos(a), math.sin(a)
                # distance from the pad centre to its edge along (ux, uy)
                hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
                edge = min(hx / abs(ux) if abs(ux) > 1e-6 else 1e9, hy / abs(uy) if abs(uy) > 1e-6 else 1e9)
                for extra in (0.15, 0.35, 0.6, 0.9, 1.3, 1.8, 2.4):
                    d = edge + extra + vr
                    vx, vy = px + ux * d, py + uy * d
                    if not inside(vx, vy):
                        continue
                    if not _clear(obs, gnd_name, vx, vy, vr, clearance):
                        continue
                    if any(math.hypot(vx - a, vy - b_) < via[0] + 0.15 for a, b_ in via_xy):
                        continue                    # hole-to-hole spacing, whatever the net
                    if not _seg_clear(obs, gnd_name, px, py, vx, vy, sw, clearance):
                        continue
                    best = (vx, vy)
                    break
                if best:
                    break
            if not best and math.hypot(px - fx, py - fy) < 0.3:
                best = (px, py)                          # exposed centre pad boxed in by its pins: via in the pad
            if not best:                                 # later: a short track to a grounded pad of this part
                fallback.append((f, p, px, py, sw))
                continue
            grounded.add(key(p))
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
            s.SetWidth(mm(sw))
            s.SetLayer(pcbnew.B_Cu)
            s.SetNet(gnd)
            board.Add(s)
            group.AddItem(s)
            obs.add("circle", gnd_name, (vx, vy, vr))
            obs.add("seg", gnd_name, (px, py, vx, vy, sw / 2))
            via_xy.append((vx, vy))
            added += 1

    # pads with no room for a via: a short track to a same-net pad of the same part that already reaches the other
    # layers (its own via, a plated hole, or a big exposed pad with holes); repeated so chains work
    for f in board.GetFootprints():
        for q in f.Pads():
            if q.GetNetname() == gnd_name and (q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or
                                               (lambda r: (r[2] - r[0]) * (r[3] - r[1]))(pad_rect(q)) > max_pad_area):
                grounded.add(key(q))
    progress = True
    while fallback and progress:
        progress = False
        for item in list(fallback):
            f, p, px, py, sw = item
            for q in sorted((q for q in f.Pads() if key(q) in grounded and q.GetNetname() == gnd_name),
                            key=lambda q: (q.GetPosition() - p.GetPosition()).EuclideanNorm()):
                qx0, qy0, qx1, qy1 = pad_rect(q)
                tx, ty = min(max(px, qx0 + 0.1), qx1 - 0.1), min(max(py, qy0 + 0.1), qy1 - 0.1)
                L = math.hypot(tx - px, ty - py)
                if L < 0.05 or L > 3 or not _seg_clear(obs, gnd_name, px, py, tx, ty, sw, clearance):
                    continue
                s = pcbnew.PCB_TRACK(board)
                s.SetStart(p.GetPosition())
                s.SetEnd(pcbnew.VECTOR2I(mm(tx), mm(ty)))
                s.SetWidth(mm(sw))
                s.SetLayer(pcbnew.B_Cu)
                s.SetNet(gnd)
                board.Add(s)
                group.AddItem(s)
                obs.add("seg", gnd_name, (px, py, tx, ty, sw / 2))
                grounded.add(key(p))
                fallback.remove(item)
                progress = True
                break
    no_room += [f"{f.GetReference()}.{p.GetNumber()}" for f, p, *_ in fallback]
    return added, no_room


def hull(points):
    """Convex hull (monotone chain) of [(x, y)], counter-clockwise."""
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def grow(poly, d):
    """Push each vertex of a convex polygon out by d (approximate offset), as an octagon-ish outline."""
    cx = sum(x for x, _ in poly) / len(poly)
    cy = sum(y for _, y in poly) / len(poly)
    out = []
    for x, y in poly:
        L = math.hypot(x - cx, y - cy) or 1
        out.append((x + (x - cx) / L * d, y + (y - cy) / L * d))
    return out
