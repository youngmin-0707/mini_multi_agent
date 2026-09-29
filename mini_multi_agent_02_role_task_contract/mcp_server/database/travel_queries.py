from mcp_server.database.connection import query

def find_places(city: str) -> list[dict]:
    return query("SELECT name, category, transit_note, source_url, verified_at, indoor FROM mini_multi_agent_02.places WHERE city = %s ORDER BY place_id", (city,))

def find_budget_reference(city: str) -> dict | None:
    rows = query("SELECT transport, lodging_per_night, food_per_day, source_note, source_url, verified_at FROM mini_multi_agent_02.budget_reference WHERE city = %s", (city,))
    return rows[0] if rows else None


def find_allergy_guidance(city: str) -> list[dict]:
    """도시에 등록된 알레르기 안전 지침과 출처를 조회한다."""

    return query(
        "SELECT g.guidance, g.guidance_key, g.situation, g.action, g.emergency, "
        "COALESCE(s.url, g.source_url) AS source_url, "
        "COALESCE(s.checked_at, g.verified_at) AS verified_at, "
        "s.title AS source_title, s.publisher AS source_publisher, s.evidence_note "
        "FROM mini_multi_agent_02.allergy_guidance AS g "
        "LEFT JOIN mini_multi_agent_02.allergy_sources AS s ON s.source_id = g.source_id "
        "WHERE g.city = %s ORDER BY g.guidance_id",
        (city,),
    )


def find_quality_requirements(scenario: str) -> list[dict]:
    """시나리오의 안내문 완료 조건을 검사 순서대로 조회한다."""

    return query(
        "SELECT requirement_key, description, required_term, check_type "
        "FROM mini_multi_agent_02.quality_requirements "
        "WHERE scenario = %s ORDER BY requirement_id",
        (scenario,),
    )
