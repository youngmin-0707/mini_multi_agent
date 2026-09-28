"""부산 알레르기 안전 안내 시나리오의 구조화된 계약을 정의한다.

각 Agent가 자유로운 문자열 대신 일정한 구조의 결과를 반환하게 한다.
Research, Writer, Reviewer의 출력은 다음 단계로 전달되기 전에 이 파일의
Pydantic 모델로 검증된다.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ResearchFact(BaseModel):
    """Research Agent가 수집한 출처 포함 사실 한 건이다."""

    fact: str = Field(min_length=1)
    source: str = Field(min_length=1)


class SafetyGuidance(BaseModel):
    """알레르기 안전 행동 지침과 출처를 한 묶음으로 표현한다."""

    guidance: str = Field(min_length=1)
    emergency: bool = False
    source: str = Field(min_length=1)


class AllergyResearchResult(BaseModel):
    """Research Agent가 Writer Agent에게 전달하는 검증 대상 결과다."""

    agent_id: Literal["allergy_research_agent"] = "allergy_research_agent"
    facts: list[ResearchFact] = Field(default_factory=list, max_length=10)
    safety_guidance: list[SafetyGuidance] = Field(default_factory=list, max_length=10)
    completed: bool

    @model_validator(mode="after")
    def completed_requires_evidence(self) -> "AllergyResearchResult":
        """근거가 없는 조사 결과를 완료 상태로 표시하지 못하게 한다."""

        if self.completed and (not self.facts or not self.safety_guidance):
            raise ValueError("완료된 조사 결과에는 사실과 안전 지침이 모두 필요합니다.")
        return self


class AllergyGuideDraftResult(BaseModel):
    """Writer Agent가 작성한 안내문과 근거 사용 내역을 표현한다."""

    agent_id: Literal["allergy_guide_writer_agent"] = "allergy_guide_writer_agent"
    draft: str = Field(min_length=1)
    used_sources: list[str] = Field(min_length=1, max_length=10)
    included_requirements: list[str] = Field(default_factory=list, max_length=10)
    revision: int = Field(ge=1, le=3)


class AllergyGuideReviewResult(BaseModel):
    """Reviewer Agent의 통과 여부와 다음 수정에 필요한 피드백이다."""

    agent_id: Literal["allergy_guide_reviewer_agent"] = "allergy_guide_reviewer_agent"
    passed: bool
    missing_requirements: list[str] = Field(default_factory=list, max_length=10)
    unsupported_claims: list[str] = Field(default_factory=list, max_length=10)
    feedback: str

    @model_validator(mode="after")
    def review_state_must_be_consistent(self) -> "AllergyGuideReviewResult":
        """통과 상태와 문제 목록이 서로 모순되지 않도록 검증한다."""

        has_problems = bool(self.missing_requirements or self.unsupported_claims)
        if self.passed and has_problems:
            raise ValueError("통과한 검토 결과에는 누락 조건이나 근거 없는 주장이 없어야 합니다.")
        if not self.passed and not self.feedback.strip():
            raise ValueError("통과하지 못한 검토 결과에는 수정 피드백이 필요합니다.")
        return self


class AllergySafetyRequest(BaseModel):
    """Swagger에서 알레르기 안전 안내 흐름을 시작할 때 받는 요청이다."""

    message: str = Field(min_length=3, max_length=1000)


class AllergyTraceEvent(BaseModel):
    """어떤 실행 주체가 무슨 행동을 했는지 보여 주는 학습용 기록이다."""

    step: int = Field(ge=1)
    actor: str
    action: str
    revision: int | None = None
    details: str | None = None


class AllergySafetyRunResult(BaseModel):
    """전체 Orchestration이 API 호출자에게 반환하는 최종 계약이다."""

    status: Literal["completed", "failed"]
    final_guide: str | None = None
    termination_reason: Literal[
        "evaluation_passed",
        "research_failed",
        "contract_rejected",
        "tool_error",
        "max_revisions_exceeded",
    ]
    revision_count: int = Field(ge=0, le=3)
    error: str | None = None
    research: AllergyResearchResult | None = None
    final_review: AllergyGuideReviewResult | None = None
    trace: list[AllergyTraceEvent] = Field(default_factory=list)
