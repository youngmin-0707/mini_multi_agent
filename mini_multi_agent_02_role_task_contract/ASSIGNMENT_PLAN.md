# 부산 알레르기 안전 안내문 멀티 에이전트 실습 계획

## 1. 문서 목적

이 문서는 `mini_multi_agent_01_patterns/SCENARIO.md`의 **부산 알레르기 안전 안내문** 시나리오를 `mini_multi_agent_02_role_task_contract` 프로젝트 구조에 맞게 구현하기 위한 사전 설계 문서다.

이번 실습의 핵심은 안내문의 문장 품질 자체보다 다음 항목이 코드에서 분명하게 동작하도록 만드는 것이다.

- 하나의 요청을 역할이 다른 여러 Agent로 분리한다.
- 각 Agent의 출력 형식을 Pydantic 계약으로 고정한다.
- 검증을 통과한 결과만 다음 Agent에게 전달한다.
- 작성 결과가 기준을 충족하지 못하면 피드백을 전달하여 다시 작성한다.
- 반복 횟수와 종료 조건은 Orchestrator가 결정적으로 관리한다.
- 완성한 흐름을 Router에 연결하고 Swagger에서 실행한다.

## 2. 적용 시나리오

| 항목 | 내용 |
| --- | --- |
| 시나리오 | 부산 알레르기 안전 안내문 |
| 사용자 요청 | 부산의 장소와 알레르기 안전 수칙을 조사하고 안내문을 작성한 뒤 필수 내용을 검토해 줘. |
| 주요 패턴 | Sequential + Evaluator–Reviser |
| 데이터 근거 | 부산 장소, 알레르기 지침, 안내문 품질 조건 |
| 완료 결과 | 검토를 통과한 안내문, 출처, 사용자 승인 요청, 실행 Trace |
| 최대 수정 횟수 | 3회 |

최종 목표는 다음 흐름을 재현하는 것이다.

```text
사용자 요청
  → Allergy Research Agent
  → Research 계약 검증
  → Allergy Guide Writer Agent
  → Draft 계약 검증
  → Allergy Guide Reviewer Agent
      ├─ 통과 → 최종 안내문 반환
      └─ 실패 → 피드백과 함께 Writer 재실행
                    └─ 최대 3회까지 반복
```

## 3. Agent 설계

세 Agent는 조사, 작성, 검토를 각각 하나의 책임으로 나눈다. 앞 Agent가 반환한 결과는 계약 검증을 통과한 뒤에만 다음 Agent의 입력 Context가 된다.

| 실행 순서 | Agent ID | 핵심 역할 | 입력 | 출력 계약 | 허용 Tool |
| --- | --- | --- | --- | --- | --- |
| 1 | `allergy_research_agent` | 장소와 안전 지침 조사 | 사용자 요청 | `AllergyResearchResult` | `search_places`, `get_allergy_guidance` |
| 2 | `allergy_guide_writer_agent` | 근거 기반 안내문 작성·수정 | 검증된 조사 결과, 품질 조건, 선택적 검토 피드백 | `AllergyGuideDraftResult` | `get_quality_requirements` |
| 3 | `allergy_guide_reviewer_agent` | 필수 조건과 근거 검토 | 검증된 조사 결과와 초안 | `AllergyGuideReviewResult` | `check_required_terms`, `get_quality_requirements` |

### 3.1 Allergy Research Agent

**식별자:** `allergy_research_agent`  
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

**완료 조건:** 사실과 안전 지침이 각각 한 개 이상 존재하고 모든 항목에 출처가 있어야 한다. 조건을 충족하지 못하면 Writer를 실행하지 않는다.

### 3.2 Allergy Guide Writer Agent

**식별자:** `allergy_guide_writer_agent`  
**목표:** 검증된 조사 자료만 사용하여 필수 안전 항목이 포함된 안내문을 작성한다.

**입력**

- 검증된 `AllergyResearchResult`
- `get_quality_requirements`가 반환한 품질 조건
- 수정 시 이전 초안과 `AllergyGuideReviewResult.feedback`
- 현재 수정 회차 `revision`

**수행할 일**

- 조사 결과에 있는 사실과 출처만 사용한다.
- 식재료·교차접촉 확인, 119 신고, 사용자 승인 요청을 초안에 반영한다.
- 실제 사용한 출처와 반영한 요구사항을 별도 필드에 기록한다.
- Reviewer의 피드백을 받은 경우 누락된 부분을 수정한다.
- 결과를 `AllergyGuideDraftResult` 구조로 반환한다.

