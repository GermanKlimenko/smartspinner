# SmartSpinner v0.3 — preliminary RFQ package

## Purpose

This package is intended for preliminary DFM discussion, sourcing feedback and a budgetary turnkey-PCBA quotation. It is not a production release.

## Requested quantity

- 10 complete electronic sets for the initial quotation.
- Each set: 1 main four-arm PCB and 4 vertical tip PCBs.
- Total: 10 main PCBs and 40 tip PCBs.
- Please also quote 5-set and 25-set alternatives.

## Available preliminary documentation

- Five-sheet mechanical engineering drawing.
- Parametric enclosure STL and STEP files.
- Main-PCB mechanical outline in DXF.
- Tip-PCB mechanical outline in DXF.
- Main and tip PCB mechanical STEP envelopes.
- Product-level visualizations and partner brief.
- Mechanical validation report and model generator.

## Files not yet released

- Electrical schematic.
- Routed PCB source files.
- Manufacturing Gerber and drill package.
- Final BOM with approved manufacturer part numbers.
- CPL / centroid / pick-and-place data.
- Assembly drawing and polarity map.
- Firmware binary and programming instructions.
- Functional-test procedure.

The missing files will be produced after preliminary supplier feedback. No file in the current package is authorized for production.

## Preliminary architecture

- Four-arm main PCB, approximately 96–100 mm overall diameter.
- 20 top-facing addressable RGB LEDs per arm, 80 total.
- Four vertical tip boards with 12 addressable RGB LEDs each, 48 total.
- nRF52840/BLE.
- Hall sensor plus IMU.
- LiPo charger and 3.3 V / 5 V power conversion.
- Batteries excluded from international shipment.

## Public reference links

- Website: https://germanklimenko.github.io/smartspinner/
- Repository: https://github.com/GermanKlimenko/smartspinner
- Engineering drawing: https://germanklimenko.github.io/smartspinner/project-files/ticker_spinner_v0_3_engineering_drawing.pdf
- Partner brief: https://germanklimenko.github.io/smartspinner/project-files/ticker_spinner_v0_3_partner_brief.pdf
- Complete preliminary package: https://germanklimenko.github.io/smartspinner/project-files/ticker_spinner_v0_3_complete_package.zip
