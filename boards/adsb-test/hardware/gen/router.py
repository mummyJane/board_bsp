"""Small grid maze router for short critical nets (KiCad's Python, numpy). Used by route_critical.py.

One net at a time, one copper layer, 8 directions on a 0.1 mm grid with a turn penalty (so tracks come out as
straight runs and 45-degree bends). Every other net's copper on that layer (pads, tracks, vias, through-holes),
the board edge, the slots and the corner holes are obstacles grown by clearance + half the track width.
Near each of the net's own pads the track may neck down (fine-pitch pins): inside a disc round the pad the
obstacles are grown by the narrow width only, and the segments there get that width.
Multi-pad nets are built as a tree: from everything already connected to the nearest unconnected pad.
"""
import heapq
import math

import numpy as np
import pcbnew

FM, TM = pcbnew.FromMM, pcbnew.ToMM
G = 0.1                                                   # grid, mm
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def pad_rect(p):
    b = p.GetBoundingBox()
    return TM(b.GetLeft()), TM(b.GetTop()), TM(b.GetRight()), TM(b.GetBottom())


class Window:
    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0 = x0, y0
        self.nx, self.ny = int((x1 - x0) / G) + 1, int((y1 - y0) / G) + 1
        self.X = x0 + np.arange(self.nx) * G
        self.Y = y0 + np.arange(self.ny) * G

    def cell(self, x, y):
        return int(round((x - self.x0) / G)), int(round((y - self.y0) / G))

    def xy(self, i, j):
        return self.x0 + i * G, self.y0 + j * G

    def sl(self, bx0, by0, bx1, by1):
        i0 = max(0, int((bx0 - self.x0) / G) - 1)
        i1 = min(self.nx, int((bx1 - self.x0) / G) + 2)
        j0 = max(0, int((by0 - self.y0) / G) - 1)
        j1 = min(self.ny, int((by1 - self.y0) / G) + 2)
        return i0, i1, j0, j1


def obstacles(board, layer, net_name, win, extra_keepouts, ignore=frozenset()):
    """List of (kind, geom) for every other net's copper on `layer` inside the window (mm)."""
    out = []
    pad_layer_ok = lambda p: p.IsOnLayer(layer)
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == net_name and p.GetNetname() != "":
                continue
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) or pad_layer_ok(p):
                out.append(("rect", pad_rect(p)))
    for t in board.GetTracks():
        if t.GetNetname() == net_name or t.m_Uuid.AsString() in ignore:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            out.append(("circle", (TM(t.GetPosition().x), TM(t.GetPosition().y), TM(t.GetWidth(pcbnew.F_Cu)) / 2)))
        elif t.GetLayer() == layer:
            out.append(("seg", (TM(t.GetStart().x), TM(t.GetStart().y), TM(t.GetEnd().x), TM(t.GetEnd().y),
                                TM(t.GetWidth()) / 2)))
    for k in extra_keepouts:
        out.append(("rect", k))
    import copper                                    # keep-out rule areas (e.g. under the module antenna)
    for k in copper.rule_areas(board):
        out.append(("rect", k))
    return out


