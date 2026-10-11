# L001 · 경쟁사 가격·평점 자동 수집기

매장 페이지의 상품 제목·가격·평점·재고를 모아 날짜별로 저장하고, 직전 수집과 비교해 리포트를 만듭니다. API 키·AI 모델 없이 동작합니다.
영상 실행 환경: 2026-10-10 · macOS · 파이썬 3.12.7 · crawl4ai 0.9.4

## 먼저 확인
crawl4ai 는 **파이썬 3.10 이상**이 필요합니다.
```bash
python3 --version
```
맥 기본 파이썬(3.9)이라면, L002 에서 쓴 uv 로 새 파이썬을 설치할 수 있습니다: `uv python install 3.12`

## 따라 하기 (이 폴더에서)

```bash
python3 -m venv .venv && .venv/bin/pip install crawl4ai
.venv/bin/crawl4ai-setup
.venv/bin/python monitor.py run
```

- 수집 결과: `data/snapshots/`, 리포트: `reports/`
- 두 수집본만 비교: `.venv/bin/python monitor.py diff A.json B.json`

매일 아침 7시 자동 실행 (cron 설정 예시):
```
0 7 * * * cd /path/to/tool && .venv/bin/python monitor.py run
```

## 대상 바꾸기
- 매장 목록은 `targets.json`. 영상의 대상은 스크래핑 연습용 공개 사이트(books.toscrape.com)입니다.
- 매장 구조가 다르면 `monitor.py` 의 `SCHEMAS` 에 선택자 규칙을 추가합니다.
- **실제 쇼핑몰에 쓰기 전에 robots.txt 와 이용약관을 꼭 확인하세요.** 로그인·개인정보·결제가 걸린 페이지는 대상으로 삼지 마세요.
