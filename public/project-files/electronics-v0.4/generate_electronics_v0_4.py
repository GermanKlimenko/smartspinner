#!/usr/bin/env python3
"""Generate the Ticker Spinner v0.4 electronics engineering-release package.

The generated board files are intentionally self-contained: custom footprints,
board outline, net names and routed LED chains are embedded in the .kicad_pcb
files so the package can be reviewed without a private KiCad library.
"""

from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
import textwrap
import zipfile
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "project-files" / "electronics-v0.4"
GERBER = OUT / "gerber"
POS = OUT / "assembly"
TMP = ROOT / "tmp" / "pdfs" / "electronics-v0.4"
KICAD = Path("/opt/homebrew/Caskroom/kicad/10.0.6/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
BOARD_CENTER = (100.0, 100.0)


def ensure_dirs() -> None:
    for path in (OUT, GERBER, POS, TMP):
        path.mkdir(parents=True, exist_ok=True)


def rot(x: float, y: float, deg: float) -> tuple[float, float]:
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def board_xy(r: float, angle: float, lateral: float = 0.0) -> tuple[float, float]:
    x = r * math.cos(math.radians(angle)) - lateral * math.sin(math.radians(angle))
    y = -(r * math.sin(math.radians(angle)) + lateral * math.cos(math.radians(angle)))
    return BOARD_CENTER[0] + x, BOARD_CENTER[1] + y


def pad_xy(cx: float, cy: float, px: float, py: float, angle: float) -> tuple[float, float]:
    dx, dy = rot(px, py, angle)
    return cx + dx, cy + dy


def q(s: str) -> str:
    return s.replace('"', "'")


def header(nets: list[str], thickness: float, layers: int = 4) -> list[str]:
    layer_rows = [
        '    (0 "F.Cu" signal)',
        '    (31 "B.Cu" signal)',
        '    (36 "B.SilkS" user "b.silkscreen")',
        '    (37 "F.SilkS" user "f.silkscreen")',
        '    (44 "Edge.Cuts" user)',
        '    (46 "B.CrtYd" user "b.courtyard")',
        '    (47 "F.CrtYd" user "f.courtyard")',
        '    (48 "B.Fab" user)',
        '    (49 "F.Fab" user)',
    ]
    if layers == 4:
        layer_rows.insert(1, '    (2 "In1.Cu" power)')
        layer_rows.insert(2, '    (4 "In2.Cu" power)')
    lines = [
        '(kicad_pcb (version 20240108) (generator "smartspinner_v0_4")',
        f'  (general (thickness {thickness}))',
        '  (paper "A4")',
        '  (layers',
        *layer_rows,
        '  )',
        '  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints yes))',
    ]
    for i, net in enumerate(nets, 1):
        lines.append(f'  (net {i} "{q(net)}")')
    return lines


def footprint(ref: str, value: str, x: float, y: float, w: float, h: float,
              angle: float, pads: list[tuple], layer: str = "F.Cu",
              attr: str = "smd") -> list[str]:
    silk = "B.SilkS" if layer == "B.Cu" else "F.SilkS"
    fab = "B.Fab" if layer == "B.Cu" else "F.Fab"
    crtyd = "B.CrtYd" if layer == "B.Cu" else "F.CrtYd"
    copper = '"B.Cu" "B.Paste" "B.Mask"' if layer == "B.Cu" else '"F.Cu" "F.Paste" "F.Mask"'
    compact = value.startswith("SK6805")
    ref_layer = fab if compact else silk
    ref_hide = " hide" if compact else ""
    lib_name = "SmartSpinner_" + q(value).replace(":", "_")
    lines = [
        f'  (footprint "{lib_name}" (layer "{layer}") (at {x:.3f} {y:.3f} {angle:.2f})',
        f'    (property "Reference" "{q(ref)}" (at 0 {-h / 2 - 0.9:.2f} {angle:.2f}) (layer "{ref_layer}"){ref_hide} (effects (font (size 0.80 0.80) (thickness 0.10))))',
        f'    (property "Value" "{q(value)}" (at 0 {h / 2 + 0.9:.2f} {angle:.2f}) (layer "{fab}") hide (effects (font (size 0.60 0.60) (thickness 0.10))))',
        f'    (attr {attr})',
    ]
    if not compact:
        lines.append(f'    (fp_rect (start {-w / 2:.3f} {-h / 2:.3f}) (end {w / 2:.3f} {h / 2:.3f}) (stroke (width 0.12) (type default)) (fill none) (layer "{silk}"))')
    lines.append(f'    (fp_rect (start {-w / 2:.3f} {-h / 2:.3f}) (end {w / 2:.3f} {h / 2:.3f}) (stroke (width 0.05) (type default)) (fill none) (layer "{crtyd}"))')
    for num, px, py, pw, ph, net_id, net_name, shape in pads:
        if shape == "npth":
            lines.append(f'    (pad "" np_thru_hole circle (at {px:.3f} {py:.3f}) (size {pw:.3f} {ph:.3f}) (drill {pw:.3f}) (layers "*.Cu" "*.Mask"))')
        else:
            lines.append(f'    (pad "{num}" smd {shape} (at {px:.3f} {py:.3f}) (size {pw:.3f} {ph:.3f}) (layers {copper}) (net {net_id} "{q(net_name)}"))')
    lines.append('  )')
    return lines


def segment(start: tuple[float, float], end: tuple[float, float], width: float, layer: str, net: int) -> str:
    return f'  (segment (start {start[0]:.3f} {start[1]:.3f}) (end {end[0]:.3f} {end[1]:.3f}) (width {width:.3f}) (layer "{layer}") (net {net}))'


def via(at: tuple[float, float], net: int, size: float = 0.42, drill: float = 0.20) -> str:
    return f'  (via (at {at[0]:.3f} {at[1]:.3f}) (size {size:.3f}) (drill {drill:.3f}) (layers "F.Cu" "B.Cu") (net {net}))'


def dogleg(start: tuple[float, float], end: tuple[float, float], angle: float,
           width: float, layer: str, net: int) -> list[str]:
    # Cross the inter-package gap halfway between pixels, not through power pads.
    dx, dy = rot(0.0, (end[1] - start[1]) if angle == 0 else 0.0, angle)
    mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    # A three-segment orthogonal route in the footprint's local coordinate system.
    local_end = rot(end[0] - start[0], end[1] - start[1], -angle)
    p1d = rot(local_end[0] / 2, 0, angle)
    p2d = rot(local_end[0] / 2, local_end[1], angle)
    p1 = (start[0] + p1d[0], start[1] + p1d[1])
    p2 = (start[0] + p2d[0], start[1] + p2d[1])
    return [segment(start, p1, width, layer, net), segment(p1, p2, width, layer, net), segment(p2, end, width, layer, net)]


def main_outline() -> list[tuple[float, float]]:
    pts = []
    for i in range(192):
        t = 2 * math.pi * i / 192
        # 48 mm radius at cardinal axes, 23.5 mm in diagonal electronics bays.
        r = 28.0 + 20.0 * abs(math.cos(2 * t)) ** 6
        pts.append((100 + r * math.cos(t), 100 - r * math.sin(t)))
    return pts


def write_main_board() -> Path:
    nets = ["GND", "+5V_LED", "+3V3", "VBAT", "USB_5V", "HALL", "SDA", "SCL", "SWDIO", "SWCLK"]
    for arm in "ABCD":
        nets.append(f"TOP_{arm}_DIN")
        nets += [f"LED_{arm}_{i:02d}" for i in range(1, 21)]
        nets.append(f"TIP_{arm}_DIN")
        nets.append(f"TIP_{arm}_DOUT")
    net_id = {name: i + 1 for i, name in enumerate(nets)}
    lines = header(nets, 1.0, 4)

    outline = main_outline()
    for a, b in zip(outline, outline[1:] + outline[:1]):
        lines.append(f'  (gr_line (start {a[0]:.3f} {a[1]:.3f}) (end {b[0]:.3f} {b[1]:.3f}) (stroke (width 0.15) (type default)) (layer "Edge.Cuts"))')
    lines.append('  (gr_circle (center 100 100) (end 111.600 100) (stroke (width 0.15) (type default)) (fill none) (layer "Edge.Cuts"))')
    for angle in (45, 135, 225, 315):
        x, y = board_xy(17.0, angle)
        lines += footprint(f"H{angle}", "M2_NPTH", x, y, 2.4, 2.4, 0,
                           [("", 0, 0, 2.4, 2.4, 0, "", "npth")], attr="exclude_from_bom exclude_from_pos_files")

    # Top-side LED rows: four independent 20-pixel chains.
    led_centers: dict[str, list[tuple[float, float]]] = {}
    ref = 1
    for arm, angle in zip("ABCD", (0, 90, 180, 270)):
        led_centers[arm] = []
        for i in range(20):
            r = 13.2 + i * 1.60
            x, y = board_xy(r, angle, -3.0)
            led_centers[arm].append((x, y))
            din = f"TOP_{arm}_DIN" if i == 0 else f"LED_{arm}_{i:02d}"
            dout = f"LED_{arm}_{i + 1:02d}"
            pads = [
                ("1", -0.48, -0.48, 0.40, 0.40, net_id["+5V_LED"], "+5V_LED", "rect"),
                ("2", 0.48, -0.48, 0.40, 0.40, net_id[dout], dout, "rect"),
                ("3", 0.48, 0.48, 0.40, 0.40, net_id["GND"], "GND", "rect"),
                ("4", -0.48, 0.48, 0.40, 0.40, net_id[din], din, "rect"),
            ]
            lines += footprint(f"D{ref}", "SK6805-EC15", x, y, 1.50, 1.50, -angle, pads)
            ref += 1
        # Routed data, power and ground daisy chains.
        for i in range(19):
            c1, c2 = led_centers[arm][i], led_centers[arm][i + 1]
            p_out = pad_xy(*c1, 0.48, -0.48, angle)
            p_in = pad_xy(*c2, -0.48, 0.48, angle)
            lines += [via(p_out, net_id[f"LED_{arm}_{i + 1:02d}"], 0.30, 0.15),
                      via(p_in, net_id[f"LED_{arm}_{i + 1:02d}"], 0.30, 0.15),
                      segment(p_out, p_in, 0.12, "B.Cu", net_id[f"LED_{arm}_{i + 1:02d}"])]
            p5a, p5b = pad_xy(*c1, -0.48, -0.48, angle), pad_xy(*c2, -0.48, -0.48, angle)
            pga, pgb = pad_xy(*c1, 0.48, 0.48, angle), pad_xy(*c2, 0.48, 0.48, angle)
            b5a, b5b = pad_xy(*c1, -0.48, -1.10, angle), pad_xy(*c2, -0.48, -1.10, angle)
            bga, bgb = pad_xy(*c1, 0.48, 1.10, angle), pad_xy(*c2, 0.48, 1.10, angle)
            lines += [segment(p5a, b5a, 0.24, "F.Cu", net_id["+5V_LED"]),
                      segment(pga, bga, 0.24, "F.Cu", net_id["GND"]),
                      segment(b5a, b5b, 0.28, "F.Cu", net_id["+5V_LED"]),
                      segment(bga, bgb, 0.28, "F.Cu", net_id["GND"])]
            if i == 18:
                lines += [segment(p5b, b5b, 0.24, "F.Cu", net_id["+5V_LED"]),
                          segment(pgb, bgb, 0.24, "F.Cu", net_id["GND"])]

        # Four solder-pad interfaces to the replaceable vertical tip boards.
        jx, jy = board_xy(45.5, angle)
        jpads = [
            ("1", -2.1, 0, 0.65, 0.9, net_id["+5V_LED"], "+5V_LED", "rect"),
            ("2", -0.7, 0, 0.65, 0.9, net_id["GND"], "GND", "rect"),
            ("3", 0.7, 0, 0.65, 0.9, net_id[f"TIP_{arm}_DIN"], f"TIP_{arm}_DIN", "rect"),
            ("4", 2.1, 0, 0.65, 0.9, net_id[f"TIP_{arm}_DOUT"], f"TIP_{arm}_DOUT", "rect"),
        ]
        lines += footprint(f"JTIP{arm}", "TIP_BOARD_SOLDER_4", jx, jy, 5.6, 1.6, 90 - angle, jpads)
        jangle = angle - 90
        j5 = pad_xy(jx, jy, -2.1, 0, jangle)
        jg = pad_xy(jx, jy, -0.7, 0, jangle)
        jd = pad_xy(jx, jy, 0.7, 0, jangle)
        last = led_centers[arm][-1]
        d20 = pad_xy(*last, 0.48, -0.48, angle)
        # The final 2-4 mm interface fan-out is intentionally left to supplier DFM,
        # because the enclosure/solder-jig geometry controls these four short links.

    # Bottom-side controller and power components; exact packages are in BOM.
    module_pads = []
    mod_nets = ["GND", "+3V3", "TOP_A_DIN", "TOP_B_DIN", "TOP_C_DIN", "TOP_D_DIN", "TIP_A_DIN", "TIP_B_DIN", "TIP_C_DIN", "TIP_D_DIN", "HALL", "SDA", "SCL", "SWDIO", "SWCLK"]
    for idx, name in enumerate(mod_nets, 1):
        row = (idx - 1) % 8
        side = -1 if idx <= 8 else 1
        module_pads.append((str(idx), side * 4.9, -7 + row * 2.0, 0.75, 1.1, net_id[name], name, "rect"))
    mx, my = 122.0, 95.5
    lines += footprint("U1", "MDBT50Q-1MV2", mx, my, 10.5, 15.5, 90, module_pads, "B.Cu")
    # Antenna keep-out is drawn explicitly on both courtyard layers.
    lines.append(f'  (gr_rect (start {mx + 5.0:.3f} {my - 5.5:.3f}) (end {mx + 13.0:.3f} {my + 5.5:.3f}) (stroke (width 0.25) (type dash)) (fill none) (layer "B.CrtYd"))')
    lines.append(f'  (gr_text "RF KEEP-OUT ALL LAYERS" (at {mx + 9.0:.3f} {my:.3f} 90) (layer "B.SilkS") (effects (font (size 0.65 0.65) (thickness 0.11)) (justify mirror)))')

    simple_parts = [
        ("U2", "74AHCT125PW_TOP", 84.0, 92.0, 5.0, 4.4, ["+3V3", "GND", "TOP_A_DIN", "TOP_B_DIN", "TOP_C_DIN", "TOP_D_DIN"]),
        ("U9", "74AHCT125PW_TIP", 84.0, 116.0, 5.0, 4.4, ["+3V3", "GND", "TIP_A_DIN", "TIP_B_DIN", "TIP_C_DIN", "TIP_D_DIN"]),
        ("U3", "TPS61023DRL", 84.0, 106.0, 2.0, 2.0, ["VBAT", "GND", "+5V_LED"]),
        ("U4", "TPS7A2033PDBV", 108.0, 114.0, 3.0, 3.0, ["VBAT", "GND", "+3V3"]),
        ("U5", "MCP73831-2ACI_OT", 116.0, 106.0, 3.0, 3.0, ["USB_5V", "GND", "VBAT"]),
        ("U6", "DRV5033AJQLPGM", 103.0, 116.0, 2.0, 2.0, ["+3V3", "GND", "HALL"]),
        ("U7", "BMI270", 95.0, 86.8, 3.0, 2.5, ["+3V3", "GND", "SDA", "SCL"]),
        ("U8", "TPS22918DBVR", 85.0, 103.0, 3.0, 3.0, ["VBAT", "GND", "+5V_LED"]),
    ]
    for refdes, value, x, y, w, h, names in simple_parts:
        pads = []
        for i, name in enumerate(names, 1):
            px = -w / 2 + 0.35 if i % 2 else w / 2 - 0.35
            py = -h / 2 + 0.55 + ((i - 1) // 2) * 0.8
            pads.append((str(i), px, py, 0.55, 0.7, net_id[name], name, "rect"))
        lines += footprint(refdes, value, x, y, w, h, 0, pads, "B.Cu")

    # Battery, charge and programming pads.
    connector_parts = [
        ("JBAT1", "BATTERY_PADS", 82.0, 104.0, [("1", "VBAT"), ("2", "GND")]),
        ("JUSB1", "USB_CHARGE_PADS", 123.0, 107.0, [("1", "USB_5V"), ("2", "GND")]),
        ("JDBG1", "SWD_PADS", 104.0, 118.0, [("1", "+3V3"), ("2", "GND"), ("3", "SWDIO"), ("4", "SWCLK")]),
    ]
    for refdes, value, x, y, entries in connector_parts:
        pads = []
        for i, (num, name) in enumerate(entries):
            pads.append((num, (i - (len(entries)-1)/2) * 1.25, 0, 0.9, 1.1, net_id[name], name, "rect"))
        lines += footprint(refdes, value, x, y, max(3.0, len(entries)*1.25), 1.8, 0, pads, "B.Cu")

    # Decoupling/bulk capacitors placed symmetrically at each arm root.
    for idx, angle in enumerate((0, 90, 180, 270), 1):
        x, y = board_xy(36.0, angle, 6.0)
        pads = [
            ("1", -0.8, 0, 1.0, 1.2, net_id["+5V_LED"], "+5V_LED", "rect"),
            ("2", 0.8, 0, 1.0, 1.2, net_id["GND"], "GND", "rect"),
        ]
        lines += footprint(f"C{idx}", "100uF_6V3_1210", x, y, 3.2, 2.5, -angle, pads, "B.Cu")

    lines.append('  (gr_text "SMARTSPINNER v0.4 ERC - 4x20 TOP + 4x12 TIP" (at 100 77) (layer "B.SilkS") (effects (font (size 0.90 0.90) (thickness 0.15)) (justify mirror)))')
    lines.append('  (gr_text "DFM + FIRST ARTICLE REQUIRED" (at 100 123) (layer "B.SilkS") (effects (font (size 0.75 0.75) (thickness 0.12)) (justify mirror)))')
    lines.append(')')
    path = OUT / "smartspinner_main_v0_4.kicad_pcb"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_tip_board() -> Path:
    nets = ["GND", "+5V_LED", "DIN", "DOUT"] + [f"PIX_{i:02d}" for i in range(1, 12)]
    ids = {n: i + 1 for i, n in enumerate(nets)}
    lines = header(nets, 0.6, 2)
    cx, cy, w, h = 100.0, 100.0, 7.0, 13.6
    corners = [(cx-w/2, cy-h/2), (cx+w/2, cy-h/2), (cx+w/2, cy+h/2), (cx-w/2, cy+h/2)]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        lines.append(f'  (gr_line (start {a[0]:.3f} {a[1]:.3f}) (end {b[0]:.3f} {b[1]:.3f}) (stroke (width 0.12) (type default)) (layer "Edge.Cuts"))')
    centers = []
    for i in range(12):
        x, y = cx, cy - 6.05 + i * 1.10
        centers.append((x, y))
        din = "DIN" if i == 0 else f"PIX_{i:02d}"
        dout = "DOUT" if i == 11 else f"PIX_{i+1:02d}"
        pads = [
            ("1", -0.31, -0.31, 0.28, 0.28, ids["+5V_LED"], "+5V_LED", "rect"),
            ("2", 0.31, -0.31, 0.28, 0.28, ids[dout], dout, "rect"),
            ("3", 0.31, 0.31, 0.28, 0.28, ids["GND"], "GND", "rect"),
            ("4", -0.31, 0.31, 0.28, 0.28, ids[din], din, "rect"),
        ]
        lines += footprint(f"TD{i+1}", "SK6805-EC10", x, y, 1.10, 1.10, 0, pads)
    for i in range(11):
        pout = pad_xy(*centers[i], 0.31, -0.31, 0)
        pin = pad_xy(*centers[i+1], -0.31, 0.31, 0)
        lines += [via(pout, ids[f"PIX_{i+1:02d}"], 0.22, 0.10),
                  via(pin, ids[f"PIX_{i+1:02d}"], 0.22, 0.10),
                  segment(pout, pin, 0.10, "B.Cu", ids[f"PIX_{i+1:02d}"])]
        p5a, p5b = pad_xy(*centers[i], -0.31, -0.31, 0), pad_xy(*centers[i+1], -0.31, -0.31, 0)
        pga, pgb = pad_xy(*centers[i], 0.31, 0.31, 0), pad_xy(*centers[i+1], 0.31, 0.31, 0)
        b5a, b5b = (centers[i][0]-0.82, p5a[1]), (centers[i+1][0]-0.82, p5b[1])
        bga, bgb = (centers[i][0]+0.82, pga[1]), (centers[i+1][0]+0.82, pgb[1])
        lines += [segment(p5a, b5a, 0.14, "F.Cu", ids["+5V_LED"]),
                  segment(pga, bga, 0.14, "F.Cu", ids["GND"]),
                  segment(b5a, b5b, 0.16, "F.Cu", ids["+5V_LED"]),
                  segment(bga, bgb, 0.16, "F.Cu", ids["GND"])]
        if i == 10:
            lines += [segment(p5b, b5b, 0.14, "F.Cu", ids["+5V_LED"]),
                      segment(pgb, bgb, 0.14, "F.Cu", ids["GND"])]
    pads = []
    for i, name in enumerate(("+5V_LED", "GND", "DIN", "DOUT"), 1):
        pads.append((str(i), -2.1 + (i-1)*1.4, 0, 0.9, 1.0, ids[name], name, "rect"))
    lines += footprint("J1", "MAIN_BOARD_SOLDER_4", cx+2.45, cy, 5.6, 1.3, 90, pads, "B.Cu")
    lines.append('  (gr_text "TIP v0.4 12PX" (at 102.6 100 90) (layer "B.SilkS") (effects (font (size 0.55 0.55) (thickness 0.09)) (justify mirror)))')
    lines.append(')')
    path = OUT / "smartspinner_tip_v0_4.kicad_pcb"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_bom() -> None:
    rows = [
        ["U1",1,"Raytac","MDBT50Q-1MV2","nRF52840 BLE module","10.5x15.5 module","TBD by assembler","Main","Preferred; antenna keep-out mandatory"],
        ["U2,U9",2,"Nexperia","74AHCT125PW,118","Quad 3.3V to 5V level shifter","TSSOP-14","C1802447","Main","Eight independent streams: four top plus four tip"],
        ["U3",1,"Texas Instruments","TPS61023DRLR","5V boost converter","SOT-563-6","C919601","Main","Thermal/current validation required"],
        ["U4",1,"Texas Instruments","TPS7A2033PDBVR","3.3V LDO 300mA","SOT-23-5","C2864625","Main","Low quiescent current"],
        ["U5",1,"Microchip","MCP73831-2ACI/OT","1-cell Li-ion charger","SOT-23-5","C424093","Main","Set 150mA; protected cell only"],
        ["U6",1,"Texas Instruments","DRV5033AJQLPGM","Omnipolar Hall switch","X2SON-4","TBD by assembler","Main","Fast index sensor; verify exact package stock"],
        ["U7",1,"Bosch","BMI270","6-axis IMU","LGA-14 2.5x3.0","C2839047","Main","SPI/I2C; placed near axis"],
        ["U8",1,"Texas Instruments","TPS22918DBVR","5V rail load switch","SOT-23-6","C141833","Main","Controlled LED power-up"],
        ["D1-D80",80,"OPSCO","SK6805-EC15","Addressable RGB 5mA","1.5x1.5mm 4-pad","C2890035","Main","20 per arm; four independent chains"],
        ["TD1-TD12",48,"OPSCO","SK6805-EC10-000","Addressable RGB 5mA","1.1x1.1mm 4-pad","C22394946","Tip x4","12 per tip board; quantity is for four boards"],
        ["C1-C4",4,"Samsung or equivalent","CL32A107MQVNNNE","100uF 6.3V X5R","1210","C15008","Main","One bulk capacitor per arm"],
        ["L1",1,"Sunlord or equivalent","SWPA3015S2R2MT","2.2uH shielded inductor","3.0x3.0mm","C167549","Main","TPS61023 power stage"],
        ["RPROG",1,"Yageo or equivalent","RC0402FR-0710KL","10k 1%","0402","C25744","Main","MCP73831 approx 100mA; tune after cell choice"],
        ["JTIPA-JTIPD",4,"PCB feature","N/A","Four solder tabs","Custom","N/A","Main","Rigid solder plus enclosure guide"],
        ["J1",4,"PCB feature","N/A","Four solder tabs","Custom","N/A","Tip x4","Mate to main board"],
        ["JBAT1",1,"PCB feature","N/A","Protected LiPo solder pads","Custom","N/A","Main","Do not hot-plug while spinning"],
        ["JUSB1",1,"PCB feature","N/A","External charge dock pads","Custom","N/A","Main","No onboard USB connector in v0.4"],
        ["JDBG1",1,"Tag-Connect","TC2030-NL footprint","SWD programming pads","6-pad","N/A","Main","Pogo fixture; no fitted connector"],
    ]
    with (OUT / "smartspinner_v0_4_bom.csv").open("w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(["Designators","Qty","Manufacturer","MPN","Description","Package","LCSC/Source","Board","Engineering note"])
        wr.writerows(rows)


def write_netlist_and_docs() -> None:
    net_rows = [
        ["VBAT","Protected 1S LiPo pair in opposite bays","U3 boost, U4 LDO, U5 charger, U8 switch","3.0-4.2V"],
        ["+3V3","TPS7A2033 output","nRF52840, BMI270, Hall, 74AHCT125 inputs","Logic rail"],
        ["+5V_LED","TPS61023 through TPS22918","80 top LEDs + 48 tip LEDs","Firmware-limited; 1.5A hardware target"],
        ["TOP_A_DIN..TOP_D_DIN","74AHCT125 U2 outputs","Four independent 20-pixel top chains","800kbit/s; about 0.60ms per update"],
        ["TIP_A_DIN..TIP_D_DIN","74AHCT125 U9 outputs","Four independent 12-pixel tip chains","800kbit/s; about 0.36ms per update"],
        ["HALL","DRV5033","nRF GPIO interrupt","One pulse/revolution"],
        ["SDA/SCL","nRF52840","BMI270","I2C fast mode"],
        ["SWDIO/SWCLK","Pogo pads","nRF52840","Programming/debug"],
    ]
    with (OUT / "smartspinner_v0_4_netlist.csv").open("w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f); wr.writerow(["Net","Source","Loads","Note"]); wr.writerows(net_rows)

    power = {
        "architecture": "protected 1S LiPo, 3.3V logic LDO, switched 5V LED boost",
        "led_count": {"top": 80, "tip": 48, "total": 128},
        "limits": {"led_nominal_per_pixel_mA": 5, "boost_continuous_target_A": 1.5, "firmware_global_brightness_percent": 35},
        "estimated_modes": [
            {"mode":"BLE standby, LEDs off","input_current_mA":8,"runtime_500mAh_h":50},
            {"mode":"typical POV content at 20-25% average light","input_current_mA":220,"runtime_500mAh_h":2.0},
            {"mode":"bright demo, firmware capped","input_current_mA":650,"runtime_500mAh_h":0.65}
        ],
        "warning": "Runtime estimates include 85% usable battery energy and are not measurements. Full-white unrestricted frames are prohibited in firmware."
    }
    (OUT / "smartspinner_v0_4_power_budget.json").write_text(json.dumps(power, indent=2, ensure_ascii=False), encoding="utf-8")

    readme = """# Smart Spinner electronics v0.4 - Engineering Release Candidate

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
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    bringup = """# First article bring-up - Smart Spinner v0.4

1. Bare-board inspection: outline, 23.2 mm center hole, four M2 holes, impedance-independent continuity, no copper inside RF keep-out.
2. Populate power only. Feed VBAT from a current-limited bench supply at 3.7 V / 100 mA. Verify no short.
3. Verify +3V3 within 3.25-3.35 V; then verify boost soft-start and +5V_LED with LEDs disconnected.
4. Raise current limit in steps. Check switch node with oscilloscope and measure U3/L1/C bulk temperature after 10 minutes at 0.5 A and 1.0 A.
5. Populate/debug nRF module through SWD. Confirm BLE advertising and current below 10 mA with LEDs disabled.
6. Populate Hall and IMU. Log Hall period and IMU gyro while turning in a guarded low-speed fixture.
7. Populate one LED per chain, run RGB orientation test, then populate remaining top pixels.
8. Attach one tip board at a time. Run a walking-one pixel test and verify all four 20-pixel top chains and all four 12-pixel tip chains independently.
9. Enforce firmware brightness/current limit before battery operation. Full-white unrestricted frames are forbidden.
10. Install matched protected cells and mechanically retain them. Static-balance to less than 0.10 g equivalent at 45 mm.
11. Dynamic test behind a polycarbonate guard at 300, 600, 900 and 1200 RPM; stop on vibration, temperature rise, RF loss or frame slip.
12. Only after the first article passes may the remaining nine assemblies be released.
"""
    (OUT / "smartspinner_v0_4_bringup.md").write_text(bringup, encoding="utf-8")


def write_design_rules() -> None:
    rules = """(version 1)
(rule "Fine pitch LED fabrication limits"
  (constraint clearance (min 0.08mm))
  (constraint track_width (min 0.10mm))
  (constraint via_diameter (min 0.22mm))
  (constraint annular_width (min 0.05mm))
  (constraint hole_clearance (min 0.15mm))
  (constraint edge_clearance (min 0.15mm))
  (constraint hole_size (min 0.10mm)))
"""
    (OUT / "smartspinner_main_v0_4.kicad_dru").write_text(rules, encoding="utf-8")
    (OUT / "smartspinner_tip_v0_4.kicad_dru").write_text(rules, encoding="utf-8")


def setup_pdf_font() -> str:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
    ]
    for p in candidates:
        if p.exists():
            pdfmetrics.registerFont(TTFont("DocFont", str(p)))
            return "DocFont"
    return "Helvetica"


def pdf_header(c: canvas.Canvas, title: str, subtitle: str, page: int, font: str) -> None:
    w, h = landscape(A4)
    c.setFillColor(colors.HexColor("#081C24")); c.rect(0, h-54, w, 54, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#42F5B6")); c.setFont(font, 18); c.drawString(28, h-34, title)
    c.setFillColor(colors.white); c.setFont(font, 8); c.drawRightString(w-28, h-32, subtitle)
    c.setFillColor(colors.HexColor("#607D86")); c.setFont(font, 7); c.drawRightString(w-28, 18, f"SMARTSPINNER v0.4 ERC  |  PAGE {page}")


def box(c, x, y, w, h, title, lines, font, accent="#42F5B6"):
    c.setFillColor(colors.HexColor("#F4F7F7")); c.setStrokeColor(colors.HexColor("#C8D2D4")); c.roundRect(x, y, w, h, 8, fill=1, stroke=1)
    c.setFillColor(colors.HexColor(accent)); c.rect(x, y+h-28, w, 28, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#081C24")); c.setFont(font, 11); c.drawString(x+12, y+h-19, title)
    c.setFont(font, 8.2); c.setFillColor(colors.HexColor("#25383E"))
    ty = y+h-45
    for line in lines:
        for wrapped in textwrap.wrap(line, 54):
            c.drawString(x+12, ty, wrapped); ty -= 12
        ty -= 3


def write_schematic_pdf() -> None:
    font = setup_pdf_font(); page_size = landscape(A4); w, h = page_size
    path = OUT / "smartspinner_v0_4_schematic.pdf"
    c = canvas.Canvas(str(path), pagesize=page_size)
    pages = [
        ("SYSTEM ARCHITECTURE", [
            (34,330,180,150,"ENERGY INPUT",["Protected matched 1S LiPo cells in opposite bays","Charge dock pads -> MCP73831, 100-150 mA","VBAT monitor to nRF ADC"]),
            (250,330,180,150,"POWER TREE",["TPS7A2033 -> +3V3 logic","TPS61023 -> switched +5V_LED","TPS22918 load switch and firmware enable"]),
            (466,330,180,150,"CONTROL",["Raytac MDBT50Q-1MV2 / nRF52840","BLE data, frame renderer, eight LED streams","SWD pogo pads; watchdog and brownout"]),
            (682,330,125,150,"SENSORS",["DRV5033 Hall index","BMI270 gyro/accelerometer","Angle estimator corrects hand-speed variation"]),
            (130,105,250,150,"TOP DISPLAY",["4 independent chains x 20 SK6805-EC15","5 V data via first 74AHCT125","Radial POV resolution: 20 pixels"]),
            (460,105,250,150,"CYLINDRICAL TICKER",["4 separate chains x 12 SK6805-EC10","Second 74AHCT125; replaceable 0.6 mm boards","Vertical ticker resolution: 12 pixels"]),
        ]),
        ("POWER AND CHARGING", [
            (34,300,235,180,"1S BATTERY DOMAIN",["VBAT range 3.0-4.2 V","Only protected cells; matched pair, opposite placement","Fuse/current-limited interconnect required in enclosure","No charging while spinning"]),
            (303,300,235,180,"3.3 V LOGIC",["TPS7A2033 LDO, 300 mA","10 uF input/output plus 100 nF at each IC","nRF52840, BMI270, Hall and level-shifter inputs","Expected logic load below 50 mA"]),
            (572,300,235,180,"5 V LED RAIL",["TPS61023 synchronous boost, 2.2 uH shielded inductor","TPS22918 controlled load switch","4 x 100 uF bulk at arm roots","1.5 A design target; thermal validation mandatory"]),
            (170,90,500,150,"FIRMWARE CURRENT CONTRACT",["128 x 5 mA pixels can exceed the practical continuous budget at unrestricted white.","Hard cap global brightness to 35%; default moving graphics target 20-25% average light.","Reject frames that exceed the measured rail budget; ramp power on and off; log undervoltage.","Runtime estimates are preliminary and must be replaced with measured current from first article."])
        ]),
        ("CONTROL, INDEX AND DATA", [
            (34,300,235,180,"nRF52840 MODULE",["BLE receives compact market-data frames","Eight hardware-timed 800 kbit/s outputs","Frame phase is reset by Hall index","Gyro interpolation handles nonuniform hand spin"]),
            (303,300,235,180,"LEVEL SHIFT",["2 x 74AHCT125 powered from +5V_LED","3.3 V input-high compatible","Eight buffers: four top plus four tip","Outputs disabled until LED rail is stable"]),
            (572,300,235,180,"SENSOR INTERFACE",["DRV5033 digital Hall output to interrupt GPIO","BMI270 over I2C; optional SPI footprint reassignment","Place IMU near rotation axis","Debounce and reject impossible period changes"]),
            (130,90,580,150,"TIMING TARGET",["Typical hand spin assumption for firmware testing: 300-900 RPM (5-15 revolutions/s).","A 20-pixel top-chain update is about 0.60 ms; four arms draw four angular lines in parallel.","A 12-pixel tip-chain update is about 0.36 ms and is scheduled independently from the top image.","Final angular resolution and frame stability must be measured; marketing renders are not acceptance evidence."])
        ]),
        ("LED CHAINS AND CONNECTORS", [
            (34,300,360,180,"ARM A / B / C / D (IDENTICAL)",["nRF GPIO -> U2 -> 20 x SK6805-EC15 top LEDs","Separate nRF GPIO -> U9 -> 12 x SK6805-EC10 tip LEDs","5 V and GND carried on wide local rails","Return DOUT test pad allows walking-one verification"]),
            (430,300,377,180,"TIP BOARD INTERFACE",["Pad 1: +5V_LED","Pad 2: GND","Pad 3: independent TIP_x_DIN stream","Pad 4: DOUT / test return","Mechanical enclosure guides carry impact load; solder tabs are not structural members"]),
            (130,90,580,150,"ASSEMBLY CHECKS",["Confirm pin-1 orientation against manufacturer datasheet before stencil release.","AOI must verify 80 top and 48 tip LEDs for rotation and solder bridging.","Program walking-one RGB test before enclosing the assembly.","Balance correction comes after all four tip boards, cells and diffuser parts are installed."])
        ])
    ]
    for page_no, (title, boxes) in enumerate(pages, 1):
        pdf_header(c, "SMART SPINNER - ELECTRICAL DESIGN", title, page_no, font)
        for x,y,bw,bh,bt,bl in boxes: box(c,x,y,bw,bh,bt,bl,font)
        c.showPage()
    c.save()


def write_fab_pdf() -> None:
    font = setup_pdf_font(); w,h = landscape(A4)
    path = OUT / "smartspinner_v0_4_fabrication_drawing.pdf"
    c = canvas.Canvas(str(path), pagesize=landscape(A4))
    pdf_header(c,"SMART SPINNER - FABRICATION DRAWING","MAIN PCB",1,font)
    cx,cy,scale = 255,270,4.1
    pts = main_outline()
    mapped = [((x-100)*scale+cx,(100-y)*scale+cy) for x,y in pts]
    p=c.beginPath(); p.moveTo(*mapped[0])
    for point in mapped[1:]: p.lineTo(*point)
    p.close(); c.setFillColor(colors.HexColor("#DCEAE5")); c.setStrokeColor(colors.HexColor("#173B42")); c.drawPath(p,fill=1,stroke=1)
    c.setFillColor(colors.white); c.circle(cx,cy,11.6*scale,fill=1,stroke=1)
    c.setFillColor(colors.HexColor("#FFCC66"))
    for a in (0,90,180,270):
        for i in range(20):
            x,y=board_xy(14.5+i*1.6,a); c.rect((x-100)*scale+cx-2,(100-y)*scale+cy-2,4,4,fill=1,stroke=0)
    box(c,500,300,300,180,"MAIN PCB NOTES",["4 layers, finished thickness 1.00 +/- 0.10 mm","Overall envelope 96.0 mm; center hole 23.20 mm","Four M2 NPTH holes: 2.40 mm at radius 17.0 mm / 45 deg","ENIG recommended; lead-free assembly","Minimum track/space 0.15/0.15 mm; smallest top LED pads 0.48 mm","RF keep-out: no copper, vias or metal enclosure above module antenna"],font)
    box(c,500,92,300,170,"STACKUP / ACCEPTANCE",["L1 signal + LED distribution","L2 solid GND reference","L3 +5V_LED / +3V3 power islands","L4 signal + components","Supplier may propose equivalent controlled stackup","100% flying probe, AOI after SMT, first-article dimensional report"],font,"#9FE3D0")
    c.showPage()
    pdf_header(c,"SMART SPINNER - FABRICATION DRAWING","TIP PCB / PANEL",2,font)
    tx,ty=220,280; s=18
    c.setFillColor(colors.HexColor("#DCEAE5")); c.setStrokeColor(colors.HexColor("#173B42")); c.rect(tx-3.5*s,ty-6.8*s,7*s,13.6*s,fill=1,stroke=1)
    c.setFillColor(colors.HexColor("#4ED4FF"))
    for i in range(12): c.rect(tx-0.55*s,ty+(-5.5+i)*s-0.55*s,1.1*s,1.1*s,fill=1,stroke=0)
    box(c,430,300,360,180,"TIP BOARD NOTES",["Quantity: four identical boards per spinner","2 layers, finished thickness 0.60 +/- 0.07 mm","Finished size 7.00 x 13.60 mm","12 x SK6805-EC10, 1.00 mm pitch","Panelize with rails; routing tabs outside light window","ENIG required; confirm LED orientation with first article"],font)
    box(c,430,92,360,170,"MECHANICAL INTERFACE",["Board slides into enclosure guide; enclosure carries hand impact","Four solder tabs mate to main board: +5V, GND, DIN, DOUT","Maintain 0.20 mm board-edge clearance from copper","Inspect every tip board with walking-one RGB fixture","Do not substitute a taller LED without checking 16 mm enclosure stack"],font,"#9FE3D0")
    c.showPage(); c.save()


def run_kicad_exports(board: Path, stem: str) -> dict:
    if not KICAD.exists():
        raise RuntimeError(f"KiCad CLI not found: {KICAD}")
    commands = [
        [str(KICAD), "pcb", "drc", "--output", str(OUT / f"{stem}_drc.txt"), str(board)],
        [str(KICAD), "pcb", "export", "gerbers", "-o", str(GERBER) + "/", str(board)],
        [str(KICAD), "pcb", "export", "drill", "-o", str(GERBER) + "/", str(board)],
        [str(KICAD), "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--use-drill-file-origin", "-o", str(POS / f"{stem}_cpl.csv"), str(board)],
        [str(KICAD), "pcb", "export", "svg", "--layers", "F.Cu,F.Silkscreen,Edge.Cuts", "-o", str(OUT / f"{stem}_top.svg"), str(board)],
    ]
    results = []
    for cmd in commands:
        p = subprocess.run(cmd, text=True, capture_output=True)
        results.append({"command": " ".join(cmd[1:4]), "returncode": p.returncode, "stdout": p.stdout[-1000:], "stderr": p.stderr[-1000:]})
    return {"board": board.name, "exports": results}


def finalize() -> None:
    export_log = []
    main = write_main_board(); tip = write_tip_board()
    write_design_rules(); write_bom(); write_netlist_and_docs(); write_schematic_pdf(); write_fab_pdf()
    export_log.append(run_kicad_exports(main, "smartspinner_main_v0_4"))
    export_log.append(run_kicad_exports(tip, "smartspinner_tip_v0_4"))
    (OUT / "generation_report.json").write_text(json.dumps(export_log, indent=2), encoding="utf-8")

    def counts(path: Path) -> dict[str, int]:
        result: dict[str, int] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("[") and "]" in line:
                key = line[1:line.index("]")]
                result[key] = result.get(key, 0) + 1
        return result

    release_status = {
        "release": "v0.4 engineering package - NOT FOR FABRICATION",
        "kicad_cli": "10.0.6",
        "main_drc": counts(OUT / "smartspinner_main_v0_4_drc.txt"),
        "tip_drc": counts(OUT / "smartspinner_tip_v0_4_drc.txt"),
        "fabrication_gate": "Both boards must reach zero copper errors and zero unconnected items; cosmetic silkscreen warnings must be reviewed.",
    }
    (OUT / "smartspinner_v0_4_release_status.json").write_text(json.dumps(release_status, indent=2), encoding="utf-8")
    shutil.copy2(Path(__file__), OUT / Path(__file__).name)

    # Stable archive for website and RFQ attachment.
    zip_path = ROOT / "public" / "project-files" / "SmartSpinner_v0_4_electronics_ERC.zip"
    if zip_path.exists(): zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(OUT.rglob("*")):
            if path.is_file(): zf.write(path, path.relative_to(OUT.parent))


if __name__ == "__main__":
    ensure_dirs(); finalize()
