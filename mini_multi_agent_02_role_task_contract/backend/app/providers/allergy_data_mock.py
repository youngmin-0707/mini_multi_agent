"""알레르기 실습 전용 결정적 Tool Fixture. DB와 MCP를 호출하지 않는다."""

import re


SCENARIOS = {
    "haeundae": {
        "title": "해운대 바다 나들이",
        "places": [
            {"name": "해운대해수욕장", "category": "해변", "transit_note": "해변 산책"},
            {"name": "동백섬 산책로", "category": "산책", "transit_note": "바다 풍경 감상"},
        ],
        "foods": [
            {"name": "물회", "suspected_ingredients": ["생선", "조개류", "양념의 대두·밀 성분"]},
            {"name": "밀면", "suspected_ingredients": ["밀", "달걀", "육수의 대두 성분"]},
        ],
    },
    "gwangan": {
        "title": "광안리 바다 나들이",
        "places": [
            {"name": "광안리해수욕장", "category": "해변", "transit_note": "해변 산책"},
            {"name": "민락수변공원", "category": "산책", "transit_note": "바다 풍경 감상"},
        ],
        "foods": [
            {"name": "해물파전", "suspected_ingredients": ["밀", "달걀", "새우·조개류"]},
            {"name": "어묵", "suspected_ingredients": ["생선", "밀", "대두"]},
        ],
    },
}
DAYTIME_CAUTION = "12~15시에 햇볕이 강한 날에는 장시간 물놀이를 피하고 그늘에서 쉬세요."
GUIDANCE = [
    {"guidance": "실제 원재료와 교차접촉 가능성을 주문 전에 매장에 직접 확인하세요.", "emergency": False},
    {"guidance": "중증 알레르기 증상이 의심되면 즉시 119에 신고하세요.", "emergency": True},
]
REQUIREMENTS = [
    {"requirement_key": key, "description": description, "required_term": term, "check_type": check_type}
    for key, description, term, check_type in (
        ("suspected_ingredients", "추천 음식의 알레르기 유발 의심 원재료를 표시한다.", "알레르기 유발 의심 원재료", "literal"),
        ("daytime", "12~15시 햇볕 주의 안내를 포함한다.", "12~15시", "literal"),
        ("cross_contact", "식재료와 교차접촉 가능성을 직접 확인하도록 안내한다.", "교차접촉", "literal"),
        ("emergency", "중증 증상이 의심되면 119 신고를 안내한다.", "119", "emergency_report"),
        ("approval", "게시 또는 사용 전에 사용자 승인을 요청한다.", "승인", "literal"),
    )
]


def _check_required_terms(draft: str, scenario: str) -> dict:
    """Mock 조건을 URL을 제외한 본문에 적용한다."""

    requirements = REQUIREMENTS if scenario == "allergy_safety" else []
    body = re.sub(r"https?://\S+", "", draft)
    checks = []
    for item in requirements:
        if item["check_type"] == "emergency_report":
            included = bool(re.search(r"119\s*(?:에|로)?\s*신고", body))
        else:
            included = item["required_term"] in body
        checks.append({
            "requirement_key": item["requirement_key"],
            "description": item["description"],
            "required_term": item["required_term"],
            "included": included,
        })
    return {
        "success": bool(requirements), "scenario": scenario,
        "passed": bool(requirements) and all(item["included"] for item in checks),
        "checks": checks, "source": "mock",
    }


def mock_tool_result(tool_name: str, arguments: dict[str, object]) -> dict:
    """실제 MCP Tool과 같은 반환 형태로 Fixture를 제공한다."""

    if tool_name == "search_places":
        city = arguments["city"]
        scenario_id = arguments.get("scenario_id", "haeundae")
        scenario = SCENARIOS.get(scenario_id) if city == "부산" else None
        items = scenario["places"] if scenario else []
        return {
            "success": bool(items), "city": city, "items": [dict(item) for item in items],
            "scenario_id": scenario_id, "scenario_title": scenario["title"] if scenario else None,
            "food_suggestions": [dict(item) for item in scenario["foods"]] if scenario else [],
            "daytime_caution": DAYTIME_CAUTION if scenario else None, "source": "mock",
        }
    if tool_name == "get_allergy_guidance":
        city = arguments["city"]
        items = GUIDANCE if city == "부산" else []
        return {"success": bool(items), "city": city, "items": [dict(item) for item in items], "source": "mock"}
    if tool_name == "get_quality_requirements":
        scenario = arguments["scenario"]
        items = REQUIREMENTS if scenario == "allergy_safety" else []
        return {"success": bool(items), "scenario": scenario, "items": [dict(item) for item in items], "source": "mock"}
    if tool_name == "check_required_terms":
        return _check_required_terms(arguments["draft"], arguments["scenario"])
    raise ValueError(f"지원하지 않는 알레르기 Mock Tool입니다: {tool_name}")
