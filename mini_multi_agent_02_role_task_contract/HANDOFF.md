# 부산 알레르기 안전 안내문 실습 Handoff

최종 정리: 2026-09-29

## 1. 현재 목표와 동작

이 프로젝트는 Research → Writer → Reviewer의 역할 분리와 출력 계약,
검토 실패 후 재작성 과정을 학습하는 실습이다.
알레르기 안내문은 **두 가지 가상 시나리오의 고정 Mock 데이터**로 동작한다.

- 알레르기 Agent는 LLM, MCP 서버, PostgreSQL을 호출하지 않는다.
- 사진 업로드 및 이미지 분석 기능은 제거했다. 입력은 텍스트 요청이다.
- `LLM_MODE` 설정을 제거했다. 알레르기 Agent ID를 기준으로 Mock을 사용한다.
- 다른 Lab의 Provider 및 MCP 기능은 별도로 유지한다.
- 학습용 가상 데이터이므로 최종 안내문과 Research/Draft 계약에 출처 URL을 요구하지 않는다.
- 실제 매장 메뉴, 원재료, 날씨를 확인한 결과가 아니다.

## 2. 두 가지 요청 예시

| 구분 | 요청 | 장소 | 추천 메뉴 |
| --- | --- | --- | --- |
| 해운대 | 부산에서 바다 근처 가볼 만한 장소와 음식도 추천해 줘. | 해운대해수욕장, 동백섬 산책로 | 물회, 밀면 |
| 광안리 | 부산 광안리에서 산책할 장소와 먹을 만한 음식을 추천해 줘. | 광안리해수욕장, 민락수변공원 | 해물파전, 어묵 |

음식별 알레르기 유발 의심 원재료도 고정 데이터로 제공한다.

- 물회: 생선, 조개류, 양념의 대두·밀 성분
- 밀면: 밀, 달걀, 육수의 대두 성분
- 해물파전: 밀, 달걀, 새우·조개류
- 어묵: 생선, 밀, 대두

이 목록은 메뉴별 추정 예시다. 실제 원재료와 교차접촉 가능성을
주문 전에 매장에 직접 확인하도록 안내한다.

## 3. 최종 안내문 구성

긴 한 문단 대신 제목과 짧은 항목, 음식별 목록으로 표시한다.

1. 제목과 `가상 실습 예시` 표시
2. 가볼 곳
3. 햇볕 주의: `12~15시에 햇볕이 강한 날에는 장시간 물놀이를 피하고 그늘에서 쉬세요.`
4. 추천 음식과 알레르기 유발 의심 원재료
5. 주문 전 실제 원재료 및 교차접촉 확인
6. 중증 알레르기 증상이 의심되면 119 신고 안내
7. 사용 전 사용자 확인·승인 문구

햇볕 주의 문구는 실습용 조건부 안내이며 실시간 일조량 판정이 아니다.
사진을 요청하는 문구와 출처 링크 목록은 표시하지 않는다.

## 4. 실행 흐름과 계약

```text
텍스트 요청
 → Research: Mock 장소·음식·안전 수칙 조회
 → Research 계약 검증
 → Writer: 안내문 작성
 → Draft 계약 검증
 → Reviewer: 필수 조건 확인
   ├─ 실패: 피드백을 Writer에 전달하여 재작성
   └─ 통과: 최종 안내문과 실행 기록 반환
```

- 정상 예시는 1차 초안에서 응급 안내를 의도적으로 누락한다.
- Reviewer가 누락을 찾으면 2차 초안에 119 신고 문구를 추가해 통과한다.
- 최대 작성 횟수는 3회다.
- 정상 결과: `status=completed`, `termination_reason=evaluation_passed`, `revision_count=2`.
- 필수 조건은 의심 원재료, 12~15시 안내, 교차접촉, 119 신고, 승인 문구의 5개다.
- URL 속 숫자나 단순 `119` 문자열만으로 응급 안내가 통과하지 않도록 검사한다.
- `FoodSuggestion`에 메뉴명과 의심 원재료를 구조화했다.
- Research에는 `scenario_title`, `food_suggestions`, `daytime_caution`이 포함된다.
- Research의 개별 `source`와 Draft의 `used_sources` 필드는 제거했다.
- Mock Tool의 `source: mock`은 내부 실행 메타데이터다.

## 5. 주요 파일

경로는 이 프로젝트 폴더 기준이다.

