#!/usr/bin/env python3
"""Publish an allowlisted research package; retire obsolete files recoverably."""
from pathlib import Path
import json
import re
import shutil
import subprocess
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
public = ROOT / "public"
backup = ROOT / "tmp/retired-before-b01"
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
# Resolve the exact scoped targets first. Untracked old duplicate downloads are
# also moved out of public/, so the static build cannot publish them accidentally.
def obsolete(name):
    if name.startswith("public/project-files/"):
        return bool(re.search(r"v0[_.][1245]|electronics-v0\.[45]|critique_assessment|v0_3_(complete_package|partner_brief)", name))
    return name in ("tools/generate_electronics_v0_4.py", "tools/generate_schematic_v0_5.py", "tools/generate_schematic_v0_5 2.py")

targets = sorted(set(n for n in tracked if n and obsolete(n)) |
                 {str(p.relative_to(ROOT)) for p in (public / "project-files").rglob("*") if p.is_file() and obsolete(str(p.relative_to(ROOT)))})
for name in targets:
    src, dst = ROOT / name, backup / name
    if not src.exists():
        continue
    if dst.exists():
        raise RuntimeError(f"Backup already exists: {name}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
backup.mkdir(parents=True, exist_ok=True)
(backup / "manifest.json").write_text(json.dumps(targets, ensure_ascii=False, indent=2))
print(f"Retired {len(targets)} obsolete files; recoverable backup: {backup}")

bench = ROOT / "bench/v0.1"
dest = public / "project-files/bench-b0.1"
dest.mkdir(parents=True, exist_ok=True)
for name in ("shopping.md", "wiring.html", "wiring.json", "schematic.svg", "photodiode.svg", "README.md", "test_record.md"):
    shutil.copy2(bench / name, dest / name)
shutil.copy2(bench / "output/pdf/SmartSpinner_B01_Bench.pdf", dest / "SmartSpinner_B01_Bench.pdf")
# Keep relative PDF links in the original wiring page valid as well.
(dest / "output/pdf").mkdir(parents=True, exist_ok=True)
shutil.copy2(bench / "output/pdf/SmartSpinner_B01_Bench.pdf", dest / "output/pdf/SmartSpinner_B01_Bench.pdf")
shutil.copy2(ROOT / "bench/SmartSpinner_B01_DIY_Package.zip", public / "project-files/SmartSpinner_B01_DIY_Package.zip")

photos = {
    "20260929_230431.jpg": "led-ruler.jpg",
    "20260929_230621.jpg": "driver-sm16306sj.jpg",
    "7ac3c3a2-673b-4f86-bc84-44e7bbdeeb4e.jpeg": "led-closeup.jpg",
}
gallery = public / "assets/reference-fan"
gallery.mkdir(parents=True, exist_ok=True)
for source, target in photos.items():
    with Image.open(Path.home() / "Downloads" / source) as photo:
        # Only publishing hygiene: orientation normalization and removal of EXIF,
        # GPS and other source metadata. Do not alter the depicted hardware.
        normalized = ImageOps.exif_transpose(photo).convert("RGB")
        normalized.save(gallery / target, quality=94)
        with Image.open(gallery / target) as check:
            assert not check.getexif()
    print(f"Prepared real reference photo: {target}")
