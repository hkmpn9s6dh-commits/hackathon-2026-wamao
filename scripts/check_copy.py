"""创作说明字数闸：赛事要求 100–300 字（中文按字符计，标点计入，英文/数字按字符计）。

只量 submission/设计说明.md 的正文（去掉标题行、空行与小标题）。用法：python scripts/check_copy.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "submission" / "设计说明.md"
if not p.exists():
    print(f"✗ 缺 {p}")
    sys.exit(1)

text = p.read_text(encoding="utf-8")
# 去掉 markdown 标题行、引用行与空行，剩下的才是要投稿的正文
body = "\n".join(
    line for line in text.splitlines()
    if line.strip() and not line.startswith("#") and not line.startswith(">")
)
body = re.sub(r"\s+", "", body)
n = len(body)

lo, hi = 100, 300
print(f"创作说明正文：{n} 字（要求 {lo}–{hi}）")
if not (lo <= n <= hi):
    print("✗ 字数不合格")
    sys.exit(1)
print("✓ 字数合格")
