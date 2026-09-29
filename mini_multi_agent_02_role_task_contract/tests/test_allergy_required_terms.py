"""출처 URL이 알레르기 필수 안내의 증거로 오인되지 않는지 검사한다."""

import unittest
from unittest.mock import patch

from mcp_server.tools.travel_tools import check_required_terms


REQUIREMENTS = [
    {"requirement_key": key, "description": key, "required_term": term,
     "check_type": "emergency_report" if key == "emergency" else "literal"}
    for key, term in (
        ("source", "출처"),
        ("cross_contact", "교차접촉"),
        ("emergency", "119"),
        ("approval", "승인"),
    )
]


class AllergyRequiredTermsTests(unittest.TestCase):
    def check(self, draft: str) -> dict:
        with patch(
            "mcp_server.tools.travel_tools.db.find_quality_requirements",
            return_value=REQUIREMENTS,
        ):
            return check_required_terms(draft, "allergy_safety")

    def test_source_url_does_not_satisfy_emergency_requirement(self) -> None:
        result = self.check("교차접촉 확인. 출처: https://www.119.go.kr/ 사용자 승인 필요.")
        self.assertFalse(result["passed"])
        self.assertFalse(next(c for c in result["checks"] if c["requirement_key"] == "emergency")["included"])

    def test_bare_number_does_not_satisfy_emergency_requirement(self) -> None:
        self.assertFalse(self.check("교차접촉 확인. 출처 표시. 119. 사용자 승인 필요.")["passed"])

    def test_emergency_report_in_body_passes(self) -> None:
        result = self.check("교차접촉 확인. 중증 증상이 의심되면 즉시 119에 신고한다. 출처: https://www.119.go.kr/ 사용자 승인 필요.")
        self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()
