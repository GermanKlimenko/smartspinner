#!/usr/bin/env python3
"""Parametric mechanical envelope for Ticker Spinner v0.3 (12-pixel tip).

All dimensions are millimetres.  This is a mechanical/PCB-envelope prototype,
not a production-ready electronics design.
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import cadquery as cq
import ezdxf
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from cadquery import exporters
from matplotlib.patches import Circle, Polygon, Rectangle
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)


P = {
    "overall_diameter": 100.0,
    "assembled_thickness": 16.0,
    "half_height": 8.0,
    "hub_radius": 19.0,
    "arm_root_center": 17.0,
    "arm_root_radius": 9.5,
    "arm_tip_center": 42.5,
    "arm_tip_radius": 7.5,
    "shell_floor": 1.6,
    "shell_roof": 1.5,
    "bearing_od_nominal": 22.0,
    "bearing_seat_diameter": 21.85,
    "bearing_bore_diameter": 19.5,
    "bearing_width": 7.0,
    "bearing_z_bottom": 4.5,
    "pcb_thickness": 1.0,
    "pcb_z_bottom": 6.5,
    "pcb_tip_radius": 48.0,
    "pcb_center_hole": 23.2,
    "led_count_top_per_arm": 20,
    "led_radial_start": 14.8,
    "led_pitch": 1.6,
    "top_window_width": 2.4,
    "top_window_r0": 13.4,
    "top_window_r1": 46.3,
    "side_led_count_per_arm": 12,
    "side_led_z_start": 2.225,
    "side_led_z_pitch": 1.05,
    "side_window_width": 1.30,
    "side_window_height": 0.78,
    "tip_board_width": 7.0,
    "tip_board_height": 13.6,
    "tip_board_thickness": 0.6,
    "screw_radius": 30.0,
    "screw_tangent_offset": 5.3,
    "screw_clearance_diameter": 2.3,
    "screw_pilot_diameter": 1.7,
    "screw_boss_diameter": 5.0,
    "battery_length": 20.0,
    "battery_width": 11.5,
    "battery_height": 3.2,
    "battery_center_radius": 27.0,
    "diffuser_clearance": 0.20,
}


def polar(r: float, deg: float, tangential: float = 0.0) -> tuple[float, float]:
    a = math.radians(deg)
    return (r * math.cos(a) - tangential * math.sin(a),
            r * math.sin(a) + tangential * math.cos(a))


def arm_prism(height: float, z0: float = 0.0, inset: float = 0.0) -> cq.Workplane:
    rr = P["arm_root_radius"] - inset
    tr = P["arm_tip_radius"] - inset
    root = (cq.Workplane("XY", origin=(0, 0, z0))
            .center(P["arm_root_center"], 0).circle(rr).extrude(height))
    tip = (cq.Workplane("XY", origin=(0, 0, z0))
           .center(P["arm_tip_center"], 0).circle(tr).extrude(height))
    bridge = (cq.Workplane("XY", origin=(0, 0, z0))
              .polyline([(P["arm_root_center"], -rr),
                         (P["arm_tip_center"], -tr),
                         (P["arm_tip_center"], tr),
                         (P["arm_root_center"], rr)])
              .close().extrude(height))
    return root.union(bridge).union(tip)


def rotor_body(height: float, z0: float = 0.0, inset: float = 0.0,
             hub_radius: float | None = None) -> cq.Workplane:
    hr = P["hub_radius"] - inset if hub_radius is None else hub_radius
    body = cq.Workplane("XY", origin=(0, 0, z0)).circle(hr).extrude(height)
    arm0 = arm_prism(height, z0, inset)
    for angle in (0, 90, 180, 270):
        body = body.union(arm0.rotate((0, 0, 0), (0, 0, 1), angle))
    return body


def rounded_slot(length: float, width: float, height: float, z0: float) -> cq.Workplane:
    r = width / 2
    x0 = -length / 2 + r
    x1 = length / 2 - r
    left = cq.Workplane("XY", origin=(x0, 0, z0)).circle(r).extrude(height)
    right = cq.Workplane("XY", origin=(x1, 0, z0)).circle(r).extrude(height)
    bridge = cq.Workplane("XY", origin=(0, 0, z0)).rect(x1 - x0, width).extrude(height)
    return left.union(bridge).union(right)


def screw_positions() -> list[tuple[float, float]]:
    return [polar(P["screw_radius"], a, P["screw_tangent_offset"]) for a in (0, 90, 180, 270)]


def make_bottom() -> cq.Workplane:
    h = P["half_height"]
    bottom = rotor_body(h)

    # General electronics cavity; a solid central annulus remains around 608.
    cavity = rotor_body(h - P["shell_floor"] + 0.2,
                      P["shell_floor"], inset=1.55, hub_radius=16.4)
    keep = cq.Workplane("XY", origin=(0, 0, P["shell_floor"])).circle(13.4).extrude(h)
    cavity = cavity.cut(keep)
    bottom = bottom.cut(cavity)

    # Four equal universal bays. Populate opposite pairs to preserve balance.
    for angle in (0, 90, 180, 270):
        x, y = polar(P["battery_center_radius"], angle)
        pocket = (cq.Workplane("XY", origin=(x, y, P["shell_floor"]))
                  .rect(P["battery_length"] + 0.6, P["battery_width"] + 0.6)
                  .extrude(P["battery_height"] + 0.25)
                  .rotate((x, y, 0), (x, y, 1), angle))
        bottom = bottom.cut(pocket)

    # 608 pocket: lower printed lip is 3 mm thick, bearing seat continues to seam.
    lower_bore = (cq.Workplane("XY").circle(P["bearing_bore_diameter"] / 2)
                  .extrude(P["bearing_z_bottom"]))
    bearing_seat = (cq.Workplane("XY", origin=(0, 0, P["bearing_z_bottom"]))
                    .circle(P["bearing_seat_diameter"] / 2)
                    .extrude(h - P["bearing_z_bottom"] + 0.1))
    bottom = bottom.cut(lower_bore).cut(bearing_seat)

    # Four self-tapping screw bosses and pilot holes.
    for x, y in screw_positions():
        boss = cq.Workplane("XY", origin=(x, y, P["shell_floor"])).circle(
            P["screw_boss_diameter"] / 2).extrude(h - P["shell_floor"])
        pilot = cq.Workplane("XY", origin=(x, y, P["shell_floor"] + 0.6)).circle(
            P["screw_pilot_diameter"] / 2).extrude(h)
        bottom = bottom.union(boss).cut(pilot)

    # Lower windows of the vertical twelve-pixel tip column.
    z_centers = [P["side_led_z_start"] + i * P["side_led_z_pitch"]
                 for i in range(int(P["side_led_count_per_arm"]))]
    for angle in (0, 90, 180, 270):
        for zc in [z for z in z_centers if z < h]:
            slot = (cq.Workplane("XY", origin=(48.2, 0, zc - P["side_window_height"] / 2))
                    .rect(4.4, P["side_window_width"]).extrude(P["side_window_height"])
                    .rotate((0, 0, 0), (0, 0, 1), angle))
            bottom = bottom.cut(slot)

    # Paired internal ribs capture the vertical daughterboard mechanically;
    # solder joints or an FPC are not load-bearing.
    rail0a = (cq.Workplane("XY", origin=(46.0, -3.8, P["shell_floor"]))
              .rect(1.2, 0.9).extrude(h - P["shell_floor"] - 0.25))
    rail0b = (cq.Workplane("XY", origin=(46.0, 3.8, P["shell_floor"]))
              .rect(1.2, 0.9).extrude(h - P["shell_floor"] - 0.25))
    for angle in (0, 90, 180, 270):
        bottom = bottom.union(rail0a.rotate((0, 0, 0), (0, 0, 1), angle))
        bottom = bottom.union(rail0b.rotate((0, 0, 0), (0, 0, 1), angle))

    return bottom


def make_top_assembled() -> cq.Workplane:
    z0 = P["half_height"]
    h = P["half_height"]
    top = rotor_body(h, z0)

    cavity_h = h - P["shell_roof"]
    cavity = rotor_body(cavity_h + 0.1, z0 - 0.05, inset=1.55, hub_radius=16.4)
    keep = cq.Workplane("XY", origin=(0, 0, z0 - 0.1)).circle(13.4).extrude(cavity_h + 0.2)
    cavity = cavity.cut(keep)
    top = top.cut(cavity)

    # Upper half of bearing seat and finger access bore.
    bearing_top = P["bearing_z_bottom"] + P["bearing_width"]
    seat = (cq.Workplane("XY", origin=(0, 0, z0 - 0.05))
            .circle(P["bearing_seat_diameter"] / 2)
            .extrude(bearing_top - z0 + 0.05))
    bore = (cq.Workplane("XY", origin=(0, 0, bearing_top))
            .circle(P["bearing_bore_diameter"] / 2)
            .extrude(P["assembled_thickness"] - bearing_top + 0.1))
    top = top.cut(seat).cut(bore)

    # Continuous serviceable windows for 20 LEDs per arm.
    window_len = P["top_window_r1"] - P["top_window_r0"]
    window_mid = (P["top_window_r1"] + P["top_window_r0"]) / 2
    base_window = rounded_slot(window_len, P["top_window_width"], 2.0,
                               P["assembled_thickness"] - P["shell_roof"] - 0.1)
    base_window = base_window.translate((window_mid, 0, 0))
    for angle in (0, 90, 180, 270):
        top = top.cut(base_window.rotate((0, 0, 0), (0, 0, 1), angle))

    # Upper windows of the vertical twelve-pixel tip column.
    z_centers = [P["side_led_z_start"] + i * P["side_led_z_pitch"]
                 for i in range(int(P["side_led_count_per_arm"]))]
    for angle in (0, 90, 180, 270):
        for zc in [z for z in z_centers if z > z0]:
            slot = (cq.Workplane("XY", origin=(48.2, 0, zc - P["side_window_height"] / 2))
                    .rect(4.4, P["side_window_width"]).extrude(P["side_window_height"])
                    .rotate((0, 0, 0), (0, 0, 1), angle))
            top = top.cut(slot)

    rail0a = (cq.Workplane("XY", origin=(46.0, -3.8, z0 + 0.10))
              .rect(1.2, 0.9).extrude(h - P["shell_roof"] + 0.10))
    rail0b = (cq.Workplane("XY", origin=(46.0, 3.8, z0 + 0.10))
              .rect(1.2, 0.9).extrude(h - P["shell_roof"] + 0.10))
    for angle in (0, 90, 180, 270):
        top = top.union(rail0a.rotate((0, 0, 0), (0, 0, 1), angle))
        top = top.union(rail0b.rotate((0, 0, 0), (0, 0, 1), angle))

    # M2 clearance and shallow counterbores.
    for x, y in screw_positions():
        clear = (cq.Workplane("XY", origin=(x, y, z0 - 0.1))
                 .circle(P["screw_clearance_diameter"] / 2).extrude(h + 0.2))
        cbore = (cq.Workplane("XY", origin=(x, y, P["assembled_thickness"] - 1.1))
                 .circle(2.15).extrude(1.2))
        top = top.cut(clear).cut(cbore)

    return top


def make_diffusers_assembled() -> cq.Workplane:
    length = (P["top_window_r1"] - P["top_window_r0"] -
              2 * P["diffuser_clearance"])
    width = P["top_window_width"] - 2 * P["diffuser_clearance"]
    mid = (P["top_window_r1"] + P["top_window_r0"]) / 2
    strip = rounded_slot(length, width, 1.25, P["assembled_thickness"] - 1.3).translate((mid, 0, 0))
    result = None
    for angle in (0, 90, 180, 270):
        part = strip.rotate((0, 0, 0), (0, 0, 1), angle)
        result = part if result is None else result.union(part)
    return result


def make_pcb() -> cq.Workplane:
    # Mechanical envelope: 2 mm radial shell clearance, 23.2 mm center clearance.
    board = rotor_body(P["pcb_thickness"], P["pcb_z_bottom"], inset=2.0, hub_radius=17.0)
    center = (cq.Workplane("XY", origin=(0, 0, P["pcb_z_bottom"] - 0.1))
              .circle(P["pcb_center_hole"] / 2).extrude(P["pcb_thickness"] + 0.2))
    board = board.cut(center)
    for x, y in screw_positions():
        hole = (cq.Workplane("XY", origin=(x, y, P["pcb_z_bottom"] - 0.1))
                .circle(1.25).extrude(P["pcb_thickness"] + 0.2))
        board = board.cut(hole)
    return board


def make_tip_boards_assembled() -> cq.Workplane:
    board0 = (cq.Workplane("YZ", origin=(46.2, 0, P["assembled_thickness"] / 2))
              .rect(P["tip_board_width"], P["tip_board_height"])
              .extrude(-P["tip_board_thickness"]))
    result = None
    for angle in (0, 90, 180, 270):
        part = board0.rotate((0, 0, 0), (0, 0, 1), angle)
        result = part if result is None else result.union(part)
    return result


def make_tip_board_flat() -> cq.Workplane:
    return (cq.Workplane("XY").rect(P["tip_board_width"], P["tip_board_height"])
            .extrude(P["tip_board_thickness"]))


def make_finger_cap(top: bool) -> cq.Workplane:
    """Stationary 608 finger cap with a short inner-race locating stem."""
    if top:
        disc = (cq.Workplane("XY", origin=(0, 0, P["assembled_thickness"]))
                .circle(11.0).extrude(2.8))
        stem_z = P["bearing_z_bottom"] + P["bearing_width"] - 0.3
        stem = (cq.Workplane("XY", origin=(0, 0, stem_z))
                .circle(3.9).extrude(P["assembled_thickness"] - stem_z))
        return disc.union(stem)
    disc = cq.Workplane("XY", origin=(0, 0, -2.8)).circle(11.0).extrude(2.8)
    stem = cq.Workplane("XY", origin=(0, 0, 0)).circle(3.9).extrude(P["bearing_z_bottom"] + 0.3)
    pocket = (cq.Workplane("XY", origin=(9.0, 0, -2.9))
              .circle(1.55).extrude(1.7))
    return disc.union(stem).cut(pocket)


def export_cad(bottom: cq.Workplane, top_a: cq.Workplane,
               diff_a: cq.Workplane, pcb: cq.Workplane,
               tip_boards: cq.Workplane) -> None:
    # Print orientation: both large exterior faces on the build plate.
    top_local = top_a.translate((0, 0, -P["half_height"]))
    top_print = (top_local.rotate((0, 0, 0), (1, 0, 0), 180)
                 .translate((0, 0, P["half_height"])))
    diff_print = diff_a.translate((0, 0, -(P["assembled_thickness"] - 1.3)))

    parts = {
        "ticker_spinner_v0_3_bottom": bottom,
        "ticker_spinner_v0_3_top": top_print,
        "ticker_spinner_v0_3_diffusers": diff_print,
        "ticker_spinner_v0_3_pcb_envelope": pcb.translate((0, 0, -P["pcb_z_bottom"])),
        "ticker_spinner_v0_3_tip_led_board_envelope": make_tip_board_flat(),
        "ticker_spinner_v0_3_finger_cap_top": make_finger_cap(True).translate((0, 0, -P["assembled_thickness"])),
        "ticker_spinner_v0_3_finger_cap_bottom": make_finger_cap(False).translate((0, 0, 2.8)),
    }
    for name, obj in parts.items():
        exporters.export(obj, str(OUT / f"{name}.stl"), tolerance=0.04, angularTolerance=0.08)
        exporters.export(obj, str(OUT / f"{name}.step"))

    assembly = cq.Compound.makeCompound([
        bottom.val(), pcb.val(), top_a.val(), diff_a.val(), tip_boards.val(),
        make_finger_cap(True).val(), make_finger_cap(False).val()
    ])
    exporters.export(assembly, str(OUT / "ticker_spinner_v0_3_assembly.step"))


def sample_arm_boundary(inset: float = 0.0, n: int = 48) -> list[tuple[float, float]]:
    """A conservative sampled capsule-like boundary for PCB/DXF documentation."""
    x0, r0 = P["arm_root_center"], P["arm_root_radius"] - inset
    x1, r1 = P["arm_tip_center"], P["arm_tip_radius"] - inset
    # Convex hull of two sampled circles is enough for the tangent outline.
    pts = []
    for x, r in ((x0, r0), (x1, r1)):
        for a in np.linspace(0, 2 * math.pi, n, endpoint=False):
            pts.append((x + r * math.cos(a), r * math.sin(a)))
    from scipy.spatial import ConvexHull
    hull = ConvexHull(np.array(pts))
    return [pts[i] for i in hull.vertices]


def pcb_outline_points() -> list[tuple[float, float]]:
    # Use OCC's exact outer wire discretization for the manufacturing outline.
    flat = make_pcb().translate((0, 0, -P["pcb_z_bottom"]))
    face = max(flat.faces().vals(), key=lambda f: f.Area())
    wires = face.Wires()
    outer = max(wires, key=lambda w: abs(cq.Face.makeFromWires(w).Area()))
    return _ordered_wire_points(outer, 0.20)


def _ordered_wire_points(wire: cq.Wire, step: float = 0.18) -> list[tuple[float, float]]:
    """Discretize and connect OCC edges by nearest endpoints."""
    chains = []
    for edge in wire.Edges():
        samples = max(3, int(math.ceil(edge.Length() / step)))
        chain = []
        for t in np.linspace(0, 1, samples, endpoint=True):
            v = edge.positionAt(float(t))
            chain.append((v.x, v.y))
        chains.append(chain)
    result = chains.pop(0)
    while chains:
        end = result[-1]
        best_i, reverse, best_d = 0, False, float("inf")
        for i, chain in enumerate(chains):
            d0, d1 = math.dist(end, chain[0]), math.dist(end, chain[-1])
            if d0 < best_d: best_i, reverse, best_d = i, False, d0
            if d1 < best_d: best_i, reverse, best_d = i, True, d1
        chain = chains.pop(best_i)
        if reverse: chain.reverse()
        result.extend(chain[1:])
    return result


def export_dxf() -> None:
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    for name, color in [
        ("EDGE.CUTS", 7), ("NPTH", 1), ("LED_TOP", 3), ("LED_SIDE", 4),
        ("COURTYARD", 6), ("PLACEMENT_ZONES", 2), ("TIP_INTERFACE", 4),
        ("BALANCE", 5), ("NOTES", 7)
    ]:
        doc.layers.add(name, color=color)
    m = doc.modelspace()

    outline = pcb_outline_points()
    m.add_lwpolyline(outline, close=True, dxfattribs={"layer": "EDGE.CUTS"})
    m.add_circle((0, 0), P["pcb_center_hole"] / 2, dxfattribs={"layer": "NPTH"})
    for x, y in screw_positions():
        m.add_circle((x, y), 1.25, dxfattribs={"layer": "NPTH"})

    # Top LED packages, 1.5 x 1.5 mm courtyard, 20 per arm (1313 class).
    for ai, angle in enumerate((0, 90, 180, 270), start=1):
        for i in range(int(P["led_count_top_per_arm"])):
            r = P["led_radial_start"] + i * P["led_pitch"]
            x, y = polar(r, angle)
            m.add_lwpolyline([
                polar(r - .75, angle, -.75), polar(r + .75, angle, -.75),
                polar(r + .75, angle, .75), polar(r - .75, angle, .75)
            ], close=True, dxfattribs={"layer": "LED_TOP"})
            m.add_text(f"D{ai}_{i+1:02d}", height=0.65,
                       dxfattribs={"layer": "NOTES", "insert": (x, y)})

    # Interface/castellated-pad envelope for a vertical LED daughterboard.
    for angle in (0, 90, 180, 270):
        corners = [polar(r, angle, t) for r, t in
                   [(44.8, -3.5), (47.2, -3.5), (47.2, 3.5), (44.8, 3.5)]]
        m.add_lwpolyline(corners, close=True, dxfattribs={"layer": "TIP_INTERFACE"})

    # Symmetric battery courtyards under PCB.
    for angle in (0, 90, 180, 270):
        corners = [polar(P["battery_center_radius"] + dx, angle, dy)
                   for dx, dy in [(-10, -5.75), (10, -5.75), (10, 5.75), (-10, 5.75)]]
        m.add_lwpolyline(corners, close=True, dxfattribs={"layer": "COURTYARD"})

    # Functional allocation, kept close to the hub. These are routing guides.
    zones = [(0, "nRF52/BLE 12x9"), (90, "POWER 12x9"),
             (180, "CHARGE/USB PADS 12x9"), (270, "IMU / STORAGE 12x9")]
    for angle, label in zones:
        c = polar(18.5, angle, 4.6)
        corners = []
        for dx, dy in [(-6, -4.5), (6, -4.5), (6, 4.5), (-6, 4.5)]:
            # local dx radial, dy tangent
            corners.append(polar(18.5 + dx, angle, 4.6 + dy))
        m.add_lwpolyline(corners, close=True, dxfattribs={"layer": "PLACEMENT_ZONES"})
        m.add_text(label, height=0.8, dxfattribs={"layer": "NOTES", "insert": c})

    # Hall index near bearing and trim-weight pads at every tip.
    hx, hy = polar(13.4, 0, -3.0)
    m.add_lwpolyline([(hx - 1.3, hy - 1.0), (hx + 1.3, hy - 1.0),
                      (hx + 1.3, hy + 1.0), (hx - 1.3, hy + 1.0)],
                     close=True, dxfattribs={"layer": "PLACEMENT_ZONES"})
    m.add_text("HALL", height=0.75, dxfattribs={"layer": "NOTES", "insert": (hx, hy)})
    for angle in (0, 90, 180, 270):
        x, y = polar(43.5, angle, 5.4)
        m.add_circle((x, y), 1.2, dxfattribs={"layer": "BALANCE"})

    m.add_text("Ticker Spinner v0.3 PCB mechanical template - mm - verify footprints before routing",
               height=1.2, dxfattribs={"layer": "NOTES", "insert": (-48, -55)})
    doc.saveas(OUT / "ticker_spinner_v0_3_pcb_outline.dxf")

    # Separate vertical tip-board template: four identical copies are required.
    tip = ezdxf.new("R2010"); tip.units = ezdxf.units.MM
    for name, color in [("EDGE.CUTS", 7), ("LED_SIDE", 4), ("CONNECTOR", 2), ("NOTES", 7)]:
        tip.layers.add(name, color=color)
    tm = tip.modelspace()
    w, hh = P["tip_board_width"], P["tip_board_height"]
    tm.add_lwpolyline([(-w/2,-hh/2),(w/2,-hh/2),(w/2,hh/2),(-w/2,hh/2)],
                      close=True, dxfattribs={"layer":"EDGE.CUTS"})
    for i in range(int(P["side_led_count_per_arm"])):
        z = P["side_led_z_start"] + i * P["side_led_z_pitch"] - P["assembled_thickness"] / 2
        tm.add_lwpolyline([(-.55,z-.45),(.55,z-.45),(.55,z+.45),(-.55,z+.45)],
                          close=True, dxfattribs={"layer":"LED_SIDE"})
        tm.add_text(f"S{i+1}", height=.55, dxfattribs={"layer":"NOTES", "insert":(1.25,z)})
    tm.add_lwpolyline([(-3.0,-1.45),(3.0,-1.45),(3.0,-.35),(-3.0,-.35)],
                      close=True, dxfattribs={"layer":"CONNECTOR"})
    tm.add_text("VERTICAL TIP LED BOARD - 4 IDENTICAL - 7.0 x 13.6 x 0.6 mm - 12x WS2812B-0909",
                height=.8, dxfattribs={"layer":"NOTES", "insert":(-3.5,-6.3)})
    tip.saveas(OUT / "ticker_spinner_v0_3_tip_led_board.dxf")


def export_dimension_png() -> Path:
    outline = np.array(pcb_outline_points())
    fig, (ax, side) = plt.subplots(1, 2, figsize=(16.5, 8.5), gridspec_kw={"width_ratios": [1.5, 1]})
    fig.suptitle("TICKER SPINNER v0.3 — DIMENSIONAL REFERENCE (mm)", fontsize=16, weight="bold")

    # Housing top view from a dense projection of the exact arm envelope.
    body = rotor_body(1.0)
    face = max(body.faces("<Z").vals(), key=lambda f: f.Area())
    outer = max(face.Wires(), key=lambda w: abs(cq.Face.makeFromWires(w).Area()))
    hp = []
    for e in outer.Edges():
        samples = max(4, int(math.ceil(e.Length() / 0.15)))
        hp.extend([(e.positionAt(float(t)).x, e.positionAt(float(t)).y)
                   for t in np.linspace(0, 1, samples, endpoint=False)])
    hp.sort(key=lambda p: math.atan2(p[1], p[0]))
    ax.add_patch(Polygon(hp, closed=True, facecolor="#e7eaee", edgecolor="black", lw=1.5))
    ax.add_patch(Circle((0, 0), P["bearing_od_nominal"] / 2, fill=False, color="#1565c0", lw=2))
    ax.add_patch(Circle((0, 0), P["bearing_bore_diameter"] / 2, fill=False, color="#1565c0", lw=1))
    for angle in (0, 90, 180, 270):
        for i in range(int(P["led_count_top_per_arm"])):
            r = P["led_radial_start"] + i * P["led_pitch"]
            x, y = polar(r, angle)
            ax.add_patch(Rectangle((x - 0.7, y - 0.7), 1.4, 1.4, angle=angle,
                                   facecolor="#ffca28", edgecolor="none"))
    for x, y in screw_positions():
        ax.add_patch(Circle((x, y), P["screw_clearance_diameter"] / 2,
                            fill=False, color="#c62828", lw=1.2))
    ax.annotate("", xy=(-50, -52), xytext=(50, -52), arrowprops=dict(arrowstyle="<->"))
    ax.text(0, -55, "100.0 overall", ha="center", va="top", fontsize=11)
    ax.annotate("", xy=(-11, 0), xytext=(11, 0), arrowprops=dict(arrowstyle="<->", color="#1565c0"))
    ax.text(0, 2.2, "608 OD 22.0\nseat 21.85", ha="center", fontsize=9, color="#1565c0")
    ax.text(-48, 48, "80 × top RGB\n20/arm, pitch 1.60\nR14.8…45.2", va="top", fontsize=10)
    ax.text(-48, -40, "4 × M2 screws\nR30, tangent +5.3", va="top", fontsize=10)
    ax.set_aspect("equal")
    ax.set_xlim(-58, 58); ax.set_ylim(-58, 58); ax.axis("off")
    ax.set_title("TOP VIEW")

    # Simplified section through arm 1.
    side.add_patch(Rectangle((-50, 0), 100, 16, facecolor="#e7eaee", edgecolor="black"))
    side.add_patch(Rectangle((-11, 4.5), 22, 7, facecolor="#b0bec5", edgecolor="#1565c0", lw=2))
    side.add_patch(Rectangle((-48, 6.5), 96, 1, facecolor="#2e7d32", edgecolor="black"))
    side.add_patch(Rectangle((14, 1.6), 20, 3.2, facecolor="#90caf9", edgecolor="black"))
    side.add_patch(Rectangle((-46.3, 14.5), 32.9, 1.5, facecolor="#fff59d", edgecolor="#f9a825"))
    side.annotate("", xy=(52, 0), xytext=(52, 16), arrowprops=dict(arrowstyle="<->"))
    side.text(54, 8, "16.0 assembled", rotation=90, va="center")
    side.annotate("", xy=(12.5, 4.5), xytext=(12.5, 11.5), arrowprops=dict(arrowstyle="<->", color="#1565c0"))
    side.text(14.5, 8, "7.0 bearing", va="center", color="#1565c0")
    side.annotate("PCB 1.0 @ Z=6.5", xy=(38, 7.0), xytext=(22, -1.2),
                  arrowprops=dict(arrowstyle="->"), ha="center", fontsize=9)
    side.annotate("LiPo envelope 20×11.5×3.2", xy=(24, 3.2), xytext=(22, -3.2),
                  arrowprops=dict(arrowstyle="->"), ha="center", fontsize=9)
    side.annotate("1.5 roof + diffuser", xy=(-30, 12.3), xytext=(-38, 18.2),
                  arrowprops=dict(arrowstyle="->"), ha="center", fontsize=9)
    side.annotate("608 bearing 22×7×8", xy=(0, 9.5), xytext=(16, 18.2),
                  arrowprops=dict(arrowstyle="->", color="#1565c0"),
                  ha="center", fontsize=9, color="#1565c0")
    side.set_xlim(-58, 65); side.set_ylim(-5, 22); side.set_aspect("auto"); side.axis("off")
    side.set_title("SECTION / STACK")

    fig.text(0.52, 0.03,
             "Envelope prototype. Recommended print clearance: XY 0.20 mm; validate 608 press fit with a coupon. "
             "Side windows: 12/arm. Four identical universal bays maintain 90° mass symmetry.",
             ha="center", fontsize=9)
    path = OUT / "ticker_spinner_v0_3_dimension_drawing.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path


def export_pdf() -> None:
    pdf = OUT / "ticker_spinner_v0_3_engineering_drawing.pdf"
    doc = SimpleDocTemplate(str(pdf), pagesize=landscape(A3), rightMargin=14*mm,
                            leftMargin=14*mm, topMargin=12*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    story = [Paragraph("Ticker Spinner v0.3 — Engineering Reference", styles["Title"]), Spacer(1, 4*mm)]
    data = [
        ["Item", "Nominal", "Design intent / tolerance"],
        ["Overall envelope", "Ø100 × 16 mm", "Four identical arms at 90°"],
        ["Bearing", "608: 22 × 7 × 8 mm", "Printed seat Ø21.85; make fit coupon first"],
        ["Housing split", "8.0 + 8.0 mm", "Bottom tray + removable top"],
        ["PCB", "1.0 mm, max Ø96 envelope", "DXF is mechanical template, not finished layout"],
        ["Top LEDs", "80 total; 20/arm", "1.3 mm package; 1.60 mm radial pitch"],
        ["Side LEDs", "48 total; 12/tip", "Addressable 0909 RGB, 1.05 mm pitch"],
        ["Universal bays", "4 × 20 × 11.5 × 3.2 mm", "Populate opposite matched pairs; balance unused bays"],
        ["Fasteners", "4 × M2", "Top clearance Ø2.3; lower self-tap pilot Ø1.7"],
        ["Material", "PETG/PA12 preferred", "Prototype: 0.2 mm layers, 4 walls, 30–40% infill"],
    ]
    table = Table(data, colWidths=[45*mm, 58*mm, 150*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#263238")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.35, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f3f5f6")]),
        ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [table, Spacer(1, 5*mm),
              Paragraph("Critical v0.3 notes", styles["Heading2"]),
              Paragraph("The model reserves mass symmetrically, but the populated PCB must be dynamically balanced. "
                        "Populate opposite battery bays as a matched pair only when the power architecture supports it; "
                        "otherwise use one cell and an equal non-conductive dummy mass in the opposite bay. Keep antenna copper/metal keep-out per the "
                        "chosen nRF52 module. Confirm LED, USB/pogo and Hall footprints before routing. The top diffuser is a "
                        "single four-strip STL and may be printed in translucent PETG or replaced with cast clear resin.",
                        styles["BodyText"])]
    doc.build(story)


def _outline_for_shape(shape: cq.Workplane) -> list[tuple[float, float]]:
    face = max(shape.faces("<Z").vals(), key=lambda f: f.Area())
    outer = max(face.Wires(), key=lambda w: abs(cq.Face.makeFromWires(w).Area()))
    return _ordered_wire_points(outer, 0.18)


def _setup_plan_ax(ax, title: str) -> None:
    ax.set_aspect("equal")
    ax.set_xlim(-57, 57)
    ax.set_ylim(-57, 57)
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=12, weight="bold")


def _title_block(fig, sheet: str, title: str) -> None:
    fig.text(0.04, 0.965, "TICKER SPINNER v0.3", fontsize=17, weight="bold", va="top")
    fig.text(0.04, 0.935, title, fontsize=12, va="top")
    fig.text(0.69, 0.04, "UNITS mm | SCALE NTS | PROTOTYPE",
             fontsize=8, family="monospace")
    fig.text(0.04, 0.04, "Circumscribed envelope Ø100 | Assembly thickness 16 | Bearing 608",
             fontsize=8, family="monospace")
    fig.text(0.94, 0.04, f"SHEET {sheet}/5", fontsize=9, ha="right", weight="bold")
    fig.lines.extend([
        plt.Line2D([0.03, 0.97], [0.055, 0.055], transform=fig.transFigure, color="black", lw=0.8),
        plt.Line2D([0.03, 0.97], [0.91, 0.91], transform=fig.transFigure, color="black", lw=0.8),
    ])


def export_multisheet_pdf() -> None:
    """Five-sheet orthographic/mechanical reference set."""
    pdf_path = OUT / "ticker_spinner_v0_3_engineering_drawing.pdf"
    housing = _outline_for_shape(rotor_body(1.0))
    pcb_pts = pcb_outline_points()
    inner = _outline_for_shape(rotor_body(1.0, inset=1.55, hub_radius=16.4))
    grey, edge = "#e9edf0", "#202428"

    with PdfPages(pdf_path) as pdf:
        # Sheet 1 - general arrangement and section.
        fig = plt.figure(figsize=(16.54, 11.69))
        _title_block(fig, "1", "GENERAL ARRANGEMENT - TOP, SIDE AND SECTION")
        ax = fig.add_axes([0.04, 0.11, 0.56, 0.77])
        _setup_plan_ax(ax, "A. TOP VIEW")
        ax.add_patch(Polygon(housing, closed=True, fc=grey, ec=edge, lw=1.5))
        ax.add_patch(Circle((0, 0), 50, fill=False, ls="--", lw=0.7, ec="#777"))
        ax.add_patch(Circle((0, 0), 11, fill=False, ec="#1565c0", lw=1.7))
        ax.add_patch(Circle((0, 0), 9.75, fill=False, ec="#1565c0", lw=0.9))
        for angle in (0, 90, 180, 270):
            for i in range(int(P["led_count_top_per_arm"])):
                r = P["led_radial_start"] + i * P["led_pitch"]
                x, y = polar(r, angle)
                corners = [polar(r + dr, angle, dt)
                           for dr, dt in [(-.65,-.65),(.65,-.65),(.65,.65),(-.65,.65)]]
                ax.add_patch(Polygon(corners, closed=True, fc="#ffbf00", ec="none"))
        for x, y in screw_positions():
            ax.add_patch(Circle((x, y), 1.15, fill=False, ec="#d32f2f", lw=1.2))
        ax.annotate("", xy=(-50, -53), xytext=(50, -53), arrowprops=dict(arrowstyle="<->"))
        ax.text(0, -56, "Ø100 CIRCUMSCRIBED ENVELOPE", ha="center", fontsize=9)
        ax.annotate("", xy=(-11, 2), xytext=(11, 2), arrowprops=dict(arrowstyle="<->", color="#1565c0"))
        ax.text(0, 4, "Ø22 BEARING", ha="center", color="#1565c0", fontsize=8)
        ax.text(-54, 48, "80 TOP RGB\n20 PER ARM\nPITCH 1.60", fontsize=9, va="top")

        side = fig.add_axes([0.65, 0.59, 0.31, 0.20])
        side.set_title("B. SIDE ELEVATION", loc="left", fontsize=12, weight="bold")
        side.add_patch(Rectangle((-39.375, 0), 78.75, P["assembled_thickness"], fc=grey, ec=edge, lw=1.4))
        side.plot([-39.375, 39.375], [P["half_height"], P["half_height"]], color="#555", lw=0.8, ls="--")
        side.annotate("", xy=(43, 0), xytext=(43, P["assembled_thickness"]), arrowprops=dict(arrowstyle="<->"))
        side.text(45, P["half_height"], "16.0", rotation=90, va="center")
        side.annotate("", xy=(-39.375, -2), xytext=(39.375, -2), arrowprops=dict(arrowstyle="<->"))
        side.text(0, -3.4, "78.75 PROJECTED LENGTH", ha="center", fontsize=8)
        side.set_xlim(-48, 50); side.set_ylim(-5, 20); side.axis("off")

        sec = fig.add_axes([0.65, 0.24, 0.31, 0.24])
        sec.set_title("C. SECTION A-A THROUGH ARM", loc="left", fontsize=12, weight="bold")
        sec.add_patch(Rectangle((-39.375, 0), 78.75, 16, fc=grey, ec=edge, lw=1.2))
        sec.add_patch(Rectangle((-11, 4.5), 22, 7, fc="#b0bec5", ec="#1565c0", lw=1.5))
        sec.add_patch(Rectangle((-37, 6.5), 74, 1, fc="#2e7d32", ec=edge))
        sec.add_patch(Rectangle((14, 1.6), 20, 3.2, fc="#90caf9", ec=edge))
        sec.add_patch(Rectangle((-35, 14.5), 28, 1.5, fc="#fff59d", ec="#f9a825"))
        sec.annotate("PCB 1.0", xy=(32, 7), xytext=(27, 19), arrowprops=dict(arrowstyle="->"), fontsize=8)
        sec.annotate("LiPo cavity", xy=(24, 3), xytext=(18, -3), arrowprops=dict(arrowstyle="->"), fontsize=8)
        sec.annotate("608: 22×7×8", xy=(0, 10), xytext=(-12, 19), arrowprops=dict(arrowstyle="->"), fontsize=8)
        sec.set_xlim(-48, 50); sec.set_ylim(-5, 22); sec.axis("off")
        fig.text(0.65, 0.14, "FASTENERS: 4 × M2\nSPLIT LINE: Z=8.0\nBEARING AXIAL POCKET: Z=4.5…11.5",
                 fontsize=9, linespacing=1.6)
        pdf.savefig(fig); plt.close(fig)

        # Sheet 2 - bottom tray, internal projection and section.
        fig = plt.figure(figsize=(16.54, 11.69))
        _title_block(fig, "2", "BOTTOM HOUSING - INTERNAL VIEW AND FEATURES")
        ax = fig.add_axes([0.04, 0.11, 0.58, 0.77]); _setup_plan_ax(ax, "A. VIEW FROM INSIDE")
        ax.add_patch(Polygon(housing, closed=True, fc=grey, ec=edge, lw=1.5))
        ax.add_patch(Polygon(inner, closed=True, fc="white", ec="#78909c", lw=1.0, ls="--"))
        ax.add_patch(Circle((0, 0), 13.4, fc=grey, ec=edge, lw=1.0))
        ax.add_patch(Circle((0, 0), P["bearing_seat_diameter"]/2, fc="white", ec="#1565c0", lw=1.6))
        ax.add_patch(Circle((0, 0), P["bearing_bore_diameter"]/2, fill=False, ec="#1565c0", lw=0.9))
        for angle in (0, 90, 180, 270):
            corners = [polar(P["battery_center_radius"] + dx, angle, dy)
                       for dx, dy in [(-10, -5.75), (10, -5.75), (10, 5.75), (-10, 5.75)]]
            ax.add_patch(Polygon(corners, closed=True, fc="#90caf9", ec=edge, alpha=.85))
        for x, y in screw_positions():
            ax.add_patch(Circle((x, y), 2.5, fc=grey, ec="#d32f2f", lw=1.2))
            ax.add_patch(Circle((x, y), .85, fc="white", ec="#d32f2f", lw=1.0))
        ax.text(-53, 50, "WALL NOMINAL 1.55\nFLOOR 1.60", va="top", fontsize=9)
        ax.text(-53, -45, "4 UNIVERSAL BALANCED BAYS\n20.6 × 12.1 × 3.45 CUT\nCENTERS R27", fontsize=9)
        ax.annotate("", xy=(-10.925, 1), xytext=(10.925, 1), arrowprops=dict(arrowstyle="<->", color="#1565c0"))
        ax.text(0, 3, "Ø21.85 SEAT", ha="center", fontsize=8, color="#1565c0")

        detail = fig.add_axes([0.67, 0.57, 0.28, 0.22])
        detail.set_title("B. BEARING RETENTION SECTION", loc="left", fontsize=12, weight="bold")
        detail.add_patch(Rectangle((-19, 0), 38, 8.0, fc=grey, ec=edge))
        detail.add_patch(Rectangle((-11, 4.5), 22, 3.5, fc="#b0bec5", ec="#1565c0", lw=1.5))
        detail.add_patch(Rectangle((-9.75, 0), 19.5, 4.5, fc="white", ec=edge))
        detail.annotate("4.5 RETAINING LIP", xy=(10, 2.2), xytext=(22, 2.2), arrowprops=dict(arrowstyle="->"), fontsize=8)
        detail.annotate("PRESS-FIT WALL Ø21.85", xy=(11, 6), xytext=(22, 7), arrowprops=dict(arrowstyle="->"), fontsize=8)
        detail.set_xlim(-25, 50); detail.set_ylim(-2, 11); detail.axis("off")
        fig.text(0.67, 0.43, "M2 BOSS\n- boss Ø5.0\n- pilot Ø1.7\n- four positions at 90°\n- verify self-tapping screw type",
                 fontsize=10, linespacing=1.55)
        fig.text(0.67, 0.20, "PRINT ORIENTATION\nExterior floor on build plate.\nRecommended prototype: PETG, 0.20 layer,\n4 walls, 30-40% infill.",
                 fontsize=10, linespacing=1.55)
        pdf.savefig(fig); plt.close(fig)

        # Sheet 3 - top cover and diffuser details.
        fig = plt.figure(figsize=(16.54, 11.69))
        _title_block(fig, "3", "TOP COVER - EXTERNAL/INTERNAL VIEWS AND LIGHT WINDOWS")
        ax1 = fig.add_axes([0.035, 0.16, 0.46, 0.72]); _setup_plan_ax(ax1, "A. EXTERNAL VIEW")
        ax1.add_patch(Polygon(housing, closed=True, fc=grey, ec=edge, lw=1.4))
        for angle in (0, 90, 180, 270):
            r0, r1 = P["top_window_r0"], P["top_window_r1"]
            p0 = polar(r0, angle); p1 = polar(r1, angle)
            ax1.plot([p0[0], p1[0]], [p0[1], p1[1]], color="#ffc107", lw=7, solid_capstyle="round")
            p0 = polar(47.4, angle, -1.2); p1 = polar(47.4, angle, 1.2)
            ax1.plot([p0[0],p1[0]],[p0[1],p1[1]],color="#29b6f6",lw=4)
        for x, y in screw_positions(): ax1.add_patch(Circle((x, y), 2.15, fill=False, ec="#d32f2f"))
        ax1.text(-54, 49, "4 TOP WINDOWS\n32.9 × 2.4\nROUNDED ENDS", fontsize=9, va="top")
        ax1.text(-54, -48, "12 VERTICAL TIP WINDOWS / ARM\nSEE SHEET 5", fontsize=9)

        ax2 = fig.add_axes([0.505, 0.16, 0.46, 0.72]); _setup_plan_ax(ax2, "B. UNDERSIDE VIEW")
        ax2.add_patch(Polygon(housing, closed=True, fc=grey, ec=edge, lw=1.4))
        ax2.add_patch(Polygon(inner, closed=True, fc="white", ec="#78909c", lw=1.0, ls="--"))
        ax2.add_patch(Circle((0, 0), 13.4, fc=grey, ec=edge))
        ax2.add_patch(Circle((0, 0), P["bearing_seat_diameter"]/2, fc="white", ec="#1565c0", lw=1.4))
        for angle in (0, 90, 180, 270):
            p0 = polar(P["top_window_r0"], angle); p1 = polar(P["top_window_r1"], angle)
            ax2.plot([p0[0], p1[0]], [p0[1], p1[1]], color="#fff176", lw=6, solid_capstyle="round")
        for x, y in screw_positions(): ax2.add_patch(Circle((x, y), 1.15, fill=False, ec="#d32f2f"))
        ax2.text(-54, 49, "ROOF 1.50\nINTERNAL WALL 1.55", fontsize=9, va="top")
        ax2.text(-54, -48, "COUNTERBORE Ø4.3 × 1.1\nCLEARANCE Ø2.3", fontsize=9)
        fig.text(0.38, 0.10, "DIFFUSER INSERT: 4 separate translucent strips in one STL | 32.5 × 2.0 × 1.25 nominal | XY clearance 0.20/side",
                 fontsize=9, ha="center")
        pdf.savefig(fig); plt.close(fig)

        # Sheet 4 - PCB mechanical template and placement zones.
        fig = plt.figure(figsize=(16.54, 11.69))
        _title_block(fig, "4", "PCB MECHANICAL TEMPLATE - OUTLINE, LED CENTERS AND RESERVED ZONES")
        ax = fig.add_axes([0.04, 0.11, 0.62, 0.77]); _setup_plan_ax(ax, "A. PCB TOP / COMPONENT SIDE")
        ax.add_patch(Polygon(pcb_pts, closed=True, fc="#dcedc8", ec=edge, lw=1.5))
        ax.add_patch(Circle((0,0), P["pcb_center_hole"]/2, fc="white", ec="#1565c0", lw=1.4))
        for x,y in screw_positions(): ax.add_patch(Circle((x,y), 1.25, fc="white", ec="#d32f2f"))
        for ai, angle in enumerate((0,90,180,270), start=1):
            for i in range(int(P["led_count_top_per_arm"])):
                r=P["led_radial_start"]+i*P["led_pitch"]; x,y=polar(r,angle)
                corners=[polar(r+dr,angle,dt) for dr,dt in [(-.75,-.75),(.75,-.75),(.75,.75),(-.75,.75)]]
                ax.add_patch(Polygon(corners,closed=True,fc="#ffca28",ec="#795548",lw=.25))
            p0=polar(46.3,angle,-3.5); p1=polar(46.3,angle,3.5)
            ax.plot([p0[0],p1[0]],[p0[1],p1[1]],color="#29b6f6",lw=3)
        zone_colors=["#90caf9","#ffcc80","#ce93d8","#a5d6a7"]
        for (angle,label),zc in zip([(0,"nRF52/BLE"),(90,"POWER"),(180,"CHARGE"),(270,"IMU")],zone_colors):
            corners=[polar(18.5+dx,angle,4.6+dy) for dx,dy in [(-6,-4.5),(6,-4.5),(6,4.5),(-6,4.5)]]
            ax.add_patch(Polygon(corners,closed=True,fc=zc,ec=edge,alpha=.75))
            cx,cy=polar(18.5,angle,4.6); ax.text(cx,cy,label,ha="center",va="center",fontsize=6,rotation=angle)
        hx,hy=polar(13.4,0,-3); ax.add_patch(Rectangle((hx-1.3,hy-1),2.6,2,fc="#ef9a9a",ec=edge)); ax.text(hx,hy,"H",ha="center",va="center",fontsize=6)
        ax.annotate("",xy=(-11.6,1.5),xytext=(11.6,1.5),arrowprops=dict(arrowstyle="<->",color="#1565c0"))
        ax.text(0,3,"NPTH Ø23.2",ha="center",fontsize=8,color="#1565c0")
        ax.text(-54,-49,"BOARD 1.0 mm\nMAX RADIAL EXTENT 48.0\nSHELL CLEARANCE 2.0",fontsize=9)

        notes = fig.add_axes([0.70, 0.17, 0.26, 0.65]); notes.axis("off")
        notes.set_title("LEGEND / ROUTING BASIS",loc="left",fontsize=12,weight="bold")
        rows=[("Yellow","80 × top RGB, 1.5×1.5 courtyard"),("Blue tip line","captured vertical daughterboard"),("Blue zone","nRF52/BLE allocation"),("Orange zone","power regulation"),("Purple zone","charge/interface"),("Green zone","IMU / storage"),("Red H","Hall index sensor")]
        y=.94
        for name,desc in rows:
            notes.text(.02,y,name,weight="bold",fontsize=9); notes.text(.34,y,desc,fontsize=9); y-=.08
        notes.text(.02,y-.03,"CRITICAL",weight="bold",fontsize=10,color="#c62828")
        notes.text(.02,y-.09,"DXF is a mechanical template, not a finished PCB.\nReplace all provisional courtyards with selected\nmanufacturer footprints before routing.",fontsize=9,linespacing=1.5)
        notes.text(.02,y-.27,"BALANCE",weight="bold",fontsize=10)
        notes.text(.02,y-.33,"Four trim-weight areas are provided in DXF.\nPerform static and dynamic balance after population.",fontsize=9,linespacing=1.5)
        notes.text(.02,y-.47,"BATTERIES",weight="bold",fontsize=10)
        notes.text(.02,y-.53,"Use a protected opposite matched pair, with\nbalanced electronics or trim mass in the other bays.",fontsize=9,linespacing=1.5)
        pdf.savefig(fig); plt.close(fig)

        # Sheet 5 - the missing radial end view and virtual cylindrical display.
        fig = plt.figure(figsize=(16.54, 11.69))
        _title_block(fig, "5", "CYLINDRICAL POV TICKER - RADIAL TIP FACE AND UNWRAPPED DISPLAY")

        end = fig.add_axes([0.06, 0.48, 0.27, 0.34])
        end.set_title("A. RADIAL END VIEW - LOOKING TOWARD HUB", loc="left", fontsize=12, weight="bold")
        end.add_patch(Rectangle((-7.5, 0), 15, 16, fc=grey, ec=edge, lw=1.6))
        end.plot([-7.5, 7.5], [8.0, 8.0], ls="--", lw=.8, color="#555")
        z_centers = [P["side_led_z_start"] + i * P["side_led_z_pitch"]
                     for i in range(int(P["side_led_count_per_arm"]))]
        for i, z in enumerate(z_centers, start=1):
            end.add_patch(Rectangle((-P["side_window_width"]/2,
                                     z-P["side_window_height"]/2),
                                    P["side_window_width"], P["side_window_height"],
                                    fc="#29b6f6", ec="#0277bd", lw=.7))
            end.text(2.0, z, f"LED {i}", va="center", fontsize=7)
        end.annotate("", xy=(-9, 0), xytext=(-9, 16), arrowprops=dict(arrowstyle="<->"))
        end.text(-10.2, 8.0, "16.0", rotation=90, va="center", fontsize=8)
        end.annotate("", xy=(-7.5, -1.2), xytext=(7.5, -1.2), arrowprops=dict(arrowstyle="<->"))
        end.text(0, -2.2, "TIP WIDTH 15.0", ha="center", fontsize=8)
        end.text(-7.2, 8.3, "CASE SPLIT", fontsize=7)
        end.set_xlim(-12, 13); end.set_ylim(-3, 19); end.set_aspect("equal"); end.axis("off")

        conn = fig.add_axes([0.38, 0.50, 0.25, 0.31])
        conn.set_title("B. TIP CONNECTION SECTION", loc="left", fontsize=12, weight="bold")
        conn.add_patch(Rectangle((0, 0), 18, 16, fc=grey, ec=edge, lw=1.4))
        conn.add_patch(Rectangle((2.8, 1.2), .6, 13.6, fc="#00897b", ec=edge, lw=1.0))
        conn.add_patch(Rectangle((-12, 6.5), 15.2, 1, fc="#2e7d32", ec=edge, lw=1.0))
        for z in z_centers:
            conn.add_patch(Rectangle((2.9, z-.39), 3.1, .78, fc="#29b6f6", ec="#0277bd", lw=.5))
        conn.annotate("VERTICAL LED BOARD\n7.0 × 13.6 × 0.6", xy=(3.1, 11), xytext=(9, 18),
                      arrowprops=dict(arrowstyle="->"), fontsize=8, ha="center")
        conn.annotate("MAIN 4-ARM PCB", xy=(-4, 7), xytext=(-8, 18),
                      arrowprops=dict(arrowstyle="->"), fontsize=8, ha="center")
        conn.annotate("SOLDER TABS / FPC", xy=(3.1, 7), xytext=(10, -2),
                      arrowprops=dict(arrowstyle="->"), fontsize=8, ha="center")
        conn.set_xlim(-14, 22); conn.set_ylim(-3, 21); conn.axis("off")

        circle = fig.add_axes([0.70, 0.52, 0.24, 0.28])
        circle.set_title("C. VIRTUAL CYLINDER - TOP VIEW", loc="left", fontsize=12, weight="bold")
        circle.add_patch(Circle((0,0), 10, fill=False, ec=edge, lw=1.5))
        for angle, color in zip((0,90,180,270),("#ef5350","#42a5f5","#66bb6a","#ffca28")):
            x,y=polar(10,angle); circle.plot([0,x],[0,y],color=color,lw=2)
            circle.add_patch(Circle((x,y),.45,fc=color,ec="none"))
        circle.annotate("ROTATION", xy=(8,6), xytext=(1,12), arrowprops=dict(arrowstyle="->",connectionstyle="arc3,rad=.3"), fontsize=8)
        circle.text(0,-13,"Tip column sweeps the Ø100 circumference",ha="center",fontsize=8)
        circle.set_xlim(-14,14); circle.set_ylim(-14,14); circle.set_aspect("equal"); circle.axis("off")

        unwrap = fig.add_axes([0.08, 0.13, 0.84, 0.25])
        unwrap.set_title("D. UNWRAPPED VIRTUAL DISPLAY SURFACE", loc="left", fontsize=12, weight="bold")
        unwrap.add_patch(Rectangle((0,0),314.16,8.5,fc="#101820",ec=edge,lw=1.4))
        for z in np.linspace(.35,8.15,12): unwrap.plot([0,314.16],[z,z],color="#37474f",lw=.35)
        for x in np.linspace(0,314.16,73): unwrap.plot([x,x],[0,8.5],color="#263238",lw=.25)
        unwrap.text(18,4.25,"SBER   317.42   +1.73%",color="#43ff72",fontsize=22,
                    family="monospace",weight="bold",va="center")
        for x,c in zip((0,78.54,157.08,235.62),("#ef5350","#42a5f5","#66bb6a","#ffca28")):
            unwrap.axvline(x,color=c,lw=1.2,ls="--")
        unwrap.annotate("",xy=(0,-1.2),xytext=(314.16,-1.2),arrowprops=dict(arrowstyle="<->"))
        unwrap.text(157,-2.2,"C = π × 100 = 314.2 mm",ha="center",fontsize=8)
        unwrap.text(318,4.25,"12 pixels\nhigh",va="center",fontsize=8)
        unwrap.set_xlim(-8,330); unwrap.set_ylim(-3,11); unwrap.axis("off")
        fig.text(0.68, 0.42,
                 "FUNCTION\nEach LED height becomes one horizontal pixel row.\nTimed flashes create angular columns as the tip moves.\nThe four arms are phase-shifted by 90° in firmware.",
                 fontsize=9, linespacing=1.5)
        fig.text(0.37, 0.42,
                 "MECHANICAL CHANGE\nThe cylindrical ticker uses four captured vertical\ndaughterboards with 12 addressable 0909 RGB LEDs.\nThe 16 mm housing provides manufacturable margins.",
                 fontsize=9, linespacing=1.5)
        pdf.savefig(fig); plt.close(fig)


def validate_stl() -> dict:
    report = {}
    for path in sorted(OUT.glob("ticker_spinner_v0_3_*.stl")):
        mesh = trimesh.load_mesh(path, process=True)
        report[path.name] = {
            "watertight": bool(mesh.is_watertight),
            "body_count": int(len(mesh.split(only_watertight=False))),
            "bounds_mm": np.round(mesh.bounds, 3).tolist(),
            "extents_mm": np.round(mesh.extents, 3).tolist(),
            "volume_mm3": round(float(mesh.volume), 2),
        }
    (OUT / "ticker_spinner_v0_3_validation.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    return report


def write_readme(validation: dict) -> None:
    text = f"""# Ticker Spinner v0.3 - 12-pixel cylindrical ticker

