# 부산 알레르기 안전 안내문 실습 Handoff

## 1. 작업 목적

`mini_multi_agent_01_patterns/SCENARIO.md`의 부산 알레르기 안전 안내문 시나리오를 `mini_multi_agent_02_role_task_contract` 프로젝트에 구현한다.

핵심 학습 목표는 다음과 같다.

- Research, Writer, Reviewer Agent의 역할 분리
- 역할별 Pydantic Output Contract 검증
- 검증된 Context만 다음 Agent에 전달
- Reviewer 실패 시 Writer 재작성
- 최대 3회 반복과 명시적인 종료 사유
- MCP, PostgreSQL, Router와 Swagger 연결
- `LLM_MODE=mock | real` 전환

## 2. 현재 구현 상태

구현된 전체 흐름은 다음과 같다.

```text
사용자 요청
  → Allergy Research Agent
  → AllergyResearchResult 검증
  → Allergy Guide Writer Agent
  → AllergyGuideDraftResult 검증
  → Allergy Guide Reviewer Agent
  ├─ 통과 → 최종 안내문 반환
  └─ 실패 → 피드백과 함께 Writer 재실행
               └─ 최대 3회
```

현재 완료된 항목:

- 알레르기 시나리오용 Agent 3개 정의
- Agent Registry 등록
- 역할별 출력 계약과 전체 실행 결과 계약 작성
- 학습용 독스트링 추가
- PostgreSQL 테이블과 Seed SQL 작성
- 알레르기 관련 MCP Tool 4개 작성 및 등록
- 알레르기 Agent 전용 Mock Provider 작성
- `LLM_MODE=mock | real` 분기 연결
- 최대 3회 Evaluator–Reviser Orchestration 작성
- Router URL 추가
- 계약 및 Orchestration 단위 테스트 작성
- Swagger에서 API 실행 확인

## 3. 주요 파일

### 설계 문서

```text
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\ASSIGNMENT_PLAN.md
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\SCENARIO_AGENT_CONTRACT_PLAN.md
```

### Output Contract

```text
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\schemas\allergy_contracts.py
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\schemas\contracts.py
```

추가된 주요 모델:

- `ResearchFact`
- `SafetyGuidance`
- `AllergyResearchResult`
- `AllergyGuideDraftResult`
- `AllergyGuideReviewResult`
- `AllergySafetyRequest`
- `AllergyTraceEvent`
- `AllergySafetyRunResult`

### Agent

```text
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\agents\allergy_research_agent.py
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\agents\allergy_guide_writer_agent.py
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\agents\allergy_guide_reviewer_agent.py
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\agents\registry.py
```

Agent ID:

- `allergy_research_agent`
- `allergy_guide_writer_agent`
- `allergy_guide_reviewer_agent`

### Runtime과 Mock Provider

```text
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\agents\runtime.py
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\providers\allergy_mock.py
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\core\config.py
```

Mock 동작 설계:

- Research Fixture는 MCP 장소와 안전 지침을 구조화한다.
- Writer 1차 Fixture는 의도적으로 119 응급 안내를 누락한다.
- Reviewer가 실패하면 Writer 2차 Fixture가 응급 안내를 추가한다.
- Mock과 Real은 같은 Pydantic 계약을 사용한다.
- 기본 설정은 `LLM_MODE=mock`이다.

### MCP와 PostgreSQL

```text
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\mcp_server\tools\travel_tools.py
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\mcp_server\database\travel_queries.py
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\mcp_server\database\schema.sql
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\mcp_server\main.py
```

추가된 MCP Tool:

- `get_allergy_guidance`
- `get_quality_requirements`
- `check_required_terms`
- 기존 `search_places` 재사용

추가된 PostgreSQL 테이블:

- `mini_multi_agent_02.allergy_guidance`
- `mini_multi_agent_02.quality_requirements`

### Orchestration과 Router

```text
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\orchestration\allergy_safety_guide.py
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\backend\app\routers\contracts.py
```

추가된 API:

```text
POST /api/runs/allergy-safety-guide
```

### 테스트

```text
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\tests\test_allergy_contracts.py
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\tests\test_allergy_safety_guide.py
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\tests\test_runtime.py
```

## 4. 설정

