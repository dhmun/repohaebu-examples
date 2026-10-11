# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["markitdown[all]>=0.1.8"]
# ///
"""폴더 안 문서를 전부 글자(.md)로 바꿔 '결과' 폴더에 모읍니다.
쓰는 법:  uv run convert_all.py 문서폴더
"""
import sys, time, csv
from pathlib import Path
from markitdown import MarkItDown

src = Path(sys.argv[1] if len(sys.argv) > 1 else ".")   # 바꿀 문서가 든 폴더
out = Path("결과"); out.mkdir(exist_ok=True)             # 결과를 모을 폴더
md = MarkItDown()
rows, start = [], time.time()

for f in sorted(p for p in src.rglob("*") if p.is_file()):
    t = time.time()
    try:
        text = md.convert(str(f)).text_content.strip()
        state = "성공" if text else "빈 결과"
        (out / (f.name + ".md")).write_text(text, encoding="utf-8")
    except Exception as e:
        text, state = "", "실패"
    mark = {"성공": "✅", "빈 결과": "⚠️", "실패": "❌"}[state]
    print(f"{mark} {f.name}  ({len(text)}자)")
    rows.append([f.name, f.suffix.lower(), f.stat().st_size, state, len(text), round(time.time() - t, 2)])

with open("결과표.csv", "w", newline="", encoding="utf-8-sig") as fp:   # 엑셀에서 바로 열리게
    csv.writer(fp).writerows([["파일", "형식", "크기", "상태", "글자 수", "초"]] + rows)
n = {s: sum(r[3] == s for r in rows) for s in ("성공", "빈 결과", "실패")}
print(f"\n총 {len(rows)}개 · 성공 {n['성공']} · 빈 결과 {n['빈 결과']} · 실패 {n['실패']} · {time.time() - start:.1f}초")