Параметрический механический прототип четырёхлучевого POV-спиннера.

## Что входит

- `ticker_spinner_v0_3_bottom.stl/.step` — нижняя ванна, посадка 608, карманы аккумуляторов, стойки M2.
- `ticker_spinner_v0_3_top.stl/.step` — съёмная крышка, верхние и торцевые световые окна.
- `ticker_spinner_v0_3_diffusers.stl/.step` — четыре соединённых рассеивателя верхних LED.
- `ticker_spinner_v0_3_finger_cap_top.stl/.step` и `..._bottom.stl/.step` — неподвижные накладки для удержания за внутреннее кольцо 608.
- `ticker_spinner_v0_3_assembly.step` — механическая сборка с PCB-envelope.
- `ticker_spinner_v0_3_pcb_outline.dxf` — контур, NPTH, LED и функциональные зоны по слоям.
- `ticker_spinner_v0_3_tip_led_board.dxf` — вертикальная плата 12 торцевых LED; требуется 4 шт.
- `ticker_spinner_v0_3_engineering_drawing.pdf` и PNG — размерная справка.
- `ticker_spinner_v0_3_validation.json` — автоматическая проверка STL.

Электрическая схема, KiCad-разводка, BOM и pin-map в этот пакет намеренно не включены: сначала нужно утвердить конкретные корпуса LED, nRF52, IMU, зарядник и аккумулятор.

