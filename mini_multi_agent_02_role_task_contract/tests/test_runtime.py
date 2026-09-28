import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.agents.runtime import tool_arguments  # noqa: E402


class ToolArgumentTests(unittest.TestCase):
    def test_budget_arguments_parse_korean_request(self) -> None:
        arguments = tool_arguments("get_budget_reference", "부산 2박 3일 여행, 1명, 대중교통 이용, 총예산 60만 원")
        self.assertEqual(arguments, {"city": "부산", "days": 3, "people": 1, "total_budget": 600_000})

    def test_people_without_subject_particle(self) -> None:
        arguments = tool_arguments("get_budget_reference", "부산 1박 2일 여행, 2명, 예산 80만원")
        self.assertEqual(arguments["people"], 2)

    def test_similar_unit_is_not_treated_as_people(self) -> None:
        arguments = tool_arguments("get_budget_reference", "부산 1박 2일 여행에서 2인치 화면을 보고 예산은 40만원")
        self.assertIsNone(arguments)

    def test_allergy_city_arguments_parse_possessive_request(self) -> None:
        """'부산의'처럼 조사와 함께 적힌 도시 이름도 Tool 인자로 만든다."""

        arguments = tool_arguments(
            "get_allergy_guidance",
            "부산의 장소와 알레르기 안전 수칙을 조사해 줘.",
        )
        self.assertEqual(arguments, {"city": "부산"})


if __name__ == "__main__":
    unittest.main()
