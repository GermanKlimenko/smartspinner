# SmartSpinner v0.5 principle schematic - engineering review

This package fixes a documentation error in v0.4: the previous file called
`schematic.pdf` was an architecture/design-specification document, not an
editable principle schematic.

## Included

- `smartspinner_main_v0_5.kicad_sch` - editable KiCad 10 principle schematic;
- `smartspinner_main_v0_5_schematic.pdf` - printable export;
- `smartspinner_main_v0_5_erc.txt` - KiCad ERC output;
- `smartspinner_v0_5_gpio_pinmap.csv` - nRF52840 signal assignment;
- `smartspinner_v0_5_review_status.json` - scope and release status.

The circuit covers charging, protected 1S LiPo input, 3.3 V LDO, 5 V boost,
load switch/soft-start, nRF52840, Hall sensor, BMI270, two 74AHCT125 level
shifters, four 20-pixel top chains and four 12-pixel tip chains.

## Important limitation

This is a **review schematic, not a fabrication release**. Repeated LED chains
are represented as electrically equivalent blocks. During completion, the PCB
designer must expand/forward-annotate all 128 LED references, validate every
footprint and purchased MPN, close ERC/DRC, review RF keep-out and current/
thermal limits, and then generate a new production Gerber set.
