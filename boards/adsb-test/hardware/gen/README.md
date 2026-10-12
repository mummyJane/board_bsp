# Generated schematic sheets

Some ADSB_Test sheets are generated from Python with
[`tools/kicad_sch_gen.py`](../../../../tools/kicad_sch_gen.py).

How it works:
- Symbols are copied from the KiCad 10 libraries and the project library and
  placed on the sheet.
- Every pin gets a short wire stub ending in a net label, power symbol or
  no-connect flag.
- Connectivity is by net name. **Global labels** are cross-sheet nets and
  **local labels** are sheet-only nets. The result is a normal KiCad
  schematic: ERC checks it and it can be tidied by hand.

| Sheet | Script | Status |
|-------|--------|--------|
| M1421 (page 14) | [gen_m1421.py](gen_m1421.py) | Generated. ERC: only the expected cross-sheet "not driven" items until the P4 / USB Dev sheets exist |

## Regenerate a sheet

```powershell
python boards\adsb-test\hardware\gen\gen_m1421.py
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch upgrade boards\adsb-test\hardware\kicad\m1421.kicad_sch
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch erc --severity-all boards\adsb-test\hardware\kicad\ADSB_Test.kicad_sch
```

**Regenerating overwrites the sheet.** Once a sheet has been tidied or edited
by hand in KiCad, stop regenerating it: mark it "frozen" in the table above and
edit it in KiCad from then on.

## Conventions

- Reference designators: the sheet's page number × 100 (M1421 = page 14 →
  U1401, R1401, …).
- Net names: `P4_*` = driven by the P4, `DEV_*` = from the Dev-port domain,
  `M1421_*` = the m1421 side, rails like `3V3_M1421` are global labels.
- Temporary `PWR_FLAG`s ("staging") keep ERC useful until the power sheets
  drive the rails. Remove them when the power sheets are generated.
