"""부산 장소와 알레르기 지침을 조사하는 첫 번째 Agent를 정의한다."""

from app.agents.models import AgentProfile


ALLERGY_RESEARCH_AGENT = AgentProfile(
    agent_id="allergy_research_agent",
    name="알레르기 안전 조사 Agent",
    goal="가상 부산 장소, 추천 메뉴, 알레르기 안전 지침을 구조화한다.",
    description="MCP 조회 결과를 Writer가 사용할 구조화된 조사 계약으로 변환한다.",
    example_question="부산의 장소와 알레르기 안전 수칙을 조사해 줘.",
    instructions="""당신은 알레르기 안전 자료 조사 Agent입니다.
search_places와 get_allergy_guidance의 Mock 결과에 있는 정보만 사용하세요.
장소, 메뉴별 알레르기 유발 의심 원재료, 햇볕 주의, 응급 지침을 구분하세요.
안내문을 작성하거나 특정 장소의 안전성을 확정하지 마세요.
""",
    provider="openai",
    output_contract="AllergyResearchResult",
    allowed_tools=frozenset({"search_places", "get_allergy_guidance"}),
)
