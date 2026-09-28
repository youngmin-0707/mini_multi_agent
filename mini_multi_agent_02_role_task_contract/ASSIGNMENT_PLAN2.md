# 부산 알레르기 안전 안내문 설계

## 1. 시나리오

### 1.1 과제 개요

| 항목 | 내용 |
| --- | --- |
| 시나리오 | 부산 알레르기 안전 안내문 |
| 사용자 요청 | 부산의 장소와 알레르기 안전 수칙을 조사하고 안내문을 작성한 뒤 필수 내용을 검토해 줘. |
| 주요 패턴 | Sequential + Evaluator–Reviser |
| 데이터 근거 | 부산 장소, 알레르기 지침, 안내문 품질 조건 |
| 최대 수정 횟수 | 3회 |
| 완료 결과 | 검토를 통과한 안내문, 출처, 사용자 승인 요청 |

이번 과제의 목표는 안내문 문장의 품질보다 Agent 연결, 검증된 Context 전달, 평가와 재작성 흐름이 올바르게 동작하도록 만드는 것이다.

### 1.2 전체 흐름

```text
사용자 요청
  → Allergy Research Agent
  → Research 출력 계약 검증
  → Allergy Guide Writer Agent
  → Draft 출력 계약 검증
  → Allergy Guide Reviewer Agent
      ├─ 통과 → 최종 안내문 반환
      └─ 실패 → 피드백과 함께 Writer 재실행
                    └─ 최대 3회까지 반복
```

### 1.3 안내문 통과 기준

Reviewer는 다음 조건을 모두 만족할 때만 안내문을 통과시킨다.

1. 장소와 알레르기 안전 지침의 출처가 포함되어 있다.
2. 방문 전에 식재료와 교차접촉 가능성을 직접 확인하도록 안내한다.
3. 중증 증상이 의심될 때 119에 신고하도록 안내한다.
4. 안내문을 게시하거나 사용하기 전에 사용자 승인을 요청한다.
5. 데이터에 없는 장소의 안전성이나 의학적 판단을 확정하지 않는다.

하나라도 충족하지 못하면 Reviewer는 `passed=false`와 함께 누락 조건과 수정 피드백을 반환한다.

## 2. agents Agent 설계

구현 위치는 다음과 같다.

```text
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\agents\
```

세 Agent는 조사, 작성, 검토를 각각 하나의 책임으로 나눈다.

| 순서 | Agent ID | 핵심 역할 | 출력 계약 | 허용 Tool |
| --- | --- | --- | --- | --- |
| 1 | `allergy_research_agent` | 장소와 안전 지침 조사 | `AllergyResearchResult` | `search_places`, `get_allergy_guidance` |
| 2 | `allergy_guide_writer_agent` | 근거 기반 안내문 작성과 수정 | `AllergyGuideDraftResult` | `get_quality_requirements` |
| 3 | `allergy_guide_reviewer_agent` | 필수 조건과 근거 검토 | `AllergyGuideReviewResult` | `check_required_terms`, `get_quality_requirements` |

### 2.1 Allergy Research Agent

**파일:** `allergy_research_agent.py`  
**Agent ID:** `allergy_research_agent`  
**목표:** Writer가 추측 없이 안내문을 작성할 수 있도록 출처가 있는 조사 자료를 준비한다.

**입력**

- 사용자의 부산 알레르기 안전 안내 요청
- `search_places`가 반환한 부산 장소 데이터
- `get_allergy_guidance`가 반환한 알레르기 안전 지침

**수행할 일**

- Tool Result에 존재하는 장소와 지침만 선택한다.
- 모든 사실과 안전 지침에 출처를 연결한다.
- 응급 상황과 관련된 지침을 구분한다.
- 결과를 `AllergyResearchResult` 구조로 반환한다.

**수행하지 않을 일**

- 안내문 초안을 작성하지 않는다.
- 특정 장소가 절대 안전하다고 판단하지 않는다.
- Tool에 없는 의학 정보나 장소 정보를 추가하지 않는다.
- Writer나 Reviewer의 결정을 대신하지 않는다.

**완료 조건:** 사실과 안전 지침이 각각 한 개 이상 존재하고 모든 항목에 출처가 있어야 한다.

### 2.2 Allergy Guide Writer Agent

**파일:** `allergy_guide_writer_agent.py`  
**Agent ID:** `allergy_guide_writer_agent`  
**목표:** 검증된 조사 자료만 사용하여 필수 안전 항목이 포함된 안내문을 작성한다.

**입력**

- 검증된 `AllergyResearchResult`
- `get_quality_requirements`가 반환한 품질 조건
- 수정 시 이전 초안과 Reviewer의 피드백
- 현재 수정 회차 `revision`

**수행할 일**

- 조사 결과에 있는 사실과 출처만 사용한다.
- 식재료·교차접촉 확인, 119 신고, 사용자 승인 요청을 반영한다.
- 실제 사용한 출처와 반영한 요구사항을 별도 필드에 기록한다.
- Reviewer의 피드백을 받은 경우 누락된 부분을 수정한다.
- 결과를 `AllergyGuideDraftResult` 구조로 반환한다.

**수행하지 않을 일**

- 조사되지 않은 장소나 안전 정보를 새로 만들지 않는다.
- 자신의 초안을 스스로 통과 처리하지 않는다.
- 예약, 연락, 게시와 같은 외부 행동을 수행하지 않는다.

**완료 조건:** 비어 있지 않은 초안, 사용 출처, 반영 요구사항 및 1~3 범위의 수정 회차가 있어야 한다.

