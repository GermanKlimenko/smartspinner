#!/usr/bin/env python3
"""Generate Ticker Spinner v0.2 PCB placement mockups and draft KiCad boards."""

from __future__ import annotations

import csv
import json
import math
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_ticker_spinner as mech


OUT = Path(__file__).resolve().parents[1] / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
P = mech.P


def rot_point(x: float, y: float, angle: float) -> tuple[float, float]:
    a = math.radians(angle)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def rect_local(cx: float, cy: float, w: float, h: float, angle: float) -> list[tuple[float, float]]:
    return [(cx + dx, cy + dy) for dx, dy in
            [rot_point(-w/2,-h/2,angle), rot_point(w/2,-h/2,angle),
             rot_point(w/2,h/2,angle), rot_point(-w/2,h/2,angle)]]


def add_component(ax, x, y, w, h, angle, label, color, text_size=6):
    ax.add_patch(Polygon(rect_local(x,y,w,h,angle), closed=True, fc=color, ec="#263238", lw=.65))
    ax.text(x, y, label, ha="center", va="center", rotation=angle, fontsize=text_size, weight="bold")


def draw_mockup() -> None:
    outline = mech.pcb_outline_points()
    fig = plt.figure(figsize=(16, 10), facecolor="#f5f7f8")
    fig.suptitle("TICKER SPINNER v0.2 - PCB PLACEMENT MOCKUP", fontsize=18, weight="bold")

    ax = fig.add_axes([.04,.10,.60,.82]); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("MAIN 3-ARM PCB - COMPONENT SIDE", loc="left", fontsize=12, weight="bold")
    ax.add_patch(Polygon(outline, closed=True, fc="#dcedc8", ec="#263238", lw=1.6))
    ax.add_patch(Circle((0,0), P["pcb_center_hole"]/2, fc="#f5f7f8", ec="#1565c0", lw=1.5))

    # Symmetric power buses and LED chains.
    for angle, col in zip((0,120,240),("#e53935","#1e88e5","#8e24aa")):
        p0=mech.polar(13.2,angle,2.8); p1=mech.polar(45.2,angle,2.8)
        ax.plot([p0[0],p1[0]],[p0[1],p1[1]],color=col,lw=1.3,alpha=.8)
        p0=mech.polar(13.2,angle,-2.8); p1=mech.polar(45.2,angle,-2.8)
        ax.plot([p0[0],p1[0]],[p0[1],p1[1]],color="#455a64",lw=1.3,alpha=.8)

    # 45 addressable top pixels.
    for ai,angle in enumerate((0,120,240),start=1):
        for i in range(int(P["led_count_top_per_arm"])):
            r=P["led_radial_start"]+i*P["led_pitch"]; x,y=mech.polar(r,angle)
            ax.add_patch(Polygon(rect_local(x,y,1.9,1.9,angle),closed=True,fc="#ffd54f",ec="#8d6e63",lw=.35))
            if i in (0,7,14): ax.text(x,y,f"D{ai}.{i+1}",fontsize=3.8,ha="center",va="center",rotation=angle)

    # Inner functional blocks. Shapes are allocation envelopes, not final footprints.
    x,y=mech.polar(20.0,0,5.0); add_component(ax,x,y,7.0,7.0,0,"U1\nnRF52840\nIC","#90caf9")
    x,y=mech.polar(39.0,0,5.0); add_component(ax,x,y,8.0,2.4,0,"ANT1 + KEEP-OUT","#80cbc4",4.5)
    x,y=mech.polar(20.5,120,5.0); add_component(ax,x,y,9,7,120,"U2\nCHARGER +\nPROTECTION","#ffcc80",5.5)
    x,y=mech.polar(20.5,240,5.0); add_component(ax,x,y,9,7,240,"U3\n5V BOOST","#ce93d8",5.5)
    x,y=mech.polar(13.4,0,-3.1); add_component(ax,x,y,2.9,1.6,0,"H1","#ef9a9a",5)

    # Tip interfaces and battery connectors.
    for ai,angle in enumerate((0,120,240),start=1):
        x,y=mech.polar(46.0,angle); add_component(ax,x,y,2.2,7.0,angle,f"J{ai}\nTIP","#80deea",4.5)
        x,y=mech.polar(29.0,angle,-5.0); add_component(ax,x,y,4.5,2.4,angle,f"JB{ai}","#b0bec5",4.5)
        sx,sy=mech.screw_positions()[ai-1]
        ax.add_patch(Circle((sx,sy),1.25,fc="#f5f7f8",ec="#d32f2f",lw=1.0))

    ax.text(-51,-50,"RED / BLUE / PURPLE: provisional data branches\nGRAY: ground return\nActual impedance is non-critical at 800 kbit/s, but keep branches short.",fontsize=8)
    ax.set_xlim(-56,56); ax.set_ylim(-56,56)

    tip = fig.add_axes([.68,.47,.28,.40]); tip.set_aspect("equal"); tip.axis("off")
    tip.set_title("TIP LED BOARD - 3 IDENTICAL", loc="left", fontsize=12, weight="bold")
    w,h=P["tip_board_width"],P["tip_board_height"]
    tip.add_patch(Rectangle((-w/2,-h/2),w,h,fc="#dcedc8",ec="#263238",lw=1.5))
    for i in range(int(P["side_led_count_per_arm"])):
        yy=P["side_led_z_start"]+i*P["side_led_z_pitch"]-P["assembled_thickness"]/2
        tip.add_patch(Rectangle((-.45,yy-.45),.9,.9,fc="#29b6f6",ec="#0277bd",lw=.35))
        tip.text(.75,yy,f"TD{i+1}",fontsize=6,va="center")
    for i,(name,x) in enumerate(zip(("5V","GND","DIN","DOUT"),(-2.4,-.8,.8,2.4))):
        tip.add_patch(Rectangle((x-.45,-h/2+.15),.9,1.1,fc="#ffcc80",ec="#6d4c41",lw=.5))
        tip.text(x,-h/2-1.0,name,fontsize=6,ha="center",rotation=90)
    tip.annotate("",xy=(-w/2-1,-h/2),xytext=(-w/2-1,h/2),arrowprops=dict(arrowstyle="<->"))
    tip.text(-w/2-1.5,0,"13.6",rotation=90,va="center",fontsize=7)
    tip.text(0,h/2+1,"12 × WS2812B-0909\npitch 1.05 mm",ha="center",fontsize=8)
    tip.set_xlim(-7,8); tip.set_ylim(-9,10)

    info = fig.add_axes([.68,.10,.28,.28]); info.axis("off")
    info.set_title("POWER / SIGNAL CONCEPT", loc="left", fontsize=12, weight="bold")
    info.text(0,.88,"Main pixels",weight="bold",fontsize=9); info.text(.35,.88,"45 × addressable RGB 2020",fontsize=9)
    info.text(0,.76,"Tip pixels",weight="bold",fontsize=9); info.text(.35,.76,"36 × addressable RGB 0909",fontsize=9)
    info.text(0,.64,"LED rail",weight="bold",fontsize=9); info.text(.35,.64,"5 V, pulsed budget ≥1.5 A",fontsize=9)
    info.text(0,.52,"Logic",weight="bold",fontsize=9); info.text(.35,.52,"3.3 V nRF52 IC + level shift",fontsize=9)
    info.text(0,.40,"Index",weight="bold",fontsize=9); info.text(.35,.40,"Hall sensor near bearing",fontsize=9)
    info.text(0,.27,"STATUS",weight="bold",fontsize=9,color="#c62828")
    info.text(0,.04,"Placement/routing mockup only. Confirm footprints,\nantenna matching/keep-out, charging topology and\ncurrent limits before fabrication.",fontsize=8,linespacing=1.4)

    for ext in ("png","svg"):
        fig.savefig(OUT/f"ticker_spinner_v0_2_pcb_layout_mockup.{ext}",dpi=220,bbox_inches="tight")
    plt.close(fig)


