"""알레르기 Agent 출력 계약의 정상 상태와 모순 상태를 검사한다."""

import sys
import unittest
from pathlib import Path

from pydantic import ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.schemas.allergy_contracts import (  # noqa: E402
    AllergyGuideDraftResult,
    AllergyGuideReviewResult,
    AllergyResearchResult,
)


class AllergyContractTests(unittest.TestCase):
    """다음 Agent에 전달해도 되는 데이터 모양인지 확인한다."""

    def test_valid_results_pass_each_contract(self) -> None:
        """세 역할의 정상적인 결과가 모두 계약을 통과한다."""

        research = AllergyResearchResult.model_validate({
            "facts": [{"fact": "부산박물관은 실내 장소다.", "source": "place-source"}],
            "safety_guidance": [{"guidance": "교차접촉을 확인한다.", "source": "safety-source"}],
            "completed": True,
        })
        draft = AllergyGuideDraftResult.model_validate({
            "draft": "출처를 확인하고 교차접촉 가능성을 문의한다.",
            "used_sources": ["place-source", "safety-source"],
            "included_requirements": ["source", "cross_contact"],
            "revision": 1,
        })
        review = AllergyGuideReviewResult.model_validate({
            "passed": True,
            "missing_requirements": [],
            "unsupported_claims": [],
            "feedback": "모든 조건을 충족했습니다.",
        })

        self.assertTrue(research.completed)
        self.assertEqual(draft.revision, 1)
        self.assertTrue(review.passed)

    def test_passed_review_rejects_problem_lists(self) -> None:
        """문제가 남아 있는데 통과로 표시한 모순된 검토 결과를 거부한다."""

        with self.assertRaises(ValidationError):
            AllergyGuideReviewResult.model_validate({
                "passed": True,
                "missing_requirements": ["119 안내"],
                "unsupported_claims": [],
                "feedback": "통과",
            })

    def test_incomplete_research_may_report_empty_evidence(self) -> None:
        """조회 실패 상태는 빈 목록과 completed=False로 안전하게 표현한다."""

        result = AllergyResearchResult.model_validate({
            "facts": [],
            "safety_guidance": [],
            "completed": False,
        })
        self.assertFalse(result.completed)


if __name__ == "__main__":
    unittest.main()
