#!/usr/bin/env python3
"""Structural electrical checks, not a simulator or physical/ERC certification."""
from pathlib import Path
import json

p=Path(__file__).resolve().parents[1]
j=json.loads((p/'wiring.json').read_text())
nets=j['nets']; node_net={}
for name,nodes in nets.items():
    assert len(nodes)>=2, (name,'dangling named net')
    for node in nodes:
        assert node not in node_net, (node,'duplicate/short')
        node_net[node]=name

# Expected physical pins independently transcribed from Sunmoon and Kingbright.
for i in range(1,7):
    u=f'U{i}'
    assert all(f'{u}.{pin}' in node_net for pin in range(1,25)), u
    for pin,net in {1:'GND',24:'+5V_LOGIC',3:'CLK_BUS',4:'LE_BUS',21:'OE_BUS'}.items():
        assert node_net[f'{u}.{pin}']==net
    assert node_net[f'{u}.23']==node_net[f'R{i}.1']
    assert node_net[f'R{i}.2']=='GND'
    assert node_net[f'C{i}.1']=='+5V_LOGIC' and node_net[f'C{i}.2']=='GND'
    if i>1: assert node_net[f'{u}.2']==node_net[f'U{i-1}.22']
assert node_net['A1.5V']!=node_net['PS1.+']!=node_net['S2.2']
assert node_net['A1.GND']==node_net['PS1.-']=='GND'
assert node_net['S1.COM']==node_net['R11.2']=='OE_BUS'
assert node_net['S1.OFF']==node_net['R11.1']=='+5V_LOGIC'
assert node_net['S1.RUN']==node_net['R10.2']
assert node_net['R10.1']==node_net['A1.D9']
assert node_net['PD1.K']=='+5V_LOGIC' and node_net['PD1.A']==node_net['R12.1']
assert node_net['R12.2']=='GND'
assert node_net['PS1.+']==node_net['F1.1']
assert node_net['F1.2']==node_net['S2.1']
for pidx in range(32):
    d=f'D{pidx+1}'
    assert node_net[f'{d}.2']=='+5V_LED'
    for offset,pin in [(0,1),(1,4),(2,3)]:
        channel=pidx*3+offset
        u=f'U{1+channel//16}.{5+channel%16}'
        assert nets[node_net[u]]==[u,f'{d}.{pin}']
channels=[n for n in nets if n.startswith('CH_')]
assert len(channels)==96
assert len(j['pixels'])==32
print(f'PASS: {len(node_net)} nodes; all 144 driver pins accounted for; 96 unique LED channels')
print('PASS: separate positive rails, shared ground, OE switch, R_EXT and decoupling, LED polarity')
print('LIMIT: static connection checks only; no analog simulation, hardware measurements or KiCad ERC')
