# NESDC XLS 파싱 완성 및 데이터 수집 검증 계획

현재 PollAgg 프로젝트는 중앙선거여론조사심의위원회(NESDC)의 주간 주요 데이터(XLS)를 파싱하여 지지율 데이터를 수집하는 단계에 있습니다. `task.md`에 따르면 이 작업이 미완료 상태이며, 로컬 테스트 결과 날짜 파싱 로직에서 보완이 필요한 점을 확인했습니다.

## 주요 목표
1.  **날짜 파싱 로직 강화**: `26.01.02.~03.` 또는 `25.12.31./26.01.02.`와 같은 비정형 날짜 범위를 정확한 종료일(YYYY-MM-DD)로 변환합니다.
2.  **XLS 파싱 로직 통합 및 검증**: `nesdc_scraper.py`의 XLS 파싱 기능을 실제 데이터에 맞게 최적화하고, `ingestor.py`를 통해 DB에 정상적으로 저장되는지 확인합니다.
3.  **대시보드 시각화 확인**: 수집된 데이터가 Next.js 대시보드에서 정상적으로 차트로 표시되는지 검증합니다.

## 제안된 변경 사항

### 1. [nesdc_scraper.py](file:///Users/up_main/Desktop/T_Antigravity/PollAgg/pipeline/collectors/nesdc_scraper.py) 수정
-   `_extract_end_date` 메서드를 개선하여 날짜 범위(시작일~종료일)에서 연도와 월이 생략된 종료일을 처리할 수 있도록 합니다.
-   `_normalize_date`에서 `YY.MM.DD` 형식을 `20YY-MM-DD`로 변환하는 로직을 보강합니다.
-   `_download_and_parse_weekly_xls`에서 `_extract_end_date`를 호출하도록 수정하여 코드 중복을 제거하고 정확도를 높입니다.

### 2. [ingestor.py](file:///Users/up_main/Desktop/T_Antigravity/PollAgg/pipeline/ingestor.py) 검증
-   `config.json`을 업데이트하여 NESDC 수집기를 활성화하고 `use_weekly_xls` 옵션을 테스트합니다.
-   로컬에 저장된 `nesdc_test.xlsx`를 사용하여 수동 인젝션 테스트를 수행하는 스크립트를 작성합니다.

### 3. [task.md](file:///Users/up_main/Desktop/T_Antigravity/PollAgg/docs/task.md) 업데이트
-   완료된 작업을 체크하고 다음 단계(스케줄러 연동 등)를 명확히 합니다.

## 검증 계획

### 자동화 테스트
-   다양한 날짜 문자열에 대한 유닛 테스트 수행:
    -   `26.01.02.~03.` -> `2026-01-03`
    -   `25.12.31./26.01.02.` -> `2026-01-02`
    -   `2026.04.15.` -> `2026-04-15`

### 수동 검증
1.  `pipeline/run_ingestor.py` (임시)를 실행하여 `nesdc_test.xlsx` 데이터를 DB에 로드합니다.
2.  `http://localhost:8002/api/data` 엔드포인트에서 데이터가 추가되었는지 확인합니다.
3.  `http://localhost:3000/dashboard`에서 차트가 정상적으로 렌더링되는지 확인합니다.

## 사용자 확인 필요 사항
-   정당명(results의 키)을 한국어 원문 그대로 사용할지, 아니면 표준 키(예: `party_democratic`)로 변환할지 확정이 필요합니다. (현재 프런트엔드는 동적 키를 지원하므로 한국어 유지가 가능합니다.)
-   `nesdc_test.xlsx` 외에 다른 형식의 XLS 파일도 존재하는지 확인이 필요합니다.