`.env.example`에 다음 설정이 추가되어 있다.

```dotenv
LLM_MODE=mock
```

동작 방식:

- `LLM_MODE=mock`: 알레르기 Agent만 외부 LLM 대신 결정적인 Fixture 사용
- `LLM_MODE=real`: 각 Agent Profile에 지정된 기존 Provider 사용
- PostgreSQL과 MCP 조회는 두 모드 모두 실제 경로 사용

실제 `.env`의 API Key, 데이터베이스 비밀번호 등 비밀값은 이 문서에 기록하지 않는다. 다른 컴퓨터에서는 기존 `.env.example`을 참고해 `.env`를 별도로 준비해야 한다.

## 5. 다른 컴퓨터에서 준비할 것

1. 프로젝트 전체 파일을 복사하거나 Git으로 가져온다.
2. Python 가상환경을 새로 만든다. 기존 `.venv`는 컴퓨터별 절대경로를 포함할 수 있으므로 복사해서 재사용하지 않는 것이 안전하다.
3. `requirements.txt`를 설치한다.
4. `.env.example`을 참고하여 `.env`를 준비한다.
5. PostgreSQL과 Redis를 실행한다.
6. 데이터베이스 Schema와 Seed를 적용한다.
7. 테스트를 실행한다.
8. MCP 서버와 Backend를 실행한다.
9. Swagger에서 API를 호출한다.

### 권장 환경 준비 명령

프로젝트 루트에서 실행한다.

```powershell
cd C:\mini_multi_agent\mini_multi_agent_02_role_task_contract

python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 6. 데이터베이스 초기화

반드시 프로젝트 루트에서 실행한다. 상위 폴더에서 실행하면 `mcp_server`를 찾지 못한다.

```powershell
cd C:\mini_multi_agent\mini_multi_agent_02_role_task_contract
python -m mcp_server.database.init_db
```

정상 메시지:

```text
mini_multi_agent_02 Schema와 Seed 데이터 준비가 완료됐습니다.
```

## 7. 테스트 실행

```powershell
cd C:\mini_multi_agent\mini_multi_agent_02_role_task_contract
.\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests -v
```

이전 컴퓨터에서는 한때 `.venv`가 존재하지 않는 Python 경로를 가리켜 테스트를 실행하지 못했다. 이후 사용자가 가상환경을 활성화하여 DB 초기화 명령을 실행할 수 있었으므로, 새 컴퓨터에서는 가상환경을 새로 생성한 뒤 전체 테스트를 다시 실행해야 한다.

## 8. 서버 실행

### Terminal 1 MCP 서버

```powershell
cd C:\mini_multi_agent\mini_multi_agent_02_role_task_contract
.\.venv\Scripts\Activate.ps1
python -m mcp_server.main
```

기본 MCP URL:

```text
http://127.0.0.1:8010/mcp
```

### Terminal 2 Backend

```powershell
cd C:\mini_multi_agent\mini_multi_agent_02_role_task_contract
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --app-dir backend --reload --port 8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

MCP 상태 확인:

```text
http://127.0.0.1:8000/api/mcp-status
```

## 9. Swagger 요청

Swagger에서 다음 API를 실행한다.

```text
POST /api/runs/allergy-safety-guide
```

Request Body:

```json
{
  "message": "부산의 장소와 알레르기 안전 수칙을 조사하고 안내문을 작성한 뒤 필수 내용을 검토해 줘."
}
```

## 10. 현재 Swagger 확인 결과

API 연결, PostgreSQL 조회, MCP Tool 호출, 세 Agent 실행, 계약 검증과 Trace 반환은 성공했다.

확인된 응답의 주요 값:

```json
{
  "status": "completed",
  "termination_reason": "evaluation_passed",
  "revision_count": 1
}
```

Research 결과에는 다음 응급 지침이 존재했다.

```text
중증 알레르기 증상이 의심되면 즉시 119에 신고한다.
```

그러나 Writer 1차 안내문에는 해당 응급 문장이 포함되지 않았다. 그럼에도 Reviewer가 1차 초안을 통과시켰다.

## 11. 반드시 수정해야 할 현재 버그

### 증상

