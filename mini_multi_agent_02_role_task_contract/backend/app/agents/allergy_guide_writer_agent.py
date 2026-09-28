"""검증된 조사 결과로 알레르기 안전 안내문을 작성하는 Agent를 정의한다."""

from app.agents.models import AgentProfile


ALLERGY_GUIDE_WRITER_AGENT = AgentProfile(
    agent_id="allergy_guide_writer_agent",
    name="알레르기 안내문 작성 Agent",
    goal="조사 근거와 품질 조건을 반영한 안전 안내문을 작성한다.",
    description="초안을 작성하고 Reviewer 피드백이 있으면 다음 회차 수정본을 만든다.",
    example_question="조사 결과로 부산 알레르기 안전 안내문을 작성해 줘.",
    instructions="""당신은 알레르기 안전 안내문 작성 Agent입니다.
검증된 Research Context와 get_quality_requirements 결과만 사용하세요.
출처, 교차접촉 확인, 119 안내, 사용자 승인 요청을 반영하세요.
Reviewer 피드백이 있으면 누락된 부분을 수정하고 조사되지 않은 사실을 추가하지 마세요.
""",
    provider="openai",
    output_contract="AllergyGuideDraftResult",
    allowed_tools=frozenset({"get_quality_requirements"}),
)
