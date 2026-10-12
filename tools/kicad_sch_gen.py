#!/usr/bin/env python3
"""Small KiCad schematic generator used to build board sheets from Python.

Approach: library symbols are copied from .kicad_sym files into the sheet,
placed (rotation 0), and every pin gets a short wire stub ending in a net label,
power symbol or no-connect flag. Connectivity is by net name, so the result is a
normal KiCad schematic that ERC can check and that can be tidied by hand later.
Files are written in KiCad 9 format; run `kicad-cli sch upgrade` afterwards.
"""
import copy
import re
import uuid as _uuid
from pathlib import Path

KICAD_SYM_DIR = Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols")
GRID = 1.27
STUB = 2.54


# ----------------------------------------------------------------- s-expressions

def parse(text):
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', text)
    stack = [[]]
    for tok in tokens:
        if tok == "(":
            stack.append([])
        elif tok == ")":
            node = stack.pop()
            stack[-1].append(node)
        else:
            stack[-1].append(tok)
    return stack[0]


def dump(node, indent=0):
    if not isinstance(node, list):
        return node
    if all(not isinstance(x, list) for x in node):
        return "(" + " ".join(node) + ")"
    pad = "\t" * (indent + 1)
    head = []
    rest = []
    for x in node:
        if not rest and not isinstance(x, list):
            head.append(x)
        else:
            rest.append(x)
    return "(" + " ".join(head) + "".join("\n" + pad + dump(x, indent + 1) for x in rest) + "\n" + "\t" * indent + ")"


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def unq(s):
    return s[1:-1].replace('\\"', '"').replace("\\\\", "\\") if s.startswith('"') else s


def uid():
    return q(_uuid.uuid4())


def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def fmt(v):
    v = round(v, 4)
    return str(int(v)) if v == int(v) else repr(v)


# ----------------------------------------------------------------- symbol libraries

class SymbolLibs:
    def __init__(self, extra_libs=None):
        self.cache = {}
        self.paths = {}
        for p in KICAD_SYM_DIR.glob("*.kicad_sym"):
            self.paths[p.stem] = p
        for name, path in (extra_libs or {}).items():
            self.paths[name] = Path(path)

    def _lib(self, lib):
        if lib not in self.cache:
            tree = parse(self.paths[lib].read_text(encoding="utf-8"))[0]
            self.cache[lib] = {unq(s[1]): s for s in find(tree, "symbol")}
        return self.cache[lib]

    def get(self, lib_id):
        """Return a flattened copy of the symbol, renamed to 'lib:name' (KiCad sheet cache form)."""
        lib, name = lib_id.split(":", 1)
        syms = self._lib(lib)
        sym = copy.deepcopy(syms[name])
        ext = find(sym, "extends")
        if ext:
            parent = copy.deepcopy(syms[unq(ext[0][1])])
            pname = unq(parent[1])
            child_props = {unq(p[1]): p for p in find(sym, "property")}
            out = [x for x in parent if not (isinstance(x, list) and x and x[0] == "property"
                                              and unq(x[1]) in child_props)]
            insert_at = 2
            for p in child_props.values():
                out.insert(insert_at, p)
                insert_at += 1
            for sub in find(out, "symbol"):
                sub[1] = q(unq(sub[1]).replace(pname, name, 1))
            sym = out
        sym[1] = q(lib_id)
        # Un-hide pins: hidden power-input pins would otherwise join an implicit
        # global net named after the pin (e.g. "VCC"), separate from our rail labels.
        for sub in find(sym, "symbol"):
            for pin in find(sub, "pin"):
                pin[:] = [x for x in pin if x != "hide" and not (isinstance(x, list) and x[:2] == ["hide", "yes"])]
        return sym

    def pins(self, lib_id):
        """{number: (x, y, angle, name, type, unit)} in symbol coordinates (y up)."""
        sym = self.get(lib_id)
        name = lib_id.split(":", 1)[1]
        out = {}
        for sub in find(sym, "symbol"):
            m = re.match(re.escape(name) + r"_(\d+)_(\d+)$", unq(sub[1]))
            unit = int(m.group(1)) if m else 0
            for pin in find(sub, "pin"):
                at = find(pin, "at")[0]
                num = unq(find(pin, "number")[0][1])
                pname = unq(find(pin, "name")[0][1])
                out.setdefault(num, (float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0,
                                     pname, pin[1], unit))
        return out