### 2.3 Allergy Guide Reviewer Agent

**파일:** `allergy_guide_reviewer_agent.py`  
**Agent ID:** `allergy_guide_reviewer_agent`  
**목표:** 초안이 필수 조건과 조사 근거를 모두 충족하는지 독립적으로 판정한다.

**입력**

- 검증된 `AllergyResearchResult`
- 검증된 `AllergyGuideDraftResult`
- `check_required_terms`의 검사 결과
- `get_quality_requirements`의 품질 조건

**수행할 일**

- 필수 조건의 포함 여부를 항목별로 검사한다.
- 조사 자료로 뒷받침되지 않는 주장을 찾는다.
- 통과 여부, 누락 조건, 근거 없는 주장과 수정 피드백을 반환한다.
- 결과를 `AllergyGuideReviewResult` 구조로 반환한다.

**수행하지 않을 일**

- 안내문을 직접 다시 작성하지 않는다.
- 누락 사항이 있는데도 통과시키지 않는다.
- 반복 횟수나 전체 실행 종료를 결정하지 않는다.

**완료 조건:** 모든 기준을 충족하면 `passed=true`, 그렇지 않으면 `passed=false`와 구체적인 피드백을 반환해야 한다.

## 3. schema Output 계약

실제 프로젝트의 폴더명은 `schema`가 아니라 `schemas`다. 구현 위치는 다음과 같다.

```text
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\schemas\allergy_contracts.py
```

각 Agent의 응답은 해당 Pydantic 모델의 검증을 통과한 경우에만 다음 단계에서 사용할 수 있다.

### 3.1 보조 모델

| 모델 | 필드 | 의미 |
| --- | --- | --- |
| `ResearchFact` | `fact: str` | 조사된 장소 또는 관련 사실 |
|  | `source: str` | 해당 사실의 출처 |
| `SafetyGuidance` | `guidance: str` | 알레르기 안전 행동 지침 |
|  | `emergency: bool` | 응급 상황 안내 여부 |
|  | `source: str` | 해당 지침의 출처 |

### 3.2 AllergyResearchResult

**생성 Agent:** `allergy_research_agent`  
**사용 Agent:** `allergy_guide_writer_agent`

| 필드 | 자료형 | 필수 규칙 |
| --- | --- | --- |
| `agent_id` | 고정 문자열 | `allergy_research_agent`만 허용 |
| `facts` | `list[ResearchFact]` | 1~10개 |
| `safety_guidance` | `list[SafetyGuidance]` | 1~10개 |
| `completed` | `bool` | 근거가 준비된 경우에만 `true` |

검증 규칙은 다음과 같다.

- 사실과 안전 지침은 각각 한 개 이상이어야 한다.
- 각 항목의 내용과 출처는 빈 문자열일 수 없다.
- 필요한 근거 없이 `completed=true`인 결과는 거부한다.
- `completed=false`이면 Writer를 실행하지 않는다.

### 3.3 AllergyGuideDraftResult

**생성 Agent:** `allergy_guide_writer_agent`  
**사용 Agent:** `allergy_guide_reviewer_agent`

| 필드 | 자료형 | 필수 규칙 |
| --- | --- | --- |
| `agent_id` | 고정 문자열 | `allergy_guide_writer_agent`만 허용 |
| `draft` | `str` | 빈 문자열 금지 |
| `used_sources` | `list[str]` | 1~10개 |
| `included_requirements` | `list[str]` | 최대 10개 |
| `revision` | `int` | 1~3 |

검증 규칙은 다음과 같다.

- 초안과 사용 출처가 반드시 있어야 한다.
- 수정 회차는 1, 2, 3 중 하나여야 한다.
- `used_sources`는 Research 결과에 존재하는 출처여야 한다.
- 계약 통과와 내용 심사 통과는 다르며, 최종 품질은 Reviewer가 판정한다.

### 3.4 AllergyGuideReviewResult

**생성 Agent:** `allergy_guide_reviewer_agent`  
**사용 주체:** 전체 흐름을 제어하는 Orchestrator와 다음 회차의 Writer

| 필드 | 자료형 | 필수 규칙 |
| --- | --- | --- |
| `agent_id` | 고정 문자열 | `allergy_guide_reviewer_agent`만 허용 |
| `passed` | `bool` | 반드시 존재 |
| `missing_requirements` | `list[str]` | 기본값 빈 목록 |
| `unsupported_claims` | `list[str]` | 기본값 빈 목록 |
| `feedback` | `str` | 실패 시 비어 있을 수 없음 |

검증 규칙은 다음과 같다.

- `passed=true`이면 두 문제 목록이 모두 비어 있어야 한다.
- `passed=false`이면 Writer가 사용할 구체적인 피드백이 있어야 한다.
- `passed=false`이면 피드백과 함께 Writer를 다시 실행한다.

### 3.5 Agent 간 출력 전달

| 전달 구간 | 전달할 검증 결과 | 계약 위반 시 처리 |
| --- | --- | --- |
| Research → Writer | `AllergyResearchResult` | Writer를 실행하지 않음 |
| Writer → Reviewer | `AllergyGuideDraftResult` | Reviewer를 실행하지 않음 |
| Reviewer → Writer | `AllergyGuideReviewResult`의 피드백 | 해당 회차를 실패 처리 |
| Reviewer → 최종 결과 | 통과한 `AllergyGuideDraftResult` | 최종 성공 결과를 만들지 않음 |

Context는 하나의 긴 문자열로 합치지 않고, 검증된 Pydantic 모델의 `model_dump()` 결과처럼 구조화된 데이터로 전달한다.