## Зафиксированная геометрия

- Габарит: **Ø100 × 16 мм**.
- Подшипник: **608 (22 × 7 × 8 мм)**; печатная посадка Ø{P['bearing_seat_diameter']:.2f} мм.
- PCB: ориентировочно 1,0 мм, внешний габарит до Ø96 мм, отверстие центра Ø{P['pcb_center_hole']:.1f} мм.
- Верх: 20 LED на луч, шаг {P['led_pitch']:.2f} мм, 80 всего; рассчитано на корпус класса 1,3 × 1,3 мм.
- Торец: вертикальная колонка 12 адресных RGB LED на луч, 48 всего; четыре сменные tip-board 7 × 13,6 × 0,6 мм.
- Крепёж: 4 × M2, симметрия 90°.
- Универсальные карманы: 4 × {P['battery_length']:.0f} × {P['battery_width']:.1f} × {P['battery_height']:.1f} мм; аккумуляторы ставятся противоположной согласованной парой.

## Важные инженерные оговорки

Это v0.3 механики и **основа для разводки**, а не готовая электрическая схема. Для торцевой строки принят адресный WS2812B-0909 либо совместимый корпус 0,9 × 0,9 мм; перед заказом нужно проверить фактический footprint выбранного производителя. К единой основной PCB добавлены четыре одинаковые ремонтопригодные торцевые платы, механически удерживаемые направляющими корпуса. Перед финальной PCB нужно утвердить nRF52-модуль, Hall, IMU, зарядник и способ связи/зарядки. Для раннего прототипа безопаснее ставить один аккумулятор и равную балластную массу напротив; для большей ёмкости — только согласованную защищённую пару в противоположных карманах.

