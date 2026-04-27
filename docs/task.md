# PollAgg Task Board

## ✅ 완료

### 인프라
- [x] FastAPI 백엔드 (`api.py`) 구현
- [x] DB 스키마 (`category` 컬럼) 수정
- [x] PM2 데몬화 (pollagg-api :8002, pollagg-frontend :3000)
- [x] Mac 부팅 자동 시작 (launchd 등록)

### 대시보드
- [x] `static/index.html` (FastAPI 내장 경량 대시보드)
- [x] Next.js 메인 대시보드 (`/dashboard`)
- [x] `PollTrendChart.tsx` 동적 키 지원 (candidate_a → 실제 키 자동 감지)

### 데이터 수집기 (pipeline/collectors/)
- [x] `base_collector.py` — 공통 인터페이스
- [x] `data_gov_kr.py` — 공공데이터포털 API (API 키 필요)
- [x] `nec_data.py` — 국가선거정보포털 (실제 개표결과, API 키 필요)
- [x] `nesdc_scraper.py` — **중앙선거여론조사심의위원회 스크래퍼 (API 키 불필요)**
  - 목록 페이지 파싱 (`a.row.tr` → `span.col` 8개 컬럼)
  - 상세 페이지 보강 (표본크기, 응답률)
  - 정규화 → PollAgg 표준 포맷 변환
  - **지지율 결과 파싱 완성**: NESDC 결과분석 XLS (주간 집계) 날짜 정규화 및 자동 추출 구현

### 파이프라인
- [x] `ingestor.py` v4 — 3개 수집기 오케스트레이션 + 중복 방지

---

## 🔲 다음 작업

### 우선순위 HIGH
- [x] **지지율 결과 파싱**: NESDC 결과분석 XLS (주요데이터 페이지 `/B0000025`)
  - 주간 집계 XLS 다운로드 → openpyxl 파싱 → `results` 필드 채우기 (완료)
- [x] **실 데이터 수집 및 DB 정제**:
  - 기존의 잘못된 날짜 데이터(MM-DD 형식 등) 삭제 및 재수집 완료 (4100+ 건)
- [x] **Alembic 마이그레이션 도입**: DB 스키마 버전 관리 및 SQLite batch 모드 설정 완료
- [x] **날짜 파싱 보강**: `MM-DD` 형식만 있는 경우 연도 추론 로직 추가 (NESDC 특성 대응 완료)
- [ ] **API 키 발급 후 실 데이터 수집 테스트**:
  - data.go.kr API 키 → `config.json`의 `data_gov_kr.api_key`
  - data.nec.go.kr API 키 → `config.json`의 `nec_data.api_key`

### 우선순위 MEDIUM
- [ ] `pipeline/runner.py` 스케줄러 연동 (6시간마다 자동 수집)
- [ ] API 엔드포인트 `/api/collect` 추가 (수동 트리거)
- [ ] `pm2 startup` launchd 등록 후 재부팅 테스트

### 우선순위 LOW
- [ ] 대시보드 실시간 업데이트 (WebSocket 또는 polling)
- [ ] 지역별 필터 UI 추가
- [ ] 오차율(표본오차) 시각화

---

## 포트 배정
| 서비스 | 포트 |
|---|---|
| PollAgg FastAPI | 8002 |
| PollAgg Next.js | 3000 |
| ground-news-kr Vite | 5175 |
