"""把 AI 原图裁掉右下角的生成水印，统一成干净素材。

用法：python scripts/crop_assets.py
输入：assets/gen/*.png（原图，保留不动）
输出：assets/src/*.png（裁好的，供排版用）
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "gen"
OUT = ROOT / "assets" / "src"
OUT.mkdir(parents=True, exist_ok=True)

# 水印 "AI生成 / WORKBUDDY" 占右下角，图高 1536 时约在 y>=1478、x>=930
NAMES = {
    "hero": "博物馆级静物摄影_一只云南鹤庆瓦猫_青灰色素胎陶塑_头部明显_2026-11-15T03-40-46.png",
    "craft": "静物摄影_一只青灰色素胎的云南瓦猫陶塑放在深灰色粗麻布上_头_2026-11-15T03-41-15.png",
    "future": "概念设计摄影_一只青灰色素胎瓦猫蹲踞在现代城市高楼设备层的女_2026-11-15T03-41-37.png",
    "product": "产品设计摄影_三件陶制器物并置在浅灰色石台上__最左是一只小_2026-11-15T03-42-21.png",
}

for key, name in NAMES.items():
    src = SRC / name
    if not src.exists():
        raise SystemExit(f"缺图：{src}")
    im = Image.open(src).convert("RGB")
    w, h = im.size
    cut = 70 if h > 1200 else 56
    out = im.crop((0, 0, w, h - cut))
    dst = OUT / f"{key}.png"
    out.save(dst, dpi=(300, 300))
    print(f"{key}: {w}x{h} -> {out.size[0]}x{out.size[1]}  {dst.name}")