# ----------------------------------------------------------------- sheet builder

class Placed:
    def __init__(self, sheet, lib_id, ref, at, unit, pins):
        self.sheet, self.lib_id, self.ref, self.at, self.unit, self._pins = sheet, lib_id, ref, at, unit, pins

    def pin(self, key):
        """Pin by number, or by unique name."""
        if key in self._pins:
            return key
        hits = [n for n, p in self._pins.items() if p[3] == key]
        if len(hits) != 1:
            raise KeyError(f"{self.ref}: pin {key!r} -> {hits}")
        return hits[0]

    def pin_xy(self, key):
        x, y, a, *_ = self._pins[self.pin(key)]
        return self.at[0] + x, self.at[1] - y, a

    def pins_named(self, name):
        return [n for n, p in self._pins.items() if p[3] == name and p[5] in (0, self.unit)]


class Sheet:
    def __init__(self, libs, project, root_uuid, sheet_uuid, page_uuid=None):
        self.libs = libs
        self.project = project
        self.path = f"/{root_uuid}/{sheet_uuid}" if sheet_uuid else f"/{root_uuid}"
        self.page_uuid = page_uuid or str(_uuid.uuid4())
        self.lib_symbols = {}
        self.items = []
        self.placed = {}
        self._pwr = 0
        self.locals = set()     # nets that only exist on this sheet -> local labels

    # --- symbols
    def add(self, lib_id, ref, value, at, footprint="", unit=1, dnp=False, props=None, datasheet=""):
        if lib_id not in self.lib_symbols:
            self.lib_symbols[lib_id] = self.libs.get(lib_id)
        pins = self.libs.pins(lib_id)
        x, y = at
        node = ["symbol", ["lib_id", q(lib_id)], ["at", fmt(x), fmt(y), "0"], ["unit", str(unit)],
                ["exclude_from_sim", "no"], ["in_bom", "no" if ref.startswith("#") else "yes"],
                ["on_board", "no" if ref.startswith("#") else "yes"], ["dnp", "yes" if dnp else "no"],
                ["uuid", uid()]]
        fields = [("Reference", ref, (x, y - 3.81), ref.startswith("#")),
                  ("Value", value, (x, y + 3.81), ref.startswith("#PWR")),
                  ("Footprint", footprint, (x, y), True), ("Datasheet", datasheet, (x, y), True)]
        for k, v in (props or {}).items():
            fields.append((k, v, (x, y), True))
        for k, v, (fx, fy), hide in fields:
            eff = ["effects", ["font", ["size", "1.27", "1.27"]]]
            if hide:
                eff.append(["hide", "yes"])
            node.append(["property", q(k), q(v), ["at", fmt(fx), fmt(fy), "0"], eff])
        for num, p in pins.items():
            if p[5] in (0, unit):
                node.append(["pin", q(num), ["uuid", uid()]])
        node.append(["instances", ["project", q(self.project),
                                   ["path", q(self.path), ["reference", q(ref)], ["unit", str(unit)]]]])
        self.items.append(node)
        pl = Placed(self, lib_id, ref, (x, y), unit, {n: p for n, p in pins.items() if p[5] in (0, unit)})
        if not ref.startswith("#"):
            self.placed[ref] = pl
        return pl

    # --- primitives
    def wire(self, a, b):
        self.items.append(["wire", ["pts", ["xy", fmt(a[0]), fmt(a[1])], ["xy", fmt(b[0]), fmt(b[1])]],
                           ["stroke", ["width", "0"], ["type", "default"]], ["uuid", uid()]])

    def label(self, net, at, angle, kind="global_label", shape="passive"):
        just = {0: "left", 180: "right", 90: "left", 270: "right"}[angle]
        if kind == "label":
            node = ["label", q(net), ["at", fmt(at[0]), fmt(at[1]), str(angle)],
                    ["effects", ["font", ["size", "1.27", "1.27"]], ["justify", just, "bottom"]], ["uuid", uid()]]
        else:
            node = ["global_label", q(net), ["shape", shape], ["at", fmt(at[0]), fmt(at[1]), str(angle)],
                    ["fields_autoplaced", "yes"],
                    ["effects", ["font", ["size", "1.27", "1.27"]], ["justify", just]], ["uuid", uid()],
                    ["property", '"Intersheetrefs"', '"${INTERSHEET_REFS}"', ["at", fmt(at[0]), fmt(at[1]), "0"],
                     ["effects", ["font", ["size", "1.27", "1.27"]], ["hide", "yes"]]]]
        self.items.append(node)

    def no_connect(self, at):
        self.items.append(["no_connect", ["at", fmt(at[0]), fmt(at[1])], ["uuid", uid()]])

    def text(self, s, at, size=1.27):
        self.items.append(["text", q(s).replace("\n", "\\n"), ["exclude_from_sim", "no"],
                           ["at", fmt(at[0]), fmt(at[1]), "0"],
                           ["effects", ["font", ["size", str(size), str(size)]], ["justify", "left", "top"]],
                           ["uuid", uid()]])

    def power(self, net, at):
        """Power port symbol (power:GND, power:+3V3, ...) or, for custom rails, a global label."""
        self._pwr += 1
        if net in ("GND", "+3V3", "+5V", "+3.3V", "VBUS"):
            self.add(f"power:{net}", f"#PWR{self._pwr:03d}", net, at)
        else:
            self.label(net, at, 270 if net == "GND" else 90, shape="passive")

    def pwr_flag(self, net, at):
        self._pwr += 1
        self.add("power:PWR_FLAG", f"#FLG{self._pwr:03d}", "PWR_FLAG", at)
        if net in ("GND", "+3V3", "+5V"):
            self.power(net, at)
        else:
            self.label(net, at, 90, shape="passive")

    # --- connections
    def _stub(self, part, pin):
        x, y, a = part.pin_xy(pin)
        dx, dy = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[int(a) % 360]
        end = (x + dx * STUB, y + dy * STUB)
        self.wire((x, y), end)
        lab_angle = {(-1, 0): 180, (1, 0): 0, (0, 1): 270, (0, -1): 90}[(dx, dy)]
        return end, lab_angle

    def connect(self, part, pin, net, shape="passive", kind=None):
        if kind is None:
            kind = "label" if net in self.locals else "global_label"
        elif kind == "label":
            self.locals.add(net)
        for p in ([pin] if not isinstance(pin, (list, tuple)) else pin):
            end, ang = self._stub(part, p)
            if net in ("GND", "+3V3", "+5V"):
                self.power(net, end)
            else:
                self.label(net, end, ang, kind=kind, shape=shape)

    def nc(self, part, pin):
        x, y, _ = part.pin_xy(pin)
        self.no_connect((x, y))

    def two_pin(self, lib_id, ref, value, at, net1, net2, footprint, vertical=True, dnp=False, props=None):
        """Place a 2-pin part (R/C/LED/D) and connect pin 1 to net1, pin 2 to net2."""
        p = self.add(lib_id, ref, value, at, footprint=footprint, dnp=dnp, props=props)
        self.connect(p, "1", net1)
        self.connect(p, "2", net2)
        return p

    # --- output
    def write(self, path, title, comment="", paper="A3", keep_notes=None):
        root = ["kicad_sch", ["version", "20250114"], ["generator", '"eeschema"'], ["generator_version", '"9.0"'],
                ["uuid", q(self.page_uuid)], ["paper", q(paper)],
                ["title_block", ["title", q(title)], ["rev", '"A"'], ["comment", "1", q(comment)]],
                ["lib_symbols"] + list(self.lib_symbols.values())]
        if keep_notes:
            root.append(keep_notes)
        root += self.items
        root.append(["embedded_fonts", "no"])
        Path(path).write_text(dump(root) + "\n", encoding="utf-8", newline="\n")


def sheet_uuids(root_sch):
    """{sheet file name: sheet-symbol uuid} plus the root uuid, from the top-level schematic."""
    tree = parse(Path(root_sch).read_text(encoding="utf-8"))[0]
    root_uuid = unq(find(tree, "uuid")[0][1])
    out = {}
    for sh in find(tree, "sheet"):
        file = [unq(p[2]) for p in find(sh, "property") if unq(p[1]) == "Sheetfile"][0]
        out[file] = unq(find(sh, "uuid")[0][1])
    return root_uuid, out


def existing_notes(sheet_file):
    """Return the DESIGN NOTES text_box node of an existing sheet (to keep it)."""
    tree = parse(Path(sheet_file).read_text(encoding="utf-8"))[0]
    for tb in find(tree, "text_box"):
        if unq(tb[1]).startswith("DESIGN NOTES"):
            return tb
    return None