Перед печатью корпуса напечатайте маленький coupon с отверстиями Ø21.70 / 21.85 / 22.00 / 22.15 мм и выберите посадку под конкретный принтер и материал. Для первой печати: PETG, слой 0,2 мм, 4 периметра, 30–40% infill. Крышка и низ печатаются внешней плоской стороной на столе; рассеиватель — прозрачным/молочным PETG либо отливается прозрачной смолой.

Балансировка обязательна после монтажа: предусмотрены четыре равных зоны trim-weight в DXF. Сначала статическая балансировка, затем динамическая на ограниченных оборотах в защитном кожухе.

## Перегенерация

Главные параметры находятся в словаре `P` файла `generate_ticker_spinner_v0_3.py`. После изменения запустите его в Python-окружении с зависимостями из `requirements_ticker_spinner_v0_3.txt`; все форматы пересобираются из одной геометрии.

## Результат проверки

```json
{json.dumps(validation, indent=2, ensure_ascii=False)}
```
"""
    (OUT / "README_Ticker_Spinner_v0_3.md").write_text(text, encoding="utf-8")


def main() -> None:
    print("build bottom", flush=True)
    bottom = make_bottom()
    print("build top", flush=True)
    top = make_top_assembled()
    print("build diffusers", flush=True)
    diff = make_diffusers_assembled()
    print("build pcb", flush=True)
    pcb = make_pcb()
    print("build tip boards", flush=True)
    tip_boards = make_tip_boards_assembled()
    print("export CAD", flush=True)
    export_cad(bottom, top, diff, pcb, tip_boards)
    print("export DXF", flush=True)
    export_dxf()
    print("export drawing", flush=True)
    export_dimension_png()
    print("export PDF", flush=True)
    export_multisheet_pdf()
    print("validate", flush=True)
    validation = validate_stl()
    write_readme(validation)
    shutil.copy2(__file__, OUT / "generate_ticker_spinner_v0_3.py")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
