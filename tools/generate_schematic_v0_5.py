#!/usr/bin/env python3
"""Generate the editable SmartSpinner v0.5 review schematic.

The file is intentionally an engineering-review schematic, not a fabrication
release.  It captures the selected parts, pin assignments and every external
net needed to finish the PCB.  Repeated addressable LED strings are represented
as electrically equivalent chain blocks; the exact 80 + 48 LED references are
already present in the v0.4 PCB/BOM package and must be forward-annotated during
layout completion.

Requires kiutils (tested with 1.4.8) and KiCad 10 CLI for PDF/ERC export.
"""

from __future__ import annotations

import csv
import copy
import json
import os
import shutil
import subprocess
import sys
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

from kiutils.items.common import Effects, Fill, Font, Justify, PageSettings, Position, Property, Stroke, TitleBlock
from kiutils.items.schitems import LocalLabel, NoConnect, SchematicSymbol, SymbolProjectInstance, SymbolProjectPath, Text, TextBox
from kiutils.items.syitems import SyRect
from kiutils.schematic import Schematic
from kiutils.symbol import Symbol, SymbolLib, SymbolPin


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "project-files" / "electronics-v0.5"
PROJECT_FILES = ROOT / "public" / "project-files"
KICAD = Path("/opt/homebrew/Caskroom/kicad/10.0.6/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
SCHEMATIC = OUT / "smartspinner_main_v0_5.kicad_sch"
PDF = OUT / "smartspinner_main_v0_5_schematic.pdf"
ERC = OUT / "smartspinner_main_v0_5_erc.txt"


@dataclass(frozen=True)
class Pin:
    number: str
    name: str
    net: str | None
    side: str = "L"


def uid() -> str:
    return str(uuid.uuid4())


def fx(size: float = 1.0, *, bold: bool = False, hide: bool = False, justify: str | None = None) -> Effects:
    return Effects(
        font=Font(height=size, width=size, bold=bold),
        justify=Justify(horizontally=justify),
        hide=hide,
    )


def prop(key: str, value: str, x: float, y: float, *, hide: bool = False, size: float = 1.0) -> Property:
    return Property(key=key, value=value, position=Position(x, y, 0), effects=fx(size, hide=hide))


def make_symbol(name: str, pins: list[Pin], width: float = 20.32) -> Symbol:
    left = [p for p in pins if p.side == "L"]
    right = [p for p in pins if p.side == "R"]
    rows = max(len(left), len(right), 1)
    height = max(10.16, rows * 2.54 + 2.54)
    body = Symbol(
        entryName=name,
        unitId=1,
        styleId=1,
        graphicItems=[
            SyRect(
                start=Position(-width / 2, height / 2),
                end=Position(width / 2, -height / 2),
                stroke=Stroke(width=0.254, type="default"),
                fill=Fill(type="background"),
            )
        ],
    )
    for side_pins, side in ((left, "L"), (right, "R")):
        for i, pin in enumerate(side_pins):
            y = (len(side_pins) - 1) * 1.27 - i * 2.54
            x = -width / 2 - 5.08 if side == "L" else width / 2 + 5.08
            body.pins.append(
                SymbolPin(
                    electricalType="passive",
                    graphicalStyle="line",
                    position=Position(x, y, 0 if side == "L" else 180),
                    length=5.08,
                    name=pin.name,
                    nameEffects=fx(0.85),
                    number=pin.number,
                    numberEffects=fx(0.85),
                )
            )
    return Symbol(
        libraryNickname="SmartSpinner",
        entryName=name,
        pinNames=True,
        pinNamesOffset=0.8,
        inBom=True,
        onBoard=True,
        properties=[
            prop("Reference", "U", 0, height / 2 + 2.54),
            prop("Value", name, 0, -height / 2 - 2.54),
            prop("Footprint", "", 0, 0, hide=True),
            prop("Datasheet", "", 0, 0, hide=True),
            prop("Description", "SmartSpinner v0.5 review symbol", 0, 0, hide=True),
        ],
        units=[body],
    )


def place(s: Schematic, ref: str, value: str, pins: list[Pin], x: float, y: float, *, width: float = 20.32, footprint: str = "", datasheet: str = "") -> None:
    lib_name = f"{ref}_{value}".replace(" ", "_").replace("/", "_")
    lib = make_symbol(lib_name, pins, width)
    lib.properties[0].value = ref.rstrip("0123456789") or ref
    lib.properties[1].value = value
    lib.properties[2].value = footprint
    lib.properties[3].value = datasheet
    s.libSymbols.append(lib)

    height = max(10.16, max(sum(p.side == "L" for p in pins), sum(p.side == "R" for p in pins), 1) * 2.54 + 2.54)
    pin_ids = {p.number: uid() for p in pins}
    inst = SchematicSymbol(
        libraryNickname="SmartSpinner",
        entryName=lib_name,
        position=Position(x, y, 0),
        unit=1,
        inBom=True,
        onBoard=True,
        uuid=uid(),
        properties=[
            prop("Reference", ref, x, y - height / 2 - 2.3, size=1.05),
            prop("Value", value, x, y + height / 2 + 2.3, size=0.95),
            prop("Footprint", footprint, x, y, hide=True),
            prop("Datasheet", datasheet, x, y, hide=True),
            prop("Description", "SmartSpinner v0.5 engineering-review schematic", x, y, hide=True),
        ],
        pins=pin_ids,
        instances=[
            SymbolProjectInstance(
                name="smartspinner_main_v0_5",
                paths=[SymbolProjectPath(sheetInstancePath=f"/{s.uuid}", reference=ref, unit=1)],
            )
        ],
    )
    s.schematicSymbols.append(inst)

    for side_pins, side in (([p for p in pins if p.side == "L"], "L"), ([p for p in pins if p.side == "R"], "R")):
        for i, pin in enumerate(side_pins):
            py = y + (len(side_pins) - 1) * 1.27 - i * 2.54
            px = x - width / 2 - 5.08 if side == "L" else x + width / 2 + 5.08
            if pin.net is None:
                s.noConnects.append(NoConnect(position=Position(px, py), uuid=uid()))
            else:
                s.labels.append(
                    LocalLabel(
                        text=pin.net,
                        position=Position(px, py, 0 if side == "L" else 180),
                        effects=fx(0.8, justify="right" if side == "L" else "left"),
                        uuid=uid(),
                    )
                )


def note(s: Schematic, text: str, x: float, y: float, w: float, h: float, *, title: bool = False) -> None:
    if title:
        s.texts.append(Text(text=text, position=Position(x, y, 0), effects=fx(2.0, bold=True), uuid=uid()))
    else:
        s.textBoxes.append(
            TextBox(
                text=text.replace("\n", "\\n"),
                position=Position(x, y, 0),
                size=Position(w, h),
                stroke=Stroke(width=0.25, type="default"),
                fill=Fill(type="none"),
                effects=fx(0.9),
                uuid=uid(),
            )
        )


def two_pin(ref: str, value: str, a: str, b: str) -> tuple[str, str, list[Pin]]:
    return ref, value, [Pin("1", "1", a, "L"), Pin("2", "2", b, "R")]


def build_schematic() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    s = Schematic.create_new()
    s.uuid = uid()
    s.paper = PageSettings(paperSize="A2", portrait=False)
    s.titleBlock = TitleBlock(
        title="SMARTSPINNER v0.5 - PRINCIPLE SCHEMATIC FOR ENGINEERING REVIEW",
        date="2026-09-22",
        revision="v0.5-review",
        company="German Klimenko / SmartSpinner",
        comments={
            1: "NOT FOR FABRICATION. Validate footprints, current limits, thermal design and antenna keep-out.",
            2: "4 arms x 20 top LEDs + 4 replaceable tip boards x 12 LEDs.",
            3: "All named labels are electrical nets. Repeated LED strings are equivalent chain blocks.",
        },
    )

    note(s, "POWER / CHARGING", 28, 20, 0, 0, title=True)
    place(s, "J1", "CHARGE_PADS", [Pin("1", "CHG_5V", "CHG_5V", "L"), Pin("2", "GND", "GND", "L")], 35, 42, width=15)
    place(s, "U5", "MCP73831-2ACI/OT", [
        Pin("4", "VDD", "CHG_5V", "L"), Pin("5", "PROG", "MCP_PROG", "L"), Pin("2", "VSS", "GND", "L"),
        Pin("3", "VBAT", "VBAT", "R"), Pin("1", "STAT", "CHG_STAT", "R"),
    ], 77, 42, width=24, footprint="Package_TO_SOT_SMD:SOT-23-5", datasheet="https://ww1.microchip.com/downloads/en/DeviceDoc/20001984g.pdf")
    for args, pos in [
        (two_pin("R1", "10k PROG", "MCP_PROG", "GND"), (112, 28)),
        (two_pin("C1", "4.7uF CHG IN", "CHG_5V", "GND"), (112, 42)),
        (two_pin("C2", "4.7uF BAT", "VBAT", "GND"), (112, 56)),
    ]:
        place(s, *args, *pos, width=14)
    place(s, "J2", "PROTECTED_LIPO", [Pin("1", "BAT+", "VBAT", "L"), Pin("2", "BAT-", "GND", "L")], 35, 68, width=17)

    place(s, "U4", "TPS7A2033PDBVR", [
        Pin("1", "IN", "VBAT", "L"), Pin("3", "EN", "VBAT", "L"), Pin("2", "GND", "GND", "L"),
        Pin("5", "OUT", "3V3", "R"), Pin("4", "NC", None, "R"),
    ], 155, 40, width=22, footprint="Package_TO_SOT_SMD:SOT-23-5", datasheet="https://www.ti.com/lit/ds/symlink/tps7a20.pdf")
    place(s, *two_pin("C3", "1uF LDO IN", "VBAT", "GND"), 190, 28, width=14)
    place(s, *two_pin("C4", "1uF LDO OUT", "3V3", "GND"), 190, 48, width=14)

    place(s, "U3", "TPS61023DRLR", [
        Pin("3", "VIN", "VBAT", "L"), Pin("2", "EN", "LED_EN", "L"), Pin("1", "FB", "BOOST_FB", "L"), Pin("4", "GND", "GND", "L"),
        Pin("5", "SW", "BOOST_SW", "R"), Pin("6", "VOUT", "5V_RAW", "R"),
    ], 150, 84, width=22, footprint="Package_SON:Texas_DRL0006A_SOT-5X3-6_1.6x1.6mm_P0.5mm", datasheet="https://www.ti.com/lit/ds/symlink/tps61023.pdf")
    for args, pos in [
        (two_pin("L1", "2.2uH", "VBAT", "BOOST_SW"), (190, 72)),
        (two_pin("R2", "910k 1%", "5V_RAW", "BOOST_FB"), (190, 84)),
        (two_pin("R3", "100k 1%", "BOOST_FB", "GND"), (190, 96)),
        (two_pin("C5", "10uF BOOST IN", "VBAT", "GND"), (224, 72)),
        (two_pin("C6", "22uF BOOST OUT", "5V_RAW", "GND"), (224, 84)),
        (two_pin("C7", "22uF BOOST OUT", "5V_RAW", "GND"), (224, 96)),
    ]:
        place(s, *args, *pos, width=14)
    place(s, "U8", "TPS22918DBVR", [
        Pin("1", "VIN", "5V_RAW", "L"), Pin("3", "ON", "LED_EN", "L"), Pin("2", "GND", "GND", "L"),
        Pin("6", "VOUT", "+5V_LED", "R"), Pin("4", "CT", "LED_CT", "R"), Pin("5", "QOD", None, "R"),
    ], 268, 84, width=22, footprint="Package_TO_SOT_SMD:SOT-23-6", datasheet="https://www.ti.com/lit/ds/symlink/tps22918.pdf")
    place(s, *two_pin("C8", "1nF SOFT START", "LED_CT", "GND"), 302, 84, width=16)

    note(s, "CONTROL / SENSORS", 28, 119, 0, 0, title=True)
    mcu_pins = [
        Pin("28", "VDD", "3V3", "L"), Pin("30", "VDDH", "3V3", "L"), Pin("1", "GND", "GND", "L"), Pin("2", "GND", "GND", "L"),
        Pin("15", "GND", "GND", "L"), Pin("33", "GND", "GND", "L"), Pin("55", "GND", "GND", "L"), Pin("31", "DCCH", "DCCH", "L"),
        Pin("32", "VBUS", None, "L"), Pin("34", "D-", None, "L"), Pin("35", "D+", None, "L"), Pin("51", "SWDIO", "SWDIO", "L"), Pin("53", "SWDCLK", "SWDCLK", "L"),
        Pin("9", "P0.03", "TOP_A", "R"), Pin("20", "P0.04", "TOP_B", "R"), Pin("21", "P0.05", "TOP_C", "R"), Pin("22", "P0.06", "TOP_D", "R"),
        Pin("23", "P0.07", "TIP_A", "R"), Pin("24", "P0.08", "TIP_B", "R"), Pin("52", "P0.09", "TIP_C", "R"), Pin("54", "P0.10", "TIP_D", "R"),
        Pin("27", "P0.11", "HALL_INT", "R"), Pin("29", "P0.12", "LED_EN", "R"), Pin("37", "P0.13", "IMU_INT", "R"), Pin("36", "P0.14", "CHG_STAT", "R"),
        Pin("40", "P0.18", "RESET_N", "R"), Pin("19", "P0.26", "SDA", "R"), Pin("16", "P0.27", "SCL", "R"), Pin("11", "P0.02", "VBAT_SENSE", "R"),
    ]
    place(s, "U1", "MDBT50Q-1MV2 nRF52840", mcu_pins, 75, 165, width=33, footprint="RF_Module:Raytac_MDBT50Q-1MV2", datasheet="https://www.raytac.com/download/index.php?index_id=24")
    place(s, *two_pin("L2", "10uH DCCH", "DCCH", "3V3"), 29, 155, width=15)
    place(s, *two_pin("R4", "1M 1%", "VBAT", "VBAT_SENSE"), 29, 170, width=14)
    place(s, *two_pin("R5", "330k 1%", "VBAT_SENSE", "GND"), 29, 184, width=14)
    place(s, "J3", "SWD_TAG_CONNECT", [
        Pin("1", "3V3", "3V3", "L"), Pin("2", "SWDIO", "SWDIO", "L"), Pin("3", "SWDCLK", "SWDCLK", "L"),
        Pin("4", "RESET", "RESET_N", "L"), Pin("5", "GND", "GND", "L"),
    ], 133, 145, width=19)

    place(s, "U6", "DRV5033AJQLPGM", [Pin("1", "VCC", "3V3", "L"), Pin("2", "GND", "GND", "L"), Pin("3", "OUT", "HALL_INT", "R")], 135, 175, width=22, footprint="Package_TO_SOT_SMD:SOT-23", datasheet="https://www.ti.com/lit/ds/symlink/drv5033.pdf")
    place(s, *two_pin("R6", "10k HALL PULLUP", "HALL_INT", "3V3"), 175, 174, width=18)
    place(s, "U7", "BMI270", [
        Pin("5", "VDDIO", "3V3", "L"), Pin("8", "VDD", "3V3", "L"), Pin("6", "GNDIO", "GND", "L"), Pin("7", "GND", "GND", "L"),
        Pin("12", "CSB", "3V3", "L"), Pin("1", "SDO/SA0", "GND", "L"), Pin("14", "SDX/SDA", "SDA", "R"), Pin("13", "SCX/SCL", "SCL", "R"),
        Pin("4", "INT1", "IMU_INT", "R"), Pin("9", "INT2", None, "R"), Pin("2", "ASDx", None, "R"), Pin("3", "ASCx", None, "R"),
        Pin("10", "OCSB", None, "R"), Pin("11", "OSDO", None, "R"),
    ], 223, 164, width=25, footprint="Package_LGA:Bosch_LGA-14_3x2.5mm_P0.5mm", datasheet="https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf")
    for args, pos in [
        (two_pin("R7", "4.7k I2C", "SDA", "3V3"), (267, 145)),
        (two_pin("R8", "4.7k I2C", "SCL", "3V3"), (267, 159)),
        (two_pin("C9", "100nF VDDIO", "3V3", "GND"), (267, 177)),
        (two_pin("C10", "100nF VDD", "3V3", "GND"), (267, 191)),
    ]:
        place(s, *args, *pos, width=16)

    note(s, "LEVEL SHIFT / LED DATA", 28, 216, 0, 0, title=True)
    top_buf = [Pin("14", "VCC", "+5V_LED", "L"), Pin("7", "GND", "GND", "L")]
    tip_buf = [Pin("14", "VCC", "+5V_LED", "L"), Pin("7", "GND", "GND", "L")]
    for i, ch in enumerate("ABCD"):
        top_buf += [Pin(str(1 + i * 3), f"{i+1}OE", "GND", "L"), Pin(str(2 + i * 3), f"{i+1}A", f"TOP_{ch}", "L"), Pin(str(3 + i * 3), f"{i+1}Y", f"TOP_{ch}_5V", "R")]
        tip_buf += [Pin(str(1 + i * 3), f"{i+1}OE", "GND", "L"), Pin(str(2 + i * 3), f"{i+1}A", f"TIP_{ch}", "L"), Pin(str(3 + i * 3), f"{i+1}Y", f"TIP_{ch}_5V", "R")]
    # Correct standard package pin numbers for gates 3/4.
    top_buf = [Pin("14", "VCC", "+5V_LED", "L"), Pin("7", "GND", "GND", "L"),
        Pin("1", "1OE", "GND", "L"), Pin("2", "1A", "TOP_A", "L"), Pin("3", "1Y", "TOP_A_5V", "R"),
        Pin("4", "2OE", "GND", "L"), Pin("5", "2A", "TOP_B", "L"), Pin("6", "2Y", "TOP_B_5V", "R"),
        Pin("10", "3OE", "GND", "L"), Pin("9", "3A", "TOP_C", "L"), Pin("8", "3Y", "TOP_C_5V", "R"),
        Pin("13", "4OE", "GND", "L"), Pin("12", "4A", "TOP_D", "L"), Pin("11", "4Y", "TOP_D_5V", "R")]
    tip_buf = [Pin(p.number, p.name, p.net.replace("TOP", "TIP") if p.net else p.net, p.side) for p in top_buf]
    place(s, "U2", "74AHCT125PW TOP", top_buf, 72, 255, width=28, footprint="Package_SO:TSSOP-14_4.4x5mm_P0.65mm", datasheet="https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT125.pdf")
    place(s, "U9", "74AHCT125PW TIP", tip_buf, 155, 255, width=28, footprint="Package_SO:TSSOP-14_4.4x5mm_P0.65mm", datasheet="https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT125.pdf")

    chains = []
    for i, ch in enumerate("ABCD"):
        chains.append((f"D{1+i*20}-D{20+i*20}", f"20x SK6805-EC15 TOP {ch}", f"TOP_{ch}_5V", 225 + (i % 2) * 62, 230 + (i // 2) * 30))
        chains.append((f"TD{1+i*12}-TD{12+i*12}", f"12x SK6805-EC10 TIP {ch}", f"TIP_{ch}_5V", 225 + (i % 2) * 62, 288 + (i // 2) * 30))
    for ref, value, din, x, y in chains:
        place(s, ref, value, [Pin("1", "DIN", din, "L"), Pin("2", "VDD", "+5V_LED", "L"), Pin("3", "GND", "GND", "L"), Pin("4", "DOUT", None, "R")], x, y, width=31)

    note(s, "ENGINEERING REVIEW NOTES", 28, 330, 0, 0, title=True)
    note(s,
        "1. This is the first editable principle schematic; the earlier v0.4 PDF was an architecture document and was incorrectly named.\n"
        "2. Repeated LED strings are shown as chain blocks. Expand/annotate all 128 LED references when synchronizing schematic and PCB.\n"
        "3. Protected 1S LiPo required. No battery is to be connected before charger polarity and protection are verified.\n"
        "4. TPS61023 divider 910k/100k targets about 5.05 V from the 0.5 V feedback reference; validate against final LED voltage/current budget.\n"
        "5. TPS22918 is limited to 2 A continuous. Firmware must cap brightness/current; thermal and transient tests are mandatory.\n"
        "6. Verify every footprint against the purchased MPN, especially BMI270 LGA and SK6805 LED variants.\n"
        "7. RF antenna copper/ground/component keep-out and dynamic balance must be reviewed before first article.\n"
        "8. This review file does not authorize fabrication. Release only after independent schematic review, ERC/DRC closure and DFM.",
        28, 338, 284, 44)

    s.to_file(SCHEMATIC)
    external_symbols = copy.deepcopy(s.libSymbols)
    for symbol in external_symbols:
        symbol.libraryNickname = None
    SymbolLib(generator="kiutils", symbols=external_symbols).to_file(OUT / "smartspinner_v0_5.kicad_sym")
    (OUT / "sym-lib-table").write_text(
        '(sym_lib_table\n'
        '  (version 7)\n'
        '  (lib (name "SmartSpinner")(type "KiCad")(uri "${KIPRJMOD}/smartspinner_v0_5.kicad_sym")(options "")(descr "SmartSpinner v0.5 review symbols"))\n'
        ')\n',
        encoding="utf-8",
    )


def write_pinmap() -> None:
    rows = [
        ("P0.03", "TOP_A", "U2 gate 1 -> arm A top LED chain"),
        ("P0.04", "TOP_B", "U2 gate 2 -> arm B top LED chain"),
        ("P0.05", "TOP_C", "U2 gate 3 -> arm C top LED chain"),
        ("P0.06", "TOP_D", "U2 gate 4 -> arm D top LED chain"),
        ("P0.07", "TIP_A", "U9 gate 1 -> arm A tip board"),
        ("P0.08", "TIP_B", "U9 gate 2 -> arm B tip board"),
        ("P0.09", "TIP_C", "U9 gate 3 -> arm C tip board"),
        ("P0.10", "TIP_D", "U9 gate 4 -> arm D tip board"),
        ("P0.11", "HALL_INT", "Hall revolution index"),
        ("P0.12", "LED_EN", "5 V LED rail enable"),
        ("P0.13", "IMU_INT", "BMI270 INT1"),
        ("P0.14", "CHG_STAT", "MCP73831 charge status"),
        ("P0.18", "RESET_N", "Debug/reset"),
        ("P0.26", "SDA", "BMI270 I2C data"),
        ("P0.27", "SCL", "BMI270 I2C clock"),
        ("P0.02", "VBAT_SENSE", "Battery divider ADC"),
    ]
    with (OUT / "smartspinner_v0_5_gpio_pinmap.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["nRF52840 pin", "net", "function"])
        w.writerows(rows)


def write_readme() -> None:
    (OUT / "README.md").write_text(
        """# SmartSpinner v0.5 principle schematic - engineering review

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
""",
        encoding="utf-8",
    )


def run_exports() -> dict[str, object]:
    if not KICAD.exists():
        raise SystemExit(f"KiCad CLI not found: {KICAD}")
    commands = [
        [str(KICAD), "sch", "export", "pdf", "--output", str(PDF), str(SCHEMATIC)],
        [str(KICAD), "sch", "erc", "--severity-all", "--exit-code-violations", "--output", str(ERC), str(SCHEMATIC)],
    ]
    results = []
    for command in commands:
        proc = subprocess.run(command, text=True, capture_output=True, cwd=OUT)
        results.append({"command": command, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})
    return {"commands": results}


def write_status(results: dict[str, object]) -> None:
    status = {
        "release": "v0.5 principle schematic - ENGINEERING REVIEW - NOT FOR FABRICATION",
        "generated": "2026-09-22",
        "scope": ["power", "charging", "MCU/BLE", "Hall", "IMU", "level shifting", "4x20 top LED chains", "4x12 tip LED chains"],
        "known_actions": [
            "Independent schematic review",
            "Expand and annotate 128 LED references",
            "Verify footprints and exact manufacturer part numbers",
            "Synchronize schematic with PCB and close ERC/DRC",
            "RF/thermal/current review and manufacturer DFM",
        ],
        **results,
    }
    (OUT / "smartspinner_v0_5_review_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_archives() -> None:
    review_zip = PROJECT_FILES / "SmartSpinner_v0_5_schematic_review.zip"
    with zipfile.ZipFile(review_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(OUT.iterdir()):
            if path.is_file():
                z.write(path, f"SmartSpinner_v0_5_schematic_review/{path.name}")

    rfq_zip = PROJECT_FILES / "SmartSpinner_v0_5_RFQ_Send_Package.zip"
    v04_zip = PROJECT_FILES / "SmartSpinner_v0_4_electronics_ERC.zip"
    mechanics_zip = PROJECT_FILES / "ticker_spinner_v0_3_complete_package.zip"
    with zipfile.ZipFile(rfq_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(review_zip, review_zip.name)
        if v04_zip.exists():
            z.write(v04_zip, v04_zip.name)
        if mechanics_zip.exists():
            z.write(mechanics_zip, mechanics_zip.name)
        z.writestr(
            "START_HERE_RU.txt",
            "SmartSpinner v0.5 - пакет для оценки работ.\n\n"
            "Начать с SmartSpinner_v0_5_schematic_review.zip. В нём новая редактируемая принципиальная схема KiCad, PDF, ERC и pin-map.\n"
            "Пакет v0.4 содержит существующие PCB/BOM/CPL/Gerber, но Gerber не разрешён к производству: PCB нужно синхронизировать с новой схемой, закрыть ERC/DRC и пройти DFM.\n"
            "Механика v0.3 приложена как габаритная основа.\n",
        )


def main() -> None:
    build_schematic()
    write_pinmap()
    write_readme()
    results = run_exports()
    write_status(results)
    make_archives()
    print(SCHEMATIC)
    print(PDF)
    print(ERC)


if __name__ == "__main__":
    main()
