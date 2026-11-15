"""把渲染出来的 PNG 打上 300dpi 标记（Playwright 默认 96dpi，A4 会变成巨幅）。

只改元数据与重编码，不改像素。用法：python scripts/set_dpi.py
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"

for p in sorted(OUT.glob("*.png")):
    im = Image.open(p)
    im.load()
    im.save(p, dpi=(300, 300), optimize=True)
    print(f"{p.name}: {im.size[0]}×{im.size[1]}  300dpi  {p.stat().st_size/1024/1024:.2f}MB")
