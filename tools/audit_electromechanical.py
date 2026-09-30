#!/usr/bin/env python3
"""Compare existing PCB edges with actual mechanical STEP solids, without editing them."""
import json
import math
from pathlib import Path
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from audit_electronics import ROOT, OUT, BOARDS, parse_sexpr, child, children

def vol(shape):
    return sum(s.Volume() for s in shape.val().Solids())

def main():
    src=ROOT/'public/project-files'
    b=parse_sexpr(BOARDS['main'].read_text())
    pts=[(float(child(g,'start')[1])-100,100-float(child(g,'start')[2])) for g in children(b,'gr_line') if child(g,'layer')[1]=='Edge.Cuts']
    pcb=cq.Workplane('XY',origin=(0,0,6.5)).polyline(pts).close().extrude(1)
    pcb=pcb.cut(cq.Workplane('XY',origin=(0,0,6.4)).circle(11.6).extrude(1.2))
    inv=json.loads((OUT/'pcb-inventory.json').read_text())['main']['footprints']
    holes=[]
    for f in inv:
        if f['ref'].startswith('H'):
            x,y=float(f['at'][1])-100,100-float(f['at'][2])
            holes.append((x,y))
            pcb=pcb.cut(cq.Workplane('XY',origin=(x,y,6.4)).circle(1.2).extrude(1.2))
    bottom=cq.importers.importStep(str(src/'ticker_spinner_v0_3_bottom.step'))
    env=cq.importers.importStep(str(src/'ticker_spinner_v0_3_pcb_envelope.step')).translate((0,0,6.5))
    screws=[(30*math.cos(a)-5.3*math.sin(a),30*math.sin(a)+5.3*math.cos(a)) for a in [i*math.pi/2 for i in range(4)]]
    metrics={'pcb_v04_volume_mm3':vol(pcb),'pcb_v04_intersection_bottom_v03_mm3':vol(pcb.intersect(bottom)),
             'pcb_v03_envelope_intersection_bottom_v03_mm3':vol(env.intersect(bottom)),
             'pcb_v04_outside_v03_envelope_mm3':vol(pcb.cut(env)),
             'pcb_v04_holes_xy_mm':holes,'case_v03_screws_xy_mm':screws,
             'top_led_lateral_offset_mm':3,'top_window_half_width_mm':1.2,
             'top_led_first_radius_v04_mm':13.2,'top_led_first_radius_v03_mm':14.8,
             'tip_led_pitch_v04_mm':1.1,'tip_window_pitch_v03_mm':1.05,
             'tip_row_span_difference_mm':11*(1.1-1.05),
             'assumptions':'KiCad center (100,100) mapped to CAD (0,0), y flipped. PCB z=6.5..7.5 per v0.3; use existing STEP solids.'}
    (OUT/'mechanical-comparison.json').write_text(json.dumps(metrics,indent=2)+'\n')
    fig,ax=plt.subplots(figsize=(9,9))
    for wire in env.val().Wires():
        if all(abs(v.Z-6.5)<1e-3 for v in wire.Vertices()):
            samples,_=wire.sample(500)
            ax.plot([p.x for p in samples],[p.y for p in samples],color='#187b52',lw=1.5)
    ax.plot([p[0] for p in pts]+[pts[0][0]],[p[1] for p in pts]+[pts[0][1]],color='#b3322a',lw=1.8,label='v0.4 PCB edge')
    ax.plot([],[],color='#187b52',lw=1.5,label='v0.3 CAD PCB envelope')
    for x,y in screws: ax.add_patch(Circle((x,y),2.5,fill=False,color='#187b52'))
    for x,y in holes: ax.add_patch(Circle((x,y),1.2,fill=False,color='#b3322a'))
    ax.scatter(*zip(*screws),c='#187b52',marker='+',s=55,label='Case screw bosses')
    ax.scatter(*zip(*holes),c='#b3322a',marker='x',s=40,label='PCB mounting holes')
    led=[]
    for f in inv:
        if f['ref'].startswith('D'):
            led.append((float(f['at'][1])-100,100-float(f['at'][2])))
    ax.scatter(*zip(*led),c='#245abd',s=8,label='Actual top LED centers')
    for angle in (0,90,180,270):
        a=math.radians(angle)
        points=[(r*math.cos(a)-t*math.sin(a),r*math.sin(a)+t*math.cos(a)) for r,t in [(13.4,-1.2),(46.3,-1.2),(46.3,1.2),(13.4,1.2),(13.4,-1.2)]]
        ax.plot(*zip(*points),color='#e29313',lw=1.1)
    ax.plot([],[],color='#e29313',label='Case top windows (rectangular extent)')
    ax.set(xlim=(-53,53),ylim=(-53,53),xlabel='X, mm',ylabel='Y, mm',title='SmartSpinner: existing PCB / mechanical mismatch')
    ax.set_aspect('equal'); ax.grid(alpha=.15); ax.legend(loc='upper right',fontsize=8)
    fig.tight_layout(); fig.savefig(OUT/'pcb-mechanics-overlay.png',dpi=160); plt.close(fig)
    print(json.dumps(metrics,indent=2))

if __name__=='__main__': main()