**수행하지 않을 일**

- 조사되지 않은 장소나 안전 정보를 새로 만들지 않는다.
- 자신의 초안을 스스로 통과 처리하지 않는다.
- 예약, 연락, 게시와 같은 외부 행동을 수행하지 않는다.

**완료 조건:** 비어 있지 않은 초안, 사용 출처, 반영 요구사항 및 1~3 범위의 수정 회차가 있어야 한다.

### 3.3 Allergy Guide Reviewer Agent

**식별자:** `allergy_guide_reviewer_agent`  
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

## 4. 통과 기준

Reviewer는 다음 조건을 모두 만족할 때만 안내문을 통과시킨다.

1. 장소와 알레르기 안전 지침의 출처가 포함되어 있다.
2. 방문 전에 식재료와 교차접촉 가능성을 직접 확인하도록 안내한다.
3. 중증 증상이 의심될 때 119에 신고하도록 안내한다.
4. 안내문을 게시하거나 사용하기 전에 사용자 승인을 요청한다.
5. 데이터에 없는 장소의 안전성이나 의학적 판단을 확정하지 않는다.

하나라도 충족하지 못하면 `passed=false`와 함께 누락 조건 및 수정 피드백을 반환한다.

## 5. Output Contract 설계

계약은 Agent가 반환해야 하는 데이터의 모양과 유효 조건을 정의한다. LLM 응답은 해당 Pydantic 모델의 검증을 통과한 경우에만 다음 단계에서 사용할 수 있다.

구현 파일은 다음과 같이 분리한다.

```text
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\schemas\allergy_contracts.py
```

### 5.1 보조 모델

중첩된 사실과 안전 지침을 단순 문자열 대신 별도 모델로 표현한다.

| 모델 | 필드 | 의미 |
| --- | --- | --- |
| `ResearchFact` | `fact: str` | 조사된 장소 또는 관련 사실 |
|  | `source: str` | 해당 사실의 출처 |
| `SafetyGuidance` | `guidance: str` | 알레르기 안전 행동 지침 |
|  | `emergency: bool` | 응급 상황 안내 여부 |
|  | `source: str` | 해당 지침의 출처 |

### 5.2 AllergyResearchResult

**생성 Agent:** `allergy_research_agent`  
**사용 Agent:** `allergy_guide_writer_agent`

| 필드 | 자료형 | 필수 규칙 | 다음 단계에서의 용도 |
| --- | --- | --- | --- |
| `agent_id` | 고정 문자열 | `allergy_research_agent`만 허용 | 결과 생성자 확인 |
| `facts` | `list[ResearchFact]` | 1~10개 | 안내문에 사용할 장소와 사실 |
| `safety_guidance` | `list[SafetyGuidance]` | 1~10개 | 안전 수칙과 응급 안내 작성 |
| `completed` | `bool` | 근거가 준비된 경우에만 `true` | Writer 실행 가능 여부 판단 |

**계약 검증 규칙**

- 사실과 안전 지침은 각각 한 개 이상이어야 한다.
- 각 항목의 내용과 출처는 빈 문자열일 수 없다.
- 필요한 근거 없이 `completed=true`인 결과는 거부한다.
- `completed=false`이면 Orchestrator가 Writer 실행을 중단한다.

### 5.3 AllergyGuideDraftResult

**생성 Agent:** `allergy_guide_writer_agent`  
**사용 Agent:** `allergy_guide_reviewer_agent`

| 필드 | 자료형 | 필수 규칙 | 다음 단계에서의 용도 |
| --- | --- | --- | --- |
| `agent_id` | 고정 문자열 | `allergy_guide_writer_agent`만 허용 | 결과 생성자 확인 |
| `draft` | `str` | 빈 문자열 금지 | Reviewer가 검사할 안내문 |
| `used_sources` | `list[str]` | 1~10개 | 조사 출처 사용 여부 확인 |
| `included_requirements` | `list[str]` | 최대 10개 | Writer가 반영했다고 보고한 조건 |
| `revision` | `int` | 1~3 | 재작성 횟수 제한 확인 |

**계약 검증 규칙**

- 초안과 사용 출처가 반드시 있어야 한다.
- 수정 회차는 1, 2, 3 중 하나여야 한다.
- `used_sources`가 Research 결과에 존재하는지는 Orchestrator가 교차 검증한다.
- 계약 통과는 내용 심사 통과를 의미하지 않는다. 최종 품질 판정은 Reviewer가 담당한다.

