"""알레르기 안내 Orchestration의 Context 전달과 반복 종료를 검사한다."""

import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.orchestration.allergy_safety_guide import run_allergy_safety_guide  # noqa: E402
from app.providers.allergy_mock import generate_allergy_mock  # noqa: E402
from app.schemas.allergy_contracts import AllergySafetyRequest  # noqa: E402
from app.schemas.allergy_contracts import AllergyGuideDraftResult  # noqa: E402


def completed(result: dict) -> dict:
    """실제 Runtime과 같은 성공 응답을 테스트에서 간단히 만든다."""

    return {"status": "completed", "result": result, "error": None}


class AllergySafetyGuideTests(unittest.IsolatedAsyncioTestCase):
    """Reviewer 피드백이 Writer 재작성에 사용되는지 확인한다."""

    async def test_first_review_fails_and_second_review_passes(self) -> None:
        """1차 누락 피드백을 받은 Writer가 2차 초안을 만드는 흐름이다."""

        research = completed({
            "agent_id": "allergy_research_agent",
            "facts": [{"fact": "부산박물관", "source": "place-source"}],
            "safety_guidance": [{"guidance": "교차접촉 확인", "emergency": False, "source": "safety-source"}],
            "completed": True,
        })
        draft_one = completed({
            "agent_id": "allergy_guide_writer_agent",
            "draft": "출처와 교차접촉 안내",
            "used_sources": ["place-source", "safety-source"],
            "included_requirements": ["source", "cross_contact"],
            "revision": 1,
        })
        rejected = completed({
            "agent_id": "allergy_guide_reviewer_agent",
            "passed": False,
            "missing_requirements": ["119 신고 안내"],
            "unsupported_claims": [],
            "feedback": "119 신고 안내를 추가하세요.",
        })
        draft_two = completed({
            "agent_id": "allergy_guide_writer_agent",
            "draft": "출처, 교차접촉, 119 신고, 사용자 승인 안내",
            "used_sources": ["place-source", "safety-source"],
            "included_requirements": ["source", "cross_contact", "emergency", "approval"],
            "revision": 2,
        })
        passed = completed({
            "agent_id": "allergy_guide_reviewer_agent",
            "passed": True,
            "missing_requirements": [],
            "unsupported_claims": [],
            "feedback": "모든 조건을 충족했습니다.",
        })

        mocked = AsyncMock(side_effect=[research, draft_one, rejected, draft_two, passed])
        with patch("app.orchestration.allergy_safety_guide.run_agent", mocked):
            result = await run_allergy_safety_guide(
                AllergySafetyRequest(message="부산의 장소와 알레르기 안전 수칙을 안내해 줘.")
            )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.revision_count, 2)
        self.assertEqual(result.termination_reason, "evaluation_passed")
        second_writer_context = mocked.await_args_list[3].kwargs["context"]
        self.assertEqual(second_writer_context["feedback"], "119 신고 안내를 추가하세요.")
        self.assertEqual(second_writer_context["revision"], 2)

    async def test_mock_writer_adds_emergency_guidance_on_second_revision(self) -> None:
        """Mock Writer가 1차에는 119를 누락하고 2차에는 보완하는지 확인한다."""

        research = {
            "facts": [{"fact": "부산박물관", "source": "place-source"}],
            "safety_guidance": [
                {"guidance": "교차접촉을 확인한다.", "emergency": False, "source": "safety-source"},
                {"guidance": "중증 증상은 119에 신고한다.", "emergency": True, "source": "emergency-source"},
            ],
        }
        first, _ = generate_allergy_mock(
            "allergy_guide_writer_agent",
            AllergyGuideDraftResult,
            {},
            {"research_result": research, "revision": 1, "feedback": None},
        )
        second, _ = generate_allergy_mock(
            "allergy_guide_writer_agent",
            AllergyGuideDraftResult,
            {},
            {"research_result": research, "revision": 2, "feedback": "119 안내를 추가하세요."},
        )

        self.assertNotIn("119", first.draft)
        self.assertIn("119", second.draft)


if __name__ == "__main__":
    unittest.main()