def blocked(win, obs, grow):
    """Bool map [ny, nx]: cell centre closer than `grow` to any obstacle."""
    m = np.zeros((win.ny, win.nx), dtype=bool)
    for kind, g in obs:
        if kind == "rect":
            x0, y0, x1, y1 = g
            i0, i1, j0, j1 = win.sl(x0 - grow, y0 - grow, x1 + grow, y1 + grow)
            if i0 >= i1 or j0 >= j1:
                continue
            X, Y = win.X[i0:i1][None, :], win.Y[j0:j1][:, None]
            dx = np.maximum(np.maximum(x0 - X, 0), X - x1)
            dy = np.maximum(np.maximum(y0 - Y, 0), Y - y1)
            m[j0:j1, i0:i1] |= dx * dx + dy * dy < grow * grow
        elif kind == "circle":
            cx, cy, r = g
            R = r + grow
            i0, i1, j0, j1 = win.sl(cx - R, cy - R, cx + R, cy + R)
            if i0 >= i1 or j0 >= j1:
                continue
            X, Y = win.X[i0:i1][None, :], win.Y[j0:j1][:, None]
            m[j0:j1, i0:i1] |= (X - cx) ** 2 + (Y - cy) ** 2 < R * R
        else:
            ax, ay, bx, by, hw = g
            R = hw + grow
            i0, i1, j0, j1 = win.sl(min(ax, bx) - R, min(ay, by) - R, max(ax, bx) + R, max(ay, by) + R)
            if i0 >= i1 or j0 >= j1:
                continue
            X, Y = win.X[i0:i1][None, :], win.Y[j0:j1][:, None]
            vx, vy = bx - ax, by - ay
            L2 = vx * vx + vy * vy or 1e-9
            t = np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0, 1)
            m[j0:j1, i0:i1] |= (X - (ax + t * vx)) ** 2 + (Y - (ay + t * vy)) ** 2 < R * R
    return m


def board_edge_block(win, box, d):
    """Cells within d of the board edge (or outside it). box = (x0, y0, x1, y1) of the board, mm."""
    X, Y = win.X[None, :], win.Y[:, None]
    bx0, by0, bx1, by1 = box
    return (X < bx0 + d) | (X > bx1 - d) | (Y < by0 + d) | (Y > by1 - d)


def astar(free, sources, target_id, targets_xy, turn=0.6):
    """free: bool [ny, nx]; sources: list of (i, j); target_id: int [ny, nx] (>0 = target pad index + 1).
    Returns (path cells, target index) or (None, None)."""
    ny, nx = free.shape
    INF = 1e18
    gcost = {}
    prev = {}
    heap = []

    def h(i, j):
        best = INF
        for tx, ty in targets_xy:
            dx, dy = abs(i - tx), abs(j - ty)
            best = min(best, max(dx, dy) + 0.4142 * min(dx, dy))
        return best

    for i, j in sources:
        for d in range(8):
            gcost[(i, j, d)] = 0.0
            heapq.heappush(heap, (h(i, j), 0.0, i, j, d))
            prev[(i, j, d)] = None
    pops = 0
    while heap:
        f, gc, i, j, d = heapq.heappop(heap)
        if gc > gcost.get((i, j, d), INF):
            continue
        t = target_id[j, i]
        if t > 0 and prev.get((i, j, d)) is not None:
            path = []
            s = (i, j, d)
            while s is not None:
                path.append((s[0], s[1]))
                s = prev[s]
            return path[::-1], t - 1
        pops += 1
        if pops > 4_000_000:
            return None, None
        for nd, (di, dj) in enumerate(DIRS):
            ni, nj = i + di, j + dj
            if not (0 <= ni < nx and 0 <= nj < ny) or not free[nj, ni]:
                continue
            if di and dj and not (free[j, ni] and free[nj, i]):      # no corner cutting
                continue
            turn_steps = min((nd - d) % 8, (d - nd) % 8)
            if turn_steps > 2:
                continue                                              # no sharp (> 90 deg) bends
            ng = gc + (1.4142 if di and dj else 1.0) + turn * turn_steps
            key = (ni, nj, nd)
            if ng < gcost.get(key, INF):
                gcost[key] = ng
                prev[key] = (i, j, d)
                heapq.heappush(heap, (ng + h(ni, nj), ng, ni, nj, nd))
    return None, None


