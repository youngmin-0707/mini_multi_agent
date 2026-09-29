"""알레르기 실습의 고정 Tool Fixture를 받아 Mock Agent 응답을 생성한다."""

from time import perf_counter

from pydantic import BaseModel


def _metadata(started: float) -> dict[str, object]:
    """기존 Provider 응답과 같은 형태의 실행 메타데이터를 만든다."""

    return {
        "provider_requested": "mock",
        "provider_used": "mock",
        "model": "allergy-fixture-v1",
        "latency_ms": round((perf_counter() - started) * 1000, 2),
        "fallback_used": False,
    }


def generate_allergy_mock(
    agent_id: str,
    schema: type[BaseModel],
    tool_results: dict[str, object],
    context: object | None,
) -> tuple[BaseModel, dict[str, object]]:
    """Agent ID에 맞는 Fixture를 만들고 동일한 출력 계약으로 검증한다."""

    started = perf_counter()
    context_data = context if isinstance(context, dict) else {}

    if agent_id == "allergy_research_agent":
        places = tool_results.get("search_places", {}).get("items", [])
        guidance = tool_results.get("get_allergy_guidance", {}).get("items", [])
        payload = {
            "agent_id": agent_id,
            "facts": [
                {
                    "fact": f"{item['name']}: {item['category']}, {item['transit_note']}",
                }
                for item in places
            ],
            "safety_guidance": [
                {
                    "guidance": item["guidance"],
                    "emergency": item["emergency"],
                }
                for item in guidance
            ],
            "scenario_title": tool_results.get("search_places", {}).get("scenario_title") or "부산 바다 나들이",
            "food_suggestions": tool_results.get("search_places", {}).get("food_suggestions", []),
            "daytime_caution": tool_results.get("search_places", {}).get("daytime_caution") or "",
            "completed": bool(places and guidance),
        }
    elif agent_id == "allergy_guide_writer_agent":
        research = context_data.get("research_result", {})
        revision = int(context_data.get("revision", 1))
        facts = research.get("facts", [])
        safety = research.get("safety_guidance", [])
        place_text = " · ".join(item["fact"].split(":", 1)[0] for item in facts)
        food_lines = [
            f"- {item['name']}: 알레르기 유발 의심 원재료 — {', '.join(item['suspected_ingredients'])}"
            for item in research.get("food_suggestions", [])
        ]
        normal_guidance = " ".join(
            item["guidance"] for item in safety if not item.get("emergency")
        )
        emergency_guidance = " ".join(
            item["guidance"] for item in safety if item.get("emergency")
        )
        draft_parts = [
            f"### {research.get('scenario_title') or '부산 바다 나들이'} (가상 실습 예시)",
            f"**가볼 곳** {place_text}",
            f"**햇볕 주의** {research.get('daytime_caution') or '12~15시에는 햇볕이 강한 날 그늘에서 쉬세요.'}",
            "**추천 음식과 확인할 재료**\n" + "\n".join(food_lines),
            f"**주문 전 확인** 위 재료는 메뉴별 추정입니다. {normal_guidance}",
            "**사용 전 확인** 안내문을 확인하고 승인해 주세요.",
        ]
        requirements = ["suspected_ingredients", "daytime", "cross_contact", "approval"]
        if revision >= 2:
            draft_parts.insert(5, f"**응급 안내** {emergency_guidance}")
            requirements.append("emergency")
        payload = {
            "agent_id": agent_id,
            "draft": "\n\n".join(part for part in draft_parts if part),
            "included_requirements": requirements,
            "revision": revision,
        }
    elif agent_id == "allergy_guide_reviewer_agent":
        checks = tool_results.get("check_required_terms", {}).get("checks", [])
        missing = [item["description"] for item in checks if not item["included"]]
        passed = bool(checks) and not missing
        payload = {
            "agent_id": agent_id,
            "passed": passed,
            "missing_requirements": missing,
            "unsupported_claims": [],
            "feedback": "모든 필수 조건을 충족했습니다." if passed else "누락된 필수 조건을 초안에 추가하세요: " + "; ".join(missing),
        }
    else:
        raise ValueError(f"Mock Fixture가 없는 Agent입니다: {agent_id}")

    return schema.model_validate(payload), _metadata(started)
