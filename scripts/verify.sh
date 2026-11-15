#!/usr/bin/env bash
# 一条命令复验全部：图能重出、尺寸对、字数对。
# 用法：bash scripts/verify.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== 1/5 依赖 =="
[ -d node_modules/playwright ] || { echo "缺依赖：先跑 npm ci（或 npm i）"; exit 1; }
python -c "import PIL" 2>/dev/null || { echo "缺 pillow：pip install pillow"; exit 1; }
echo "ok"

echo "== 2/5 字体子集覆盖核对 =="
python scripts/subset_fonts.py | tail -2

echo "== 3/5 重出三张（含尺寸/安全区/溢出/压图四类断言，不过就拒绝出图）=="
node scripts/render.mjs

echo "== 4/5 打 300dpi 并量交付件 =="
python scripts/set_dpi.py
python scripts/check_output.py

echo "== 5/5 创作说明字数 =="
python scripts/check_copy.py

echo
echo "全部通过。交付件在 output/，投稿文案在 submission/。"