def route_net(board, net_name, layer, width, clearance, keepouts, board_box, edge_clear=0.5, neck_radius=1.5,
              margin=8.0, min_width=0.15, ignore=frozenset(), fallback=(), detour=(2.0, 4.0), neck_clearance=None):
    """Route all pads of `net_name` on `layer`. Returns (list of (x0, y0, x1, y1, w) segments mm, unconnected pads)."""
    pads = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == net_name and p.IsOnLayer(layer)]
    if len(pads) < 2:
        return [], []
    rects = [pad_rect(p) for p in pads]
    x0 = max(board_box[0], min(r[0] for r in rects) - margin)
    y0 = max(board_box[1], min(r[1] for r in rects) - margin)
    x1 = min(board_box[2], max(r[2] for r in rects) + margin)
    y1 = min(board_box[3], max(r[3] for r in rects) + margin)
    win = Window(x0, y0, x1, y1)
    obs = obstacles(board, layer, net_name, win, keepouts, ignore)

    X, Y = win.X[None, :], win.Y[:, None]
    maps, cache = {}, {}
    neck_clearance = clearance if neck_clearance is None else neck_clearance

    def grown(w, c=clearance):
        if (w, c) not in maps:
            maps[(w, c)] = blocked(win, obs, c + w / 2) | board_edge_block(win, board_box, edge_clear + w / 2)
        return maps[(w, c)]

    pad_id = np.zeros((win.ny, win.nx), dtype=np.int32)
    pad_cells = []
    for k, r in enumerate(rects):
        i0, i1, j0, j1 = win.sl(r[0], r[1], r[2], r[3])
        X2, Y2 = win.X[i0:i1][None, :], win.Y[j0:j1][:, None]
        inside = (X2 >= r[0] + 0.05) & (X2 <= r[2] - 0.05) & (Y2 >= r[1] + 0.05) & (Y2 <= r[3] - 0.05)
        for jj, ii in zip(*np.nonzero(inside)):           # real pad shape (rounded corners, ovals)
            x, y = float(win.X[i0 + ii]), float(win.Y[j0 + jj])
            if not pads[k].HitTest(pcbnew.VECTOR2I(FM(x), FM(y)), -FM(0.05)):
                inside[jj, ii] = False
        pad_id[j0:j1, i0:i1][inside] = k + 1
        pad_cells.append((j0, j1, i0, i1, inside))

    def free_for(trunk):
        """(free map, width per cell) for a trunk width: obstacles grown by the trunk width, by each pad's narrow
        width inside the neck-down disc round that pad; own pads always enterable."""
        if trunk in cache:
            return cache[trunk]
        blk = grown(trunk).copy()
        cellw = np.full((win.ny, win.nx), trunk)
        for r in rects:
            # neck: 0.1 mm narrower than the pad, so the gap between fine-pitch pins always holds a grid row
            w = max(min_width, min(trunk, min(r[2] - r[0], r[3] - r[1]) - 0.1))
            if w >= trunk:
                continue
            dx = np.maximum(np.maximum(r[0] - X, 0), X - r[2])
            dy = np.maximum(np.maximum(r[1] - Y, 0), Y - r[3])
            disc = dx * dx + dy * dy < neck_radius ** 2
            blk[disc] &= grown(w, neck_clearance)[disc]
            cellw[disc] = np.minimum(cellw[disc], w)
        for j0, j1, i0, i1, inside in pad_cells:
            blk[j0:j1, i0:i1][inside] = False
        cache[trunk] = (~blk, cellw)
        return cache[trunk]

    trunks = [width] + [w for w in fallback if w < width]

    # start from the pad nearest the middle of the net
    cx, cy = sum((r[0] + r[2]) / 2 for r in rects) / len(rects), sum((r[1] + r[3]) / 2 for r in rects) / len(rects)
    start = min(range(len(rects)), key=lambda k: math.hypot((rects[k][0] + rects[k][2]) / 2 - cx,
                                                            (rects[k][1] + rects[k][3]) / 2 - cy))
    connected = {start}
    tree = [tuple(c) for c in np.argwhere(pad_id.T == start + 1)]
    segs, failed = [], []
    while len(connected) + len(failed) < len(rects):
        remaining = [k for k in range(len(rects)) if k not in connected and k not in failed]
        tid = np.where(np.isin(pad_id, [k + 1 for k in remaining]), pad_id, 0)
        txy = [win.cell((rects[k][0] + rects[k][2]) / 2, (rects[k][1] + rects[k][3]) / 2) for k in remaining]
        for trunk in trunks:                         # full width first, then narrower if it does not fit
            free, cellw = free_for(trunk)
            path, hit = astar(free, tree, tid, txy)
            if path is not None and detour:
                L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:])) * G
                tx, ty = win.cell((rects[hit][0] + rects[hit][2]) / 2, (rects[hit][1] + rects[hit][3]) / 2)
                direct = math.hypot(tx - path[0][0], ty - path[0][1]) * G
                if L > detour[0] * direct + detour[1]:
                    path = None                      # a long way round: leave it for hand routing
                    continue
            if path is not None:
                break
        if path is None:
            failed.extend(remaining)
            break
        connected.add(hit)
        tree.extend(path)
        tree.extend(tuple(c) for c in np.argwhere(pad_id.T == hit + 1))
        # compress into straight runs of one width
        run = [path[0]]
        for a, b, c in zip(path, path[1:], path[2:]):
            same_dir = (b[0] - a[0], b[1] - a[1]) == (c[0] - b[0], c[1] - b[1])
            same_w = cellw[b[1], b[0]] == cellw[c[1], c[0]] and cellw[a[1], a[0]] == cellw[b[1], b[0]]
            if not (same_dir and same_w):
                run.append(b)
        run.append(path[-1])
        for a, b in zip(run, run[1:]):
            if a == b:
                continue
            w = min(cellw[a[1], a[0]], cellw[b[1], b[0]])
            segs.append(tuple(float(v) for v in (*win.xy(*a), *win.xy(*b), w)))
    return prune(segs, rects), [pads[k] for k in failed]