### 5.4 AllergyGuideReviewResult

**생성 Agent:** `allergy_guide_reviewer_agent`  
**사용 주체:** Orchestrator와 다음 회차의 Writer

| 필드 | 자료형 | 필수 규칙 | 다음 단계에서의 용도 |
| --- | --- | --- | --- |
| `agent_id` | 고정 문자열 | `allergy_guide_reviewer_agent`만 허용 | 결과 생성자 확인 |
| `passed` | `bool` | 반드시 존재 | 종료 또는 재작성 결정 |
| `missing_requirements` | `list[str]` | 기본값 빈 목록 | 누락 조건 전달 |
| `unsupported_claims` | `list[str]` | 기본값 빈 목록 | 근거 없는 주장 전달 |
| `feedback` | `str` | 실패 시 비어 있을 수 없음 | Writer의 수정 지시 |

**계약 검증 규칙**

- `passed=true`이면 두 문제 목록이 모두 비어 있어야 한다.
- `passed=false`이면 Writer가 실행 가능한 구체적인 피드백이 있어야 한다.
- `passed=false`이면 Orchestrator가 회차를 증가시켜 Writer를 다시 실행한다.

### 5.5 AllergySafetyRunResult

이 계약은 개별 Agent가 아니라 전체 Orchestration의 최종 상태를 표현한다.

| 필드 | 자료형 | 의미 |
| --- | --- | --- |
| `status` | `completed` 또는 `failed` | 전체 실행 성공 여부 |
| `final_guide` | 문자열 또는 `null` | 검토를 통과한 최종 안내문 |
| `termination_reason` | 고정된 종료 사유 | 성공·실패의 구체적인 원인 |
| `revision_count` | 정수 | 실제 Writer 실행 횟수 |
| `error` | 문자열 또는 `null` | 실패 상세 내용 |
| `trace` | 실행 기록 목록 | Agent, 검증, 반복 흐름 확인 |

`termination_reason`은 다음 값 중 하나를 사용한다.

| 종료 사유 | 의미 |
| --- | --- |
| `evaluation_passed` | Reviewer 검토를 통과함 |
| `research_failed` | 조사 결과가 없거나 완료되지 않음 |
| `contract_rejected` | Agent 결과가 출력 계약을 위반함 |
| `tool_error` | MCP Tool 또는 데이터 조회가 실패함 |
| `max_revisions_exceeded` | 세 번의 작성 후에도 검토를 통과하지 못함 |

## 6. Agent 간 Context 전달 계약

| 전달 구간 | 선행 조건 | 다음 단계에 보장할 값 | 위반 시 처리 |
| --- | --- | --- | --- |
| Research → Writer | Research 계약 검증 완료 | 출처가 있는 사실과 안전 지침 | Writer를 실행하지 않고 `research_failed` 종료 |
| Writer → Reviewer | Draft 계약 검증 완료 | 안내문, 사용 출처, 반영 조건, 수정 회차 | 해당 실행을 `contract_rejected`로 종료 |
| Reviewer → Writer | `passed=false` | 누락 조건, 근거 없는 주장, 수정 피드백 | 회차를 증가시켜 Writer 재실행 |
| Reviewer → Final | `passed=true` | 누락 없는 최종 안내문 | `evaluation_passed`로 종료 |

Context는 문자열 하나로 합치기보다 검증된 모델의 `model_dump()` 결과처럼 구조화된 데이터로 전달한다.

## 7. MCP Tool 계획

과제 목록에는 Agent, 계약, Orchestration, Router만 적혀 있지만, 이 시나리오에서 근거 기반 실행을 만들려면 MCP Tool도 함께 확인하거나 추가해야 한다.

필요한 Tool은 다음과 같다.

| Tool | 사용 Agent | 목적 |
| --- | --- | --- |
| `search_places` | Research | 부산 장소 후보 조회 |
| `get_allergy_guidance` | Research | 알레르기 안전 지침 조회 |
| `get_quality_requirements` | Writer, Reviewer | 안내문 완료 조건 조회 |
| `check_required_terms` | Reviewer | 초안의 필수 항목 포함 여부 검사 |

Tool 또는 데이터베이스 조회가 실패하면 임의의 데이터로 대체하지 않는다. 실패는 Orchestrator가 `tool_error`로 기록하고 후속 Agent 실행을 중단해야 한다.

