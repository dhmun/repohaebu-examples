#!/usr/bin/env python3
"""경쟁사 가격·평점 자동 수집기 (crawl4ai) — 매일 한 번 돌리면 아침 리포트가 쌓인다.

사용:
  python monitor.py run                  # targets.json 의 모든 매장 수집 → data/snapshots/ 저장 → 직전 수집과 비교 → reports/ 리포트
  python monitor.py diff A.json B.json   # 저장된 두 수집 결과만 비교해 변동 출력
매일 자동 실행(cron 예): 0 7 * * * cd /path/to/tool && .venv/bin/python monitor.py run

LLM·API 키 없이 동작한다 (CSS 선택자로 추출). 대상 사이트의 robots.txt·이용약관을 먼저 확인할 것.
"""
import asyncio, json, os, sys, glob, statistics
from datetime import datetime

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, JsonCssExtractionStrategy

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.join(HERE, "data", "snapshots")
REPORT_DIR = os.path.join(HERE, "reports")
STARS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

# 사이트 구조별 추출 규칙 (매장마다 다르면 여기에 하나씩 추가)
SCHEMAS = {
    "toscrape": {
        "name": "products",
        "baseSelector": "article.product_pod",
        "fields": [
            {"name": "title", "selector": "h3 a", "type": "attribute", "attribute": "title"},
            {"name": "price", "selector": "p.price_color", "type": "text"},
            {"name": "rating", "selector": "p.star-rating", "type": "attribute", "attribute": "class"},
            {"name": "stock", "selector": "p.instock.availability", "type": "text"},
        ],
    },
}


def clean(item):
    """'£51.77' → 51.77, 'star-rating Three' → 3, 공백 정리."""
    price = float("".join(ch for ch in item.get("price", "") if ch.isdigit() or ch == "."))
    cls = item.get("rating") or ""
    if isinstance(cls, list): cls = " ".join(cls)          # crawl4ai 는 class 속성을 리스트로 돌려준다
    rating = STARS.get(cls.split()[-1] if cls else "", 0)
    return {"title": item["title"].strip(), "price": price, "rating": rating,
            "in_stock": "In stock" in (item.get("stock") or "")}


async def collect(targets):
    cfg_browser = BrowserConfig(headless=True, verbose=False)
    out = {}
    async with AsyncWebCrawler(config=cfg_browser) as crawler:
        for t in targets:
            run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS,
                                       extraction_strategy=JsonCssExtractionStrategy(SCHEMAS[t["schema"]]))
            r = await crawler.arun(url=t["url"], config=run_cfg)
            if not r.success:
                print(f"  ! {t['name']}: 실패 ({r.error_message})"); out[t["name"]] = None; continue
            items = [clean(i) for i in json.loads(r.extracted_content)]
            out[t["name"]] = items
            print(f"  - {t['name']}: {len(items)} items")
    return out


def diff(old, new):
    """매장별로 가격 변동 / 신규 / 사라짐 / 평점 변동 / 재고 변동을 찾는다."""
    changes = []
    for store, items in new.items():
        if items is None or not old.get(store): continue
        before = {i["title"]: i for i in old[store]}; after = {i["title"]: i for i in items}
        for k in after.keys() - before.keys(): changes.append((store, "신규", k, "", after[k]["price"]))
        for k in before.keys() - after.keys(): changes.append((store, "사라짐", k, before[k]["price"], ""))
        for k in after.keys() & before.keys():
            a, b = before[k], after[k]
            if a["price"] != b["price"]: changes.append((store, "가격", k, a["price"], b["price"]))
            if a["rating"] != b["rating"]: changes.append((store, "평점", k, a["rating"], b["rating"]))
            if a["in_stock"] != b["in_stock"]: changes.append((store, "재고", k, a["in_stock"], b["in_stock"]))
    return changes


def summary(data):
    rows = []
    for store, items in data.items():
        if not items: rows.append((store, 0, None, None, None, None)); continue
        p = [i["price"] for i in items]
        rows.append((store, len(items), round(statistics.mean(p), 2), min(p), max(p),
                     round(statistics.mean(i["rating"] for i in items), 2)))
    return rows


def write_report(stamp, data, changes, prev_name):
    os.makedirs(REPORT_DIR, exist_ok=True)
    L = [f"# 아침 리포트 {stamp}", "", "## 매장별 요약", "",
         "| 매장 | 상품 수 | 평균가 | 최저 | 최고 | 평균 평점 |", "|---|---|---|---|---|---|"]
    for s, n, avg, lo, hi, r in summary(data):
        L.append(f"| {s} | {n} | {avg} | {lo} | {hi} | {r} |")
    L += ["", f"## 변동 (직전 수집: {prev_name or '없음'})", ""]
    if prev_name is None: L.append("첫 수집이라 비교 대상이 없습니다.")
    elif not changes: L.append("변동 없음.")
    else:
        L += ["| 매장 | 종류 | 상품 | 전 | 후 |", "|---|---|---|---|---|"]
        L += [f"| {s} | {k} | {t} | {a} | {b} |" for s, k, t, a, b in changes]
    L += ["", "## 매장별 최저가 3개", ""]
    for store, items in data.items():
        if not items: continue
        L.append(f"- **{store}**: " + ", ".join(f"{i['title']} ({i['price']})" for i in sorted(items, key=lambda i: i["price"])[:3]))
    path = os.path.join(REPORT_DIR, f"{stamp}.md")
    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return path


def print_changes(changes):
    if not changes: print("변동 없음"); return
    for s, k, t, a, b in changes: print(f"  [{k}] {s} | {t} | {a} -> {b}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "diff":
        a, b = (json.load(open(p, encoding="utf-8")) for p in sys.argv[2:4])
        print_changes(diff(a, b)); return
    targets = json.load(open(os.path.join(HERE, "targets.json"), encoding="utf-8"))
    os.makedirs(SNAP_DIR, exist_ok=True)
    prev = sorted(glob.glob(os.path.join(SNAP_DIR, "*.json")))
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    print(f"[{stamp}] 수집 시작: {len(targets)} stores")
    data = asyncio.run(collect(targets))
    json.dump(data, open(os.path.join(SNAP_DIR, f"{stamp}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    old = json.load(open(prev[-1], encoding="utf-8")) if prev else None
    changes = diff(old, data) if old else []
    print(f"비교 대상: {os.path.basename(prev[-1]) if prev else '없음 (첫 수집)'}")
    if old: print_changes(changes)
    print("리포트:", os.path.relpath(write_report(stamp, data, changes, os.path.basename(prev[-1]) if prev else None), HERE))


if __name__ == "__main__":
    main()