def prune(segs, rects, tol=0.06):
    """Drop segments with a loose end (not on one of the net's pads, nor on another of its segments)."""
    def on_pad(x, y):
        return any(r[0] - tol <= x <= r[2] + tol and r[1] - tol <= y <= r[3] + tol for r in rects)

    def on_seg(x, y, skip):
        for k, (x0, y0, x1, y1, _) in enumerate(segs):
            if k == skip:
                continue
            vx, vy = x1 - x0, y1 - y0
            L2 = vx * vx + vy * vy
            t = 0 if L2 == 0 else max(0, min(1, ((x - x0) * vx + (y - y0) * vy) / L2))
            if math.hypot(x - (x0 + t * vx), y - (y0 + t * vy)) < tol:
                return True
        return False

    changed = True
    while changed:
        changed = False
        for k, (x0, y0, x1, y1, w) in enumerate(segs):
            if not ((on_pad(x0, y0) or on_seg(x0, y0, k)) and (on_pad(x1, y1) or on_seg(x1, y1, k))):
                segs = segs[:k] + segs[k + 1:]
                changed = True
                break
    return segs


def add_segments(board, net, layer, segs, group):
    made = []
    for x0, y0, x1, y1, w in segs:
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(FM(x0), FM(y0)))
        t.SetEnd(pcbnew.VECTOR2I(FM(x1), FM(y1)))
        t.SetWidth(FM(w))
        t.SetLayer(layer)
        t.SetNet(net)
        t.SetLocked(True)
        board.Add(t)
        group.AddItem(t)
        made.append(t)
    return made


def seg_dist(a, b):
    """Shortest distance between two segments (x0, y0, x1, y1), mm."""
    def pt(px, py, x0, y0, x1, y1):
        vx, vy = x1 - x0, y1 - y0
        L2 = vx * vx + vy * vy
        t = 0 if L2 == 0 else max(0, min(1, ((px - x0) * vx + (py - y0) * vy) / L2))
        return math.hypot(px - (x0 + t * vx), py - (y0 + t * vy))

    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])

    A, B, C, D = (a[0], a[1]), (a[2], a[3]), (b[0], b[1]), (b[2], b[3])
    if cross(A, B, C) * cross(A, B, D) < 0 and cross(C, D, A) * cross(C, D, B) < 0:
        return 0.0
    return min(pt(*A, *b[:4]), pt(*B, *b[:4]), pt(*C, *a[:4]), pt(*D, *a[:4]))
