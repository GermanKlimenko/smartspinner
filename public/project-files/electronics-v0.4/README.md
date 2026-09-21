# Smart Spinner electronics v0.4 - Engineering Release Candidate

This package substantially closes the documentation gap of mechanical v0.3: it defines the electrical architecture, component selection, two KiCad PCB candidates with fully routed pixel chains, Gerbers, drill files, BOM, CPL/position data, assembly drawings, schematic PDF, power budget and bring-up plan.

## Board set

- Main board: four-layer, 1.0 mm, approximately 96 x 96 mm, 23.2 mm center hole, four M2 NPTH holes.
- Four identical tip boards: two-layer, 0.6 mm, 7.0 x 13.6 mm.
- Pixels: 80 top SK6805-EC15 plus 48 tip SK6805-EC10, split into eight independent chains (4 x 20 top and 4 x 12 tip).
- Controller: Raytac MDBT50Q-1MV2 (nRF52840); Hall index and BMI270 IMU.
- Power: protected 1S LiPo, 3.3 V logic LDO, switched TPS61023 5 V LED rail.

## Release status

This is an **engineering package for quotation and layout completion**, not yet a release for fabrication. The board geometry and pixel-chain routing are real and machine-readable, but the central power/control fan-out still has open connections. KiCad's generated DRC reports are included as the source of truth. No physical prototype has yet verified RF performance, Hall phase jitter, LED footprint orientation, thermal margin, battery current or balance.

Current generated DRC state (do not waive): main board has no track shorts after generation but retains open central/interface connections; the tip board retains four open interface fan-outs. Cosmetic silkscreen warnings are also present. The exact counts are recorded in `smartspinner_main_v0_4_drc.txt`, `smartspinner_tip_v0_4_drc.txt` and `smartspinner_v0_4_release_status.json`.

Before fabrication the assembler must:

1. Close every unconnected item in both DRC reports; rerun DRC with zero copper errors before plotting fabrication Gerbers.
2. Map every custom embedded footprint to the exact MPN land pattern and confirm pin-1 orientation.
3. Review the Raytac antenna keep-out on all copper/paste/mask layers and request an RF DFM check.
4. Complete/verify the boost passive network and all decoupling against component datasheets.
5. Confirm 4-layer stackup, 1.0 mm main board and 0.6 mm tip boards; panelize tip boards.
6. Build one first article, test it in a guarded fixture, then authorize the remaining nine.

## Files

- `smartspinner_main_v0_4.kicad_pcb`, `smartspinner_tip_v0_4.kicad_pcb` - editable PCB sources.
- `gerber/` - review-only copper, mask, silkscreen, edge cuts and Excellon drill outputs; regenerate after zero-error DRC.
- `assembly/*.csv` - KiCad position files (CPL source).
- `smartspinner_v0_4_bom.csv` - purchasing BOM with exact preferred MPNs and sourcing identifiers.
- `smartspinner_v0_4_netlist.csv` - interface/net summary.
- `smartspinner_v0_4_schematic.pdf` - four-page electrical design specification.
- `smartspinner_v0_4_fabrication_drawing.pdf` - dimensions, stackup and acceptance notes.
- `smartspinner_v0_4_power_budget.json` - preliminary energy model.
- `smartspinner_v0_4_bringup.md` - first-article test and safety procedure.

## Safety

Use only protected matched cells with welded tabs, physically retained by the enclosure. Do not charge while spinning. First spin tests must use a polycarbonate guard, remote drive and staged RPM limits. A complete loss-of-part containment test is required before handheld demonstrations.
