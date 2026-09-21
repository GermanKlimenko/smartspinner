# SmartSpinner v0.4 - PCB layout completion and PCBA RFQ

## Purpose

This package is for engineering review, completion of the PCB layout, DFM, sourcing and a budgetary turnkey-PCBA quotation. It is **not authorized for fabrication in its current state**.

## Quantity

- 10 complete electronic sets: 10 main four-arm PCBs plus 40 identical vertical tip PCBs.
- Please also quote 5-set and 25-set alternatives.
- Build one first article before releasing the remainder.

## Included

- KiCad main and tip board sources with routed pixel chains.
- Review-only Gerber and Excellon outputs.
- BOM with preferred MPNs and sourcing identifiers.
- KiCad position/CPL files.
- Four-page electrical architecture PDF and two-page fabrication drawing.
- Net summary, power budget, bring-up procedure and machine-readable DRC status.
- Mechanical v0.3 STEP/STL/DXF package and enclosure drawings.

## Work requested from supplier

1. Close all open connections listed in the KiCad DRC reports.
2. Replace/verify embedded custom footprints against exact manufacturer land patterns and pin-1 orientation.
3. Complete the TPS61023 boost, MCP73831 charge and decoupling networks from datasheets.
4. Review the Raytac antenna keep-out on all copper layers and against the enclosure.
5. Run DFM and return updated editable KiCad sources for approval.
6. After approval, regenerate fabrication Gerbers, assemble one first article and perform AOI plus the supplied electrical test sequence.

## Architecture

- Four-arm main PCB, up to 96 mm envelope, 1.0 mm four-layer target.
- 80 top SK6805-EC15 pixels in four independent 20-pixel chains.
- Four 0.6 mm tip boards, each with 12 SK6805-EC10 pixels on a separate data chain.
- Eight LED streams total through two 74AHCT125 devices.
- Raytac MDBT50Q-1MV2 (nRF52840), DRV5033 Hall sensor and BMI270 IMU.
- Protected 1S LiPo domain, 3.3 V logic and switched 5 V LED rail.
- Batteries excluded from the shipment.

## Public references

- Website: https://germanklimenko.github.io/smartspinner/
- Repository: https://github.com/GermanKlimenko/smartspinner
- Electronics package: https://germanklimenko.github.io/smartspinner/project-files/SmartSpinner_v0_4_electronics_ERC.zip
- Mechanical package: https://germanklimenko.github.io/smartspinner/project-files/ticker_spinner_v0_3_complete_package.zip
