"""알레르기 실습의 결정적인 Mock LLM 응답을 생성한다.

Mock은 LLM 호출만 대체한다. 장소, 안전 지침과 품질 조건은 실제 MCP Tool
결과를 입력으로 받아 사용하므로 Agent의 데이터 흐름은 real 모드와 같다.
"""

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
                    "source": item["source_url"],
                }
                for item in places
            ],
            "safety_guidance": [
                {
                    "guidance": item["guidance"],
                    "emergency": item["emergency"],
                    "source": item["source_url"],
                }
                for item in guidance
            ],
            "completed": bool(places and guidance),
        }
    elif agent_id == "allergy_guide_writer_agent":
        research = context_data.get("research_result", {})
        revision = int(context_data.get("revision", 1))
        facts = research.get("facts", [])
        safety = research.get("safety_guidance", [])
        sources = list(dict.fromkeys(
            [item["source"] for item in facts] + [item["source"] for item in safety]
        ))
        place_text = "; ".join(item["fact"] for item in facts)
        normal_guidance = " ".join(
            item["guidance"] for item in safety if not item.get("emergency")
        )
        emergency_guidance = " ".join(
            item["guidance"] for item in safety if item.get("emergency")
        )
        draft_parts = [
            f"부산 방문 장소 정보: {place_text}",
            normal_guidance,
            f"출처: {', '.join(sources)}",
            "게시 또는 사용 전에 사용자의 승인을 받아 주세요.",
        ]
        requirements = ["source", "cross_contact", "approval"]
        if revision >= 2:
            draft_parts.insert(2, emergency_guidance)
            requirements.append("emergency")
        payload = {
            "agent_id": agent_id,
            "draft": "\n".join(part for part in draft_parts if part),
            "used_sources": sources,
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
