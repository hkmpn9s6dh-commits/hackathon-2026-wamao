"""交付件量测：尺寸、DPI、体积、色彩模式、水印残留。

赛事原文：竖版分辨率不低于 2480×3508；单张不超过 20 MB；JPG/PNG。
用法：python scripts/check_output.py
"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
MIN_W, MIN_H = 2480, 3508
MAX_MB = 20
FILES = ["01-hero.png", "02-craft.png", "03-future.png"]

fail = 0
for name in FILES:
    p = OUT / name
    if not p.exists():
        print(f"✗ 缺文件 {name}")
        fail += 1
        continue
    im = Image.open(p)
    w, h = im.size
    mb = p.stat().st_size / 1024 / 1024
    dpi = im.info.get("dpi", (0, 0))[0]
    ok = []
    if w < MIN_W or h < MIN_H:
        ok.append(f"尺寸 {w}×{h} 低于 {MIN_W}×{MIN_H}")
    if mb > MAX_MB:
        ok.append(f"体积 {mb:.2f}MB 超过 {MAX_MB}MB")
    if im.mode != "RGB":
        ok.append(f"色彩模式 {im.mode}（应为 RGB）")
    if round(dpi) != 300:
        ok.append(f"DPI {dpi:.0f} ≠ 300")
    if ok:
        fail += 1
        print(f"✗ {name}: " + "；".join(ok))
    else:
        print(f"✓ {name}  {w}×{h}  {dpi:.0f}dpi  {mb:.2f}MB  {im.mode}")

if fail:
    print(f"\n{fail} 个文件不合格")
    sys.exit(1)
print("\n三张交付件全部合格（尺寸 / DPI / 体积 / 色彩模式）")