def kicad_header(nets: list[str]) -> list[str]:
    lines=["(kicad_pcb (version 20240108) (generator pcbnew)",
           "  (general (thickness 1.0))",
           "  (paper \"A4\")",
           "  (layers (0 \"F.Cu\" signal) (31 \"B.Cu\" signal) (36 \"B.SilkS\" user \"b.silkscreen\") (37 \"F.SilkS\" user \"f.silkscreen\") (44 \"Edge.Cuts\" user))",
           "  (setup (pad_to_mask_clearance 0))"]
    for i,n in enumerate(nets, start=1): lines.append(f'  (net {i} "{n}")')
    return lines


def fp_rect(ref, value, x, y, w, h, angle=0, pads=None, layer="F.Cu") -> list[str]:
    lines=[f'  (footprint "Ticker:{value}" (layer "{layer}") (at {x:.3f} {y:.3f} {angle:.2f})',
           f'    (property "Reference" "{ref}" (at 0 {-h/2-1:.2f} {angle:.2f}) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))',
           f'    (property "Value" "{value}" (at 0 {h/2+1:.2f} {angle:.2f}) (layer "F.Fab") hide (effects (font (size 0.8 0.8) (thickness 0.12))))',
           f'    (fp_rect (start {-w/2:.3f} {-h/2:.3f}) (end {w/2:.3f} {h/2:.3f}) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS"))']
    if pads:
        for num,px,py,pw,ph,netid,netname in pads:
            lines.append(f'    (pad "{num}" smd rect (at {px:.3f} {py:.3f}) (size {pw:.3f} {ph:.3f}) (layers "F.Cu" "F.Paste" "F.Mask") (net {netid} "{netname}"))')
    lines.append("  )")
    return lines