Agent는 `allowed_tools`에 등록된 Tool만 호출할 수 있어야 한다.

## 8. Orchestration 설계

사용자 과제의 `drchestration/`은 `orchestration/`의 오타로 보고 실제 경로인 `backend/app/orchestration/`에 구현한다.

예정 파일명은 다음과 같다.

```text
backend/app/orchestration/allergy_safety_guide.py
```

Orchestrator는 콘텐츠를 직접 만들지 않고 다음 Agent, 전달 Context, 수정 회차, 중단 조건과 종료 이유를 관리한다.

### 8.1 실행 순서

1. 사용자 요청 계약을 검증한다.
2. Research Agent를 실행한다.
3. `AllergyResearchResult`로 결과를 검증한다.
4. 조사 실패, 빈 근거 또는 Tool 실패 시 후속 Agent를 실행하지 않는다.
5. 검증된 조사 결과를 Writer에게 전달한다.
6. Writer의 결과를 `AllergyGuideDraftResult`로 검증한다.
7. 검증된 초안을 Reviewer에게 전달한다.
8. Reviewer의 결과를 `AllergyGuideReviewResult`로 검증한다.
9. Reviewer가 통과시키면 최종 결과를 반환한다.
10. 통과하지 못하면 초안과 Reviewer 피드백을 Writer에게 전달한다.
11. 최대 3회까지 작성과 검토를 반복한다.
12. 3회 안에 통과하지 못하면 `max_revisions_exceeded`로 종료한다.

### 8.2 반복 제어 예시

```python
research = await run_research()
verified_research = validate_research(research)

feedback = None
for revision in range(1, 4):
    draft = await run_writer(verified_research, feedback, revision)
    verified_draft = validate_draft(draft)

    review = await run_reviewer(verified_research, verified_draft)
    verified_review = validate_review(review)

    if verified_review.passed:
        return completed_result(verified_draft, revision)

    feedback = verified_review.feedback

return failed_result("max_revisions_exceeded")
```

실제 구현에서는 예외, Tool 오류, 계약 검증 오류와 Trace 기록을 함께 처리한다.

## 9. Trace 설계

Swagger 응답이나 실행 상태에서 전체 흐름을 확인할 수 있도록 다음과 같은 Trace를 남긴다.

```text
orchestrator: request_validated
allergy_research_agent: started
allergy_research_agent: completed
contract_guard: research_verified
allergy_guide_writer_agent: started, revision=1
contract_guard: draft_verified, revision=1
allergy_guide_reviewer_agent: started, revision=1
allergy_guide_reviewer_agent: rejected, revision=1
allergy_guide_writer_agent: started, revision=2
allergy_guide_reviewer_agent: passed, revision=2
orchestrator: evaluation_passed
```

실패하거나 건너뛴 Agent도 `failed` 또는 `skipped` 상태로 Trace에 남긴다.

## 10. Router URL 계획

`backend/app/routers/contracts.py`에 전용 API를 추가한다.

예정 URL은 다음과 같다.

```text
POST /api/runs/allergy-safety-guide
```

Router의 책임은 요청을 받아 알레르기 안전 안내 Orchestration을 호출하고 결과를 반환하는 것이다. Agent 실행 순서나 재작성 반복을 Router에 작성하지 않는다.

요청 예시는 다음과 같다.

```json
{
  "message": "부산의 장소와 알레르기 안전 수칙을 조사하고 안내문을 작성한 뒤 필수 내용을 검토해 줘."
}
```

## 11. Swagger 검증 계획

서버 실행 후 `/docs`에서 `POST /api/runs/allergy-safety-guide`를 호출한다.

정상 흐름에서 확인할 항목은 다음과 같다.

- HTTP 요청이 정상적으로 처리되는가?
- `status`가 `completed`인가?
- `termination_reason`이 `evaluation_passed`인가?
- 최종 안내문에 출처가 포함되어 있는가?
- 식재료와 교차접촉 가능성 확인 안내가 있는가?
- 중증 증상 발생 시 119 신고 안내가 있는가?
- 게시 또는 사용 전 사용자 승인 요청이 있는가?
- Writer의 수정 회차가 응답에 표시되는가?
- Research → Writer → Reviewer 순서가 Trace에 나타나는가?
- 1차 실패를 의도한 Mock을 사용하는 경우 Reviewer 피드백이 2차 Writer에게 전달되는가?

