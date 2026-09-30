#!/usr/bin/env python3
"""Run reproducible software checks, then package only bench-owned files."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone

root=Path(__file__).resolve().parents[1]
log=['SmartSpinner B0.1 software verification',
     'Timestamp: '+datetime.now(timezone.utc).isoformat(),
     'HARDWARE TESTS: NOT PERFORMED. No motor, battery or PCB production qualification.']
def run(args):
    r=subprocess.run(args,cwd=root,capture_output=True,text=True)
    log.extend(['$ '+' '.join(args),r.stdout,r.stderr,f'Exit: {r.returncode}'])
    if r.returncode:
        (root/'build').mkdir(exist_ok=True)
        (root/'build/verification.txt').write_text('\n'.join(log))
        raise SystemExit(r.returncode)
run(['arduino-cli','version'])
run(['arduino-cli','core','list'])
run(['arduino-cli','compile','--fqbn','arduino:avr:uno','--output-dir','build/uno','firmware/spinner_bench'])
with tempfile.TemporaryDirectory(prefix='spinner-bench-test-') as tmp:
    exe=str(Path(tmp)/'test_core')
    run(['c++','-std=c++11','-Wall','-Wextra','-Werror','tests/test_core.cpp','-o',exe])
    run([exe])
run([sys.executable,'tools/verify_wiring.py'])
(root/'build/verification.txt').write_text('\n'.join(log)+'\n')

# Explicit allowlist avoids copying unrelated workspace data or credentials.
files=[root/name for name in ['README.md','manual.md','shopping.md','test_record.md',
                              'wiring.json','wiring.html','schematic.svg','photodiode.svg',
                              'build/verification.txt','build/uno/spinner_bench.ino.hex',
                              'output/pdf/SmartSpinner_B01_Bench.pdf']]
for directory in ['firmware','tests','tools']:
    files += [p for p in (root/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
(root/'SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
files.append(root/'SHA256.json')
archive=root.parent/'SmartSpinner_B01_DIY_Package.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files): z.write(p,'SmartSpinner_B01/'+str(p.relative_to(root)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,sha in manifest.items():
        assert hashlib.sha256(z.read('SmartSpinner_B01/'+name)).hexdigest()==sha
print('\n'.join(log))
print(f'PACKAGE VERIFIED: {archive.name}; {len(files)} files; {archive.stat().st_size} bytes')
