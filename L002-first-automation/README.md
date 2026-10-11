# L002 · 문서 정리 자동화 10분 컷

폴더 안의 PDF·워드·엑셀·파워포인트를 전부 글자(.md)로 바꿔 `결과` 폴더에 모읍니다.
영상 실행 환경: 2026-10-11 · macOS · uv 0.13.0 · markitdown 0.1.8 (파이썬 3.13 은 uv 가 자동 설치)

## 따라 하기

**① uv 설치** (설치 후 터미널을 닫았다가 다시 여세요)

맥:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
윈도우 (uv 공식 안내 명령 · 영상에서는 맥으로만 실행):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**② 이 파일 받기** — 작업할 폴더에서
```bash
curl -O https://raw.githubusercontent.com/dhmun/repohaebu-examples/main/L002-first-automation/convert_all.py
```

**③ 같은 폴더에 `문서` 폴더를 만들고 파일을 넣은 뒤**
```bash
uv run convert_all.py 문서
```

`문서` 자리에 여러분 폴더 이름을 넣으면 됩니다. 처음 한 번은 필요한 것을 내려받느라 30초쯤, 그다음부터는 몇 초면 끝납니다.

## 결과
- `결과/` — 문서마다 글자 파일 하나
- `결과표.csv` — 파일별 성공·실패·글자 수 (엑셀에서 열림)

## 알아 둘 점
- 스캔한 PDF(글자 없이 그림만 있는 PDF)는 `빈 결과`가 됩니다. 그림 속 글자를 읽으려면 OCR 이 따로 필요합니다.
- 파일 맨 위 네 줄은 지우지 마세요. 알맞은 파이썬·도구 버전을 uv 가 고르도록 하는 줄입니다.