def write_main_kicad() -> None:
    base=["GND","+5V","+3V3","VBAT","HALL","TIP_A","TIP_B","TIP_C"]
    chain=[]
    for arm in "ABC": chain += [f"TOP_{arm}_{i:02d}" for i in range(16)]
    nets=base+chain
    netid={n:i+1 for i,n in enumerate(nets)}
    lines=kicad_header(nets)
    pts=mech.pcb_outline_points()[::4]
    for a,b in zip(pts,pts[1:]+pts[:1]):
        lines.append(f'  (gr_line (start {100+a[0]:.3f} {100-a[1]:.3f}) (end {100+b[0]:.3f} {100-b[1]:.3f}) (stroke (width 0.15) (type default)) (layer "Edge.Cuts"))')
    lines.append(f'  (gr_circle (center 100 100) (end {100+P["pcb_center_hole"]/2:.3f} 100) (stroke (width 0.15) (type default)) (fill none) (layer "Edge.Cuts"))')
    for sx,sy in mech.screw_positions():
        lines += fp_rect("H", "M2_NPTH",100+sx,100-sy,2.5,2.5,pads=[("",0,0,2.5,2.5,netid["GND"],"GND")])
    for ai,(arm,angle) in enumerate(zip("ABC",(0,120,240)),start=1):
        for i in range(15):
            r=P["led_radial_start"]+i*P["led_pitch"]; x,y=mech.polar(r,angle)
            din=f"TOP_{arm}_{i:02d}"; dout=f"TOP_{arm}_{i+1:02d}"
            pads=[("1",-.6,-.6,.55,.55,netid["+5V"],"+5V"),("2",.6,-.6,.55,.55,netid[dout],dout),
                  ("3",.6,.6,.55,.55,netid["GND"],"GND"),("4",-.6,.6,.55,.55,netid[din],din)]
            lines += fp_rect(f"D{ai}{i+1:02d}","RGB_2020_ADDR",100+x,100-y,1.9,1.9,-angle,pads)
        x,y=mech.polar(46,angle)
        pads=[("1",0,-2.4,.8,.9,netid["+5V"],"+5V"),("2",0,-.8,.8,.9,netid["GND"],"GND"),
              ("3",0,.8,.8,.9,netid[f"TOP_{arm}_15"],f"TOP_{arm}_15"),("4",0,2.4,.8,.9,netid[f"TIP_{arm}"],f"TIP_{arm}")]
        lines += fp_rect(f"JTIP{arm}","TIP_BOARD_4PAD",100+x,100-y,2.2,7,-angle,pads)
    lines += fp_rect("U1","NRF52840_QFN_WLCSP_TBD",120,95,7,7,0,[])
    lines += fp_rect("ANT1","BLE_ANTENNA_KEEP_OUT",139,95,8,2.4,0,[])
    lines += fp_rect("U2","LIPO_CHARGER_PROTECT_TBD",86,78,9,7,-120,[])
    lines += fp_rect("U3","BOOST_5V_1P5A_TBD",86,122,9,7,-240,[])
    lines.append("  (gr_text \"PLACEMENT MOCKUP - DO NOT FABRICATE\" (at 100 151) (layer \"F.SilkS\") (effects (font (size 1.2 1.2) (thickness 0.2))))")
    lines.append(")")
    (OUT/"ticker_spinner_v0_2_main_board_mockup.kicad_pcb").write_text("\n".join(lines),encoding="utf-8")


