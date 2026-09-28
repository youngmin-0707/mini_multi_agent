from mcp_server.database.connection import query

def find_places(city: str) -> list[dict]:
    return query("SELECT name, category, transit_note, source_url, verified_at, indoor FROM mini_multi_agent_02.places WHERE city = %s ORDER BY place_id", (city,))

def find_budget_reference(city: str) -> dict | None:
    rows = query("SELECT transport, lodging_per_night, food_per_day, source_note, source_url, verified_at FROM mini_multi_agent_02.budget_reference WHERE city = %s", (city,))
    return rows[0] if rows else None


def find_allergy_guidance(city: str) -> list[dict]:
    """도시에 등록된 알레르기 안전 지침과 출처를 조회한다."""

    return query(
        "SELECT guidance, emergency, source_url, verified_at "
        "FROM mini_multi_agent_02.allergy_guidance "
        "WHERE city = %s ORDER BY guidance_id",
        (city,),
    )


def find_quality_requirements(scenario: str) -> list[dict]:
    """시나리오의 안내문 완료 조건을 검사 순서대로 조회한다."""

    return query(
        "SELECT requirement_key, description, required_term "
        "FROM mini_multi_agent_02.quality_requirements "
        "WHERE scenario = %s ORDER BY requirement_id",
        (scenario,),
    )