Mock 시나리오는 1차 Writer가 119 응급 안내를 누락하고, Reviewer가 실패시킨 뒤 2차 Writer가 보완하도록 설계되었다.

기대 결과:

```json
{
  "status": "completed",
  "termination_reason": "evaluation_passed",
  "revision_count": 2
}
```

실제 결과:

```json
{
  "status": "completed",
  "termination_reason": "evaluation_passed",
  "revision_count": 1
}
```

### 원인

`check_required_terms`는 초안 전체에서 필수 문자열 `119`가 있는지만 검사한다.

1차 안내문의 출처 목록에 다음 URL이 포함된다.

```text
https://www.119.go.kr/
```

따라서 실제 응급 신고 문장이 없어도 URL 안의 `119`를 발견하여 조건을 통과시키는 false positive가 발생한다.

### 수정 대상

```text
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\mcp_server\tools\travel_tools.py
```

대상 함수:

```python
check_required_terms
```

### 권장 수정 방향

필수 조건을 검사하기 전에 URL을 제거한 본문을 사용한다.

예시 개념:

```python
import re

body_without_urls = re.sub(r"https?://\S+", "", draft)
```

그 후 `required_term`을 `body_without_urls`에서 검사한다.

더 엄격하게 만들려면 단순 `119` 대신 다음과 같은 의미 있는 문구를 검사한다.

```text
119에 신고
119 신고
119로 신고
```

입문 실습 범위에서는 URL 제거 후 검사하는 방식이 가장 작은 수정이다.

## 12. 버그 수정 후 확인할 Trace

정상적인 Mock 실행에서는 다음 순서가 나타나야 한다.

```text
request_validated
research started
research_verified
writer started revision 1
draft_verified revision 1
reviewer rejected revision 1
writer started revision 2
draft_verified revision 2
reviewer passed revision 2
evaluation_passed revision 2
```

확인할 최종 값:

- `status == "completed"`
- `termination_reason == "evaluation_passed"`
- `revision_count == 2`
- `final_review.passed == true`
- `final_guide`에 교차접촉 안내가 있음
- `final_guide`에 실제 119 신고 문장이 있음
- `final_guide`에 출처가 있음
- `final_guide`에 사용자 승인 요청이 있음

## 13. 프론트엔드 상태

현재 Streamlit 화면에는 알레르기 시나리오가 연결되어 있지 않다.

현재 파일:

```text
C:\mini_multi_agent\mini_multi_agent_02_role_task_contract\frontend\app.py
```

현재 화면은 기존 Lab 01~11만 지원하며 다음 API를 호출하지 않는다.

```text
POST /api/runs/allergy-safety-guide
```

따라서 현재 테스트 방법은 Swagger 또는 직접 API 호출이다. Reviewer 오탐 수정과 Backend 검증이 끝난 뒤 Streamlit에 별도 화면을 추가하는 것이 다음 확장 작업이다.

## 14. 다음 작업 순서

1. 새 컴퓨터에서 가상환경과 `.env`를 준비한다.
2. 전체 자동 테스트를 실행한다.
3. `check_required_terms`의 URL 오탐을 수정한다.
4. MCP 서버를 재시작한다.
5. Swagger에서 같은 요청을 다시 실행한다.
6. `revision_count=2`와 재작성 Trace를 확인한다.
7. 필요하면 최대 3회 실패와 Tool 오류 테스트를 추가한다.
8. Backend 검증 완료 후 Streamlit 프론트 화면을 추가한다.

## 15. 작업 시 주의사항

- 기존 여행 Agent와 Lab 01~11 동작을 깨뜨리지 않는다.
- Mock 분기는 `allergy_` Agent에만 적용한다.
- Mock은 LLM 응답만 대체하며 MCP와 PostgreSQL은 실제 경로를 유지한다.
- Agent의 결과는 반드시 Pydantic 계약을 통과시킨다.
- Writer가 사용한 출처는 Research 결과의 출처와 Orchestrator에서 교차 검증한다.
- Reviewer는 안내문을 직접 수정하지 않고 피드백만 반환한다.
- 반복 횟수와 종료 조건은 Orchestrator가 관리한다.
- `.env`의 API Key와 데이터베이스 비밀번호를 문서나 Git에 포함하지 않는다.
