#!/usr/bin/env python3
"""Read-only source audit; write fresh KiCad evidence and calculations to audits/."""
import ast
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'audits' / '2026-09-29-electronics'
CLI = '/opt/homebrew/Caskroom/kicad/10.0.6/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
SCH = ROOT / 'public/project-files/electronics-v0.5/smartspinner_main_v0_5.kicad_sch'
BOARDS = {name: ROOT / f'public/project-files/electronics-v0.4/smartspinner_{name}_v0_4.kicad_pcb' for name in ('main', 'tip')}

def parse_sexpr(text):
    root, stack = [], []
    current = root
    for token in re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', text):
        if token == '(':
            new = []
            current.append(new)
            stack.append(current)
            current = new
        elif token == ')':
            current = stack.pop()
        else:
            current.append(ast.literal_eval(token) if token.startswith('"') else token)
    assert not stack
    return root[0]

def children(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]

def child(node, key):
    return next(iter(children(node, key)), [])

def run(args):
    p = subprocess.run([CLI, *args], text=True, capture_output=True)
    return {'argv': [CLI, *args], 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = [SCH, *BOARDS.values(), ROOT / 'tools/generate_schematic_v0_5.py', ROOT / 'tools/generate_electronics_v0_4.py', ROOT / 'public/project-files/generate_ticker_spinner_v0_3.py']
    before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    jobs = [
        ['--version'],
        ['sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(OUT/'schematic.net.xml'), str(SCH)],
        ['sch', 'erc', '--severity-all', '--exit-code-violations', '-o', str(OUT/'erc.txt'), str(SCH)],
    ] + [['pcb', 'drc', '--severity-all', '--exit-code-violations', '--format', 'json', '-o', str(OUT/f'{name}-drc.json'), str(path)] for name, path in BOARDS.items()]
    with ThreadPoolExecutor(max_workers=3) as pool:
        command_results = list(pool.map(run, jobs))
    (OUT/'commands.json').write_text(json.dumps(command_results, ensure_ascii=False, indent=2)+'\n')
    if command_results[1]['returncode'] != 0:
        raise RuntimeError(command_results[1])
    net = ET.parse(OUT/'schematic.net.xml').getroot()
    pin_nets = {}
    for n in net.findall('./nets/net'):
        for p in n.findall('node'):
            pin_nets.setdefault(p.attrib['ref'], {})[p.attrib['pin']] = {'net': n.attrib['name'], 'pinfunction': p.get('pinfunction'), 'pintype': p.get('pintype')}
    components = [{'ref': c.get('ref'), 'value': c.findtext('value'), 'footprint': c.findtext('footprint')} for c in net.findall('./components/comp')]
    (OUT/'schematic-connectivity.json').write_text(json.dumps({'components': components, 'pins': pin_nets},ensure_ascii=False,indent=2)+'\n')
    boards = {}
    for name, path in BOARDS.items():
        b = parse_sexpr(path.read_text())
        footprints = []
        for fp in children(b, 'footprint'):
            props = {p[1]: p[2] for p in children(fp, 'property')}
            pads = [{'number':p[1], 'net': child(p,'net'), 'at':child(p,'at'), 'size':child(p,'size'), 'layers':child(p,'layers')} for p in children(fp,'pad')]
            footprints.append({'ref':props.get('Reference'),'value':props.get('Value'),'at':child(fp,'at'),'layer':child(fp,'layer'),'pad_count':len(pads),'pads':pads})
        counts = Counter(x[0] for x in b if isinstance(x,list) and x)
        drc = json.loads((OUT/f'{name}-drc.json').read_text())
        errors = Counter(v['type'] for k in ('violations','unconnected_items','schematic_parity') for v in drc.get(k,[]))
        boards[name] = {'object_counts':dict(counts),'drc_counts':dict(errors),'footprints':footprints}
    (OUT/'pcb-inventory.json').write_text(json.dumps(boards,ensure_ascii=False,indent=2)+'\n')
    # Optimistic protocol bound: specified reset is >80 us; ignore software overhead.
    timing = []
    for rpm in (300,600,900,1200):
        row = {'rpm':rpm,'four_arm_refresh_hz':4*rpm/60,'gyro_dps':rpm*6}
        for n in (20,12):
            t=n*24/800000+80e-6
            row[f'{n}_led_chain']={'update_us':t*1e6,'max_updates_per_revolution':math.floor(60/rpm/t),'travel_mm_at_r50':2*math.pi*50*rpm/60*t}
        row['g_at_14mm']=((rpm*2*math.pi/60)**2)*0.014/9.80665
        timing.append(row)
    # Scenario assumptions, not measurements or approved battery/LED specifications.
    power=[]
    for duty in (0,0.1,0.25,0.35,1):
        idle=128*0.0005
        led=idle+128*3*0.005*duty
        batt=5*led/(3.7*0.85)+0.015
        power.append({'mean_RGB_channel_duty':duty,'led_5V_current_A':led,'battery_3V7_current_A':batt,'runtime_500mAh_85pct_usable_min':0.5*0.85/batt*60})
    (OUT/'calculations.json').write_text(json.dumps({'assumptions':{'baud':800000,'reset_us_lower_bound':80,'led_channel_current_A':0.005,'led_idle_current_A':0.0005,'logic_battery_current_A':0.015,'boost_efficiency':0.85,'battery_capacity_Ah':0.5,'usable_capacity_fraction':0.85,'power_warning':'Illustrative sensitivity calculation, NOT verified purchased LED currents or battery specification. Duty includes spatial occupancy, brightness and active color channels. Full-white scenario exceeds the proposed supply design; runtime is mathematical, not a supported operating mode.'},'boost_intended_divider':{'upper_ohm':910000,'lower_ohm':100000,'actual_typical_reference_pwm_V':0.595,'nominal_target_pwm_V':0.595*(1+910000/100000),'nominal_target_pfm_V':0.601*(1+910000/100000),'allowed_output_setting_max_V':5.5,'warning':'Target calculation, not prediction of actual regulated output: overvoltage protection will interfere.'},'timing':timing,'power_scenarios':power},indent=2)+'\n')
    gerbers = sorted(p.name for p in (ROOT/'public/project-files/electronics-v0.4/gerber').iterdir() if p.is_file())
    (OUT/'fabrication-files.json').write_text(json.dumps({'files':gerbers,'mask_or_paste_files':[p for p in gerbers if any(s in p.lower() for s in ('mask','paste','.gts','.gbs','.gtp','.gbp'))],'warning':'File inventory only; does not validate copper/drill/placement manufacturing readiness.'},indent=2)+'\n')
    after = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    assert before == after, 'Source changed during audit'
    (OUT/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
    print(json.dumps({'sources_unchanged':True,'components':len(components),'empty_schematic_footprints':sum(not c['footprint'] for c in components),'board_counts':{k:v['object_counts'] for k,v in boards.items()},'drc':{k:v['drc_counts'] for k,v in boards.items()},'commands':[{k:x[k] for k in ('returncode','stdout','stderr')} for x in command_results],'U5':pin_nets.get('U5'),'U3':pin_nets.get('U3'),'U4':pin_nets.get('U4'),'U1':pin_nets.get('U1')},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