| 파일 | 역할 |
| --- | --- |
| `ASSIGNMENT_PLAN.md` | 과제 계획, 사용 방법, Mock 범위 |
| `frontend/app.py` | 두 요청 선택, 실행, 안내문 및 Agent 기록 표시 |
| `backend/app/providers/allergy_data_mock.py` | 장소·음식·수칙·검토 조건 Fixture |
| `backend/app/providers/allergy_mock.py` | Research/Writer/Reviewer 고정 응답 생성 |
| `backend/app/agents/runtime.py` | 알레르기 Agent의 Mock 분기 및 시나리오 선택 |
| `backend/app/agents/allergy_*_agent.py` | 각 Agent의 역할 정의 |
| `backend/app/schemas/allergy_contracts.py` | 입력·출력 계약 |
| `backend/app/orchestration/allergy_safety_guide.py` | 계약 검증 및 재작성 흐름 |
| `tests/test_allergy_contracts.py` | 계약 검증 테스트 |
| `tests/test_allergy_safety_guide.py` | 시나리오·재작성·외부 호출 차단 검증 |
| `tests/test_allergy_required_terms.py` | 기존 MCP 필수 문구 검사 회귀 테스트 |

## 6. 해결한 오류

- **화면 `KeyError: '12'`**: 알레르기 메뉴 이름과 분기 조건을 공통 상수로 맞췄다.
- **backend 폴더 실행 시 import 오류**: Mock Provider의 `mcp_server` import 의존성을 제거했다.
  Mock 필수 문구 검사는 backend 내부에서 수행한다.
- **URL의 119 숫자로 검토 통과**: URL을 제외하고 실제 `119 신고` 표현을 검사한다.
- **광안리 요청의 도시 추출 오류**: 부산 요청은 도시를 부산으로 설정하고,
  광안리·민락 키워드로 광안리 Fixture를 선택한다.
- **안내문 가독성**: Markdown 제목, 빈 줄, 메뉴별 목록으로 구성했다.

## 7. 실행 방법

프로젝트 루트에서 기존 가상환경을 사용한다.

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

가상환경 활성화 후 `backend` 폴더에서 실행해도 된다.

```bash
uvicorn app.main:app --reload
```

별도 터미널에서 프로젝트 루트 기준:

```bash
.venv/bin/python -m streamlit run frontend/app.py
```

화면에서 `12.부산 알레르기 · Mock 안내문`을 선택하고 요청 예시를 고른 뒤 실행한다.
알레르기 실습에는 DB나 MCP 서버를 시작할 필요가 없다.

API는 `POST /api/runs/allergy-safety-guide`이며 요청 예시는 다음과 같다.

```json
{"message": "부산 광안리에서 산책할 장소와 먹을 만한 음식을 추천해 줘."}
```

사진용 `/api/runs/allergy-safety-guide/photo` 경로는 제거되어 404를 반환한다.

## 8. 데이터베이스 작업 이력

Mock 전환 전에 기존 DB/MCP 경로도 보완했다.

- `allergy_sources` 출처 테이블과 안전 지침의 출처 연결 컬럼을 추가했다.
- `travel_queries.py`는 기존 DB 조회 시 출처 메타데이터를 함께 반환한다.
- `quality_requirements`에 검사 유형을 추가했다.
- 당시 로컬 DB 초기화를 두 차례 실행하여 중복 적재 없이
  출처 3건, 안전 지침 3건, 품질 조건 4건을 확인했다.
- 이 DB 데이터와 MCP 코드는 보존했다. 현재 알레르기 안내문은 이를 조회하지 않는다.
- 현재 Mock 품질 조건은 5개이므로 기존 DB의 4개와 다르다.
- 위 건수는 이전 적재 당시 기록이며 이번 문서 정리에서 DB를 다시 조회하지 않았다.

`.env`는 사용자가 직접 수정한 로컬 설정이며 Git 커밋 대상에서 제외한다.
`.env.example`은 공유용 예시다. DB를 다시 사용하는 경우 backend와 MCP의
DB 접속 설정 및 비밀번호를 별도로 확인해야 한다.

## 9. 검증 기록

최근 구현 검증:

- `python -m unittest discover -s tests -q`: 40개 테스트 통과
- `python -m compileall -q backend frontend tests`: 통과
- `git diff --check`: 통과
- backend 작업 디렉터리에서 TestClient로 두 요청 모두 HTTP 200,
  `completed`, 작성 2회 확인
- 사진 경로 404 및 Research 개별 출처 필드 제거 확인
- 테스트에서 외부 LLM/MCP/DB 호출 없이 Mock 흐름이 실행되는지 확인

브라우저 화면의 수동 시각 검증과 실제 LLM 호출 검증은 수행하지 않았다.

## 10. 다음 작업 시 주의사항

- 현재 범위는 두 고정 시나리오다. 자유 입력을 이해하는 LLM 추천 기능이 아니다.
- 광안리 또는 민락 키워드가 있으면 광안리, 그 외 기본 시나리오는 해운대다.
- Reviewer의 필수 문구 검사는 규칙 기반이다. `unsupported_claims`의 빈 목록이
  실제 사실 검증이나 의료적 안전성 검증을 뜻하지 않는다.
- 실습 데이터를 바꿀 때 Fixture, 계약, 검토 조건, 테스트, `ASSIGNMENT_PLAN.md`를 함께 맞춘다.
- 사용자가 요청한 Mock 전용 범위와 사진 기능 제거를 유지한다.