def write_tip_kicad() -> None:
    nets=["GND","+5V","DIN","DOUT"]+[f"PIX_{i:02d}" for i in range(1,12)]
    netid={n:i+1 for i,n in enumerate(nets)}
    lines=kicad_header(nets)
    w,h=P["tip_board_width"],P["tip_board_height"]; cx,cy=100,100
    corners=[(cx-w/2,cy-h/2),(cx+w/2,cy-h/2),(cx+w/2,cy+h/2),(cx-w/2,cy+h/2)]
    for a,b in zip(corners,corners[1:]+corners[:1]):
        lines.append(f'  (gr_line (start {a[0]:.3f} {a[1]:.3f}) (end {b[0]:.3f} {b[1]:.3f}) (stroke (width 0.15) (type default)) (layer "Edge.Cuts"))')
    for i in range(12):
        yy=cy-(P["side_led_z_start"]+i*P["side_led_z_pitch"]-P["assembled_thickness"]/2)
        din="DIN" if i==0 else f"PIX_{i:02d}"; dout="DOUT" if i==11 else f"PIX_{i+1:02d}"
        pads=[("1",-.30,-.30,.28,.28,netid["+5V"],"+5V"),("2",.30,-.30,.28,.28,netid[dout],dout),
              ("3",.30,.30,.28,.28,netid["GND"],"GND"),("4",-.30,.30,.28,.28,netid[din],din)]
        lines += fp_rect(f"TD{i+1}","WS2812B_0909_TBD",cx,yy,.9,.9,0,pads)
    conpads=[]
    for num,(name,x) in enumerate(zip(("+5V","GND","DIN","DOUT"),(-2.4,-.8,.8,2.4)),start=1):
        conpads.append((str(num),x,0,.9,1.1,netid[name],name))
    lines += fp_rect("J1","MAIN_BOARD_4PAD",cx,cy+h/2-.7,6.0,1.4,0,conpads)
    lines.append("  (gr_text \"TIP 12PX v0.2 - VERIFY 0909 FOOTPRINT\" (at 100 109) (layer \"F.SilkS\") (effects (font (size 0.65 0.65) (thickness 0.1))))")
    lines.append(")")
    (OUT/"ticker_spinner_v0_2_tip_board_mockup.kicad_pcb").write_text("\n".join(lines),encoding="utf-8")


def write_bom_and_pinmap() -> None:
    rows=[
        ["D1-D45",45,"Addressable RGB 2020","Top POV pixels","Footprint/protocol TBD"],
        ["TD1-TD12",36,"WS2812B-0909 compatible","12 per tip board × 3","Verify exact manufacturer footprint"],
        ["U1",1,"nRF52840 module","BLE + timing","Module selection TBD; antenna keep-out required"],
        ["U2",1,"1S LiPo charger/protection","Battery management","Topology TBD"],
        ["U3",1,"5 V boost, ≥1.5 A pulsed","LED supply","Current limit and thermal test required"],
        ["H1",1,"Digital Hall sensor","One index pulse/revolution","3.3 V type TBD"],
        ["JTIP-A/B/C",3,"4-pad board interface","5V/GND/DIN/DOUT","Solder tabs or 0.5 mm FPC TBD"],
        ["Cbulk",3,"47-100 µF low-profile","One per arm","Size TBD"],
    ]
    with (OUT/"ticker_spinner_v0_2_preliminary_bom.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["References","Qty total","Part class","Function","Status"]); w.writerows(rows)
    pinmap={"tip_board":{"1":"+5V","2":"GND","3":"DIN from main board","4":"DOUT / return-test"},
            "architecture":"Three independently phase-addressed 12-pixel tip chains",
            "warning":"Draft allocation only; verify logic levels, connector order and footprints before fabrication."}
    (OUT/"ticker_spinner_v0_2_pinmap.json").write_text(json.dumps(pinmap,indent=2),encoding="utf-8")


def main() -> None:
    draw_mockup(); write_main_kicad(); write_tip_kicad(); write_bom_and_pinmap()
    shutil.copy2(__file__, OUT / "generate_pcb_mockup_v0_2.py")


if __name__ == "__main__":
    main()