실패 흐름에서도 다음 결과를 확인한다.

- 조사 근거가 없으면 Writer와 Reviewer가 실행되지 않는다.
- Tool 오류가 성공 응답으로 변경되지 않는다.
- 계약에 맞지 않는 결과가 다음 Agent에게 전달되지 않는다.
- 세 번의 수정 후에도 실패하면 `max_revisions_exceeded`로 종료된다.

## 12. 자동 테스트 계획

Swagger 수동 테스트와 별도로 `tests/`에 시나리오 테스트를 추가한다.

필수 테스트는 다음과 같다.

1. 세 Agent가 올바른 순서로 실행된다.
2. Research 결과가 Writer Context에 전달된다.
3. Writer 결과가 Reviewer Context에 전달된다.
4. Reviewer의 실패 피드백이 다음 Writer 실행에 전달된다.
5. 필수 문구가 없으면 Reviewer가 실패시킨다.
6. 수정본이 조건을 충족하면 반복이 즉시 종료된다.
7. 최대 수정 횟수는 3회다.
8. Research 계약 검증 실패 시 후속 Agent는 실행되지 않는다.
9. 허용되지 않은 Tool 호출은 차단된다.
10. 잘못된 Agent 출력은 Pydantic 계약에서 거부된다.
11. Tool 또는 DB 오류가 실패 상태와 Trace에 남는다.
12. 동일한 Mock 입력은 동일한 결과와 Trace를 만든다.

## 13. 예상 파일 변경 목록

구현 단계에서 추가하거나 수정할 가능성이 있는 파일은 다음과 같다.

```text
backend/app/agents/
├─ allergy_research_agent.py                 # 추가
├─ allergy_guide_writer_agent.py             # 추가
├─ allergy_guide_reviewer_agent.py           # 추가
└─ registry.py                               # 수정

backend/app/schemas/
└─ contracts.py                              # 계약 추가

backend/app/orchestration/
└─ allergy_safety_guide.py                   # 추가

backend/app/routers/
└─ contracts.py                              # URL 추가

mcp_server/tools/
└─ 관련 Tool 파일                            # 확인 후 추가 또는 수정

mcp_server/database/
└─ 관련 조회 및 데이터                       # 필요 시 추가 또는 수정

tests/
└─ test_allergy_safety_guide.py              # 추가
```

기존 날씨·장소·숙소·예산 실습 코드는 가능한 한 변경하지 않고 새 시나리오를 추가한다.

## 14. 구현 순서

1. 기존 Agent Runtime, Registry, MCP Client와 테스트 구조를 확인한다.
2. 시나리오에 필요한 MCP Tool과 데이터가 현재 프로젝트에 있는지 확인한다.
3. 역할별 출력 계약과 전체 실행 결과 계약을 작성한다.
4. 세 Agent를 작성하고 Registry에 등록한다.
5. MCP Tool과 데이터 조회를 연결한다.
6. 최대 3회의 Evaluator–Reviser 반복이 있는 Orchestration을 작성한다.
7. Router에 전용 URL을 추가한다.
8. 계약과 정상·실패·반복 흐름의 자동 테스트를 작성한다.
9. 전체 테스트를 실행한다.
10. 서버를 실행하고 Swagger에서 최종 흐름을 확인한다.

## 15. 최종 완료 기준

다음 조건을 모두 충족하면 과제가 완료된 것으로 본다.

- Research, Writer, Reviewer의 책임과 금지 범위가 분리되어 있다.
- 각 Agent에 허용된 Tool만 연결되어 있다.
- 역할별 Pydantic Output Contract가 존재한다.
- 검증된 결과만 다음 Agent의 Context로 전달된다.
- Reviewer 피드백으로 Writer가 실제 재실행된다.
- 최대 3회 제한을 Orchestrator가 강제한다.
- 모든 성공·실패·건너뜀 상태가 Trace에 기록된다.
- 실패 원인과 종료 이유가 API 결과에 나타난다.
- Router URL을 통해 Swagger에서 전체 흐름을 실행할 수 있다.
- 자동 테스트가 정상 흐름과 주요 실패 흐름을 검증한다.

이번 실습의 최종 산출물은 단순한 안내문 생성 API가 아니라, **역할 분리, 계약 검증, Context 전달, 평가와 재작성, 종료 제어를 확인할 수 있는 작은 멀티 에이전트 시스템**이다.
