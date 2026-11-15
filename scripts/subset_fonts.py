"""把随包的 OFL 字体裁成"只留用到的字"，并核对没有漏字。

为什么不用整套字体：Noto Serif SC / Sans SC 全量各 17–25 MB，仓库和 Pages 都吃不消。
为什么必须核对：缺字会**静默**回落到系统字体，页面照样出图，但字形已经变了。

用法：python scripts/subset_fonts.py
产出：assets/fonts/*.subset.ttf + 控制台核对结果（缺字则退出 1）
"""
import glob
import re
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"

# 1) 收集版式里出现的所有字符
chars = set()
for p in glob.glob(str(ROOT / "src" / "*.html")):
    txt = Path(p).read_text(encoding="utf-8")
    txt = re.sub(r"<style[\s\S]*?</style>", "", txt)
    txt = re.sub(r"<[^>]+>", "", txt)
    chars |= {c for c in txt if not c.isspace()}
chars |= set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
             "·—–…“”‘’《》〈〉「」『』、，。；：？！（）%×/+-=.·#")
print(f"版式用字 {len(chars)} 个")

PAIRS = [("NotoSerifSC-VF.ttf", "NotoSerifSC-subset.ttf"),
         ("NotoSansSC-VF.ttf", "NotoSansSC-subset.ttf")]

missing_all = []
for src_name, out_name in PAIRS:
    src = FONTS / src_name
    out = FONTS / out_name

    # 全新 clone 里只有子集、没有源字体：那就只核对覆盖，不再生成
    if not src.exists():
        if not out.exists():
            print(f"✗ 源字体与子集都不在：{src_name} / {out_name}")
            sys.exit(1)
        f = TTFont(out, lazy=True)
        cm = set()
        for t in f["cmap"].tables:
            cm |= set(t.cmap.keys())
        miss = sorted(c for c in chars if ord(c) not in cm)
        if miss:
            print(f"✗ {out_name} 缺字：{''.join(miss)}")
            sys.exit(1)
        print(f"{out_name}: {out.stat().st_size/1024:.0f} KB（源字体不在本仓库，跳过再生成，覆盖核对通过）")
        continue

    # 2) 核对覆盖：源字体里有没有这些字
    font = TTFont(src, lazy=True)
    cmap = set()
    for table in font["cmap"].tables:
        cmap |= set(table.cmap.keys())
    missing = sorted(c for c in chars if ord(c) not in cmap)
    if missing:
        missing_all.append((src_name, "".join(missing)))

    # 3) 子集化
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    opts.recalc_bounds = True
    s = subset.Subsetter(options=opts)
    s.populate(text="".join(sorted(chars)))
    f2 = TTFont(src)
    s.subset(f2)
    f2.save(out)
    print(f"{out_name}: {out.stat().st_size/1024:.0f} KB")

if missing_all:
    for name, miss in missing_all:
        print(f"✗ {name} 缺字：{miss}")
    sys.exit(1)
print("✓ 两个子集都覆盖了版式里出现的全部字符")
