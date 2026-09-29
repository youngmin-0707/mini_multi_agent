"""부산 알레르기 안전 안내문의 조사, 작성, 검토 흐름을 제어한다.

Orchestrator는 콘텐츠를 직접 만들지 않는다. Agent 실행 순서, 계약 통과 여부,
Context 전달, 재작성 횟수와 최종 종료 사유만 결정한다.
"""

from pydantic import ValidationError

from app.agents.registry import get_agent
from app.agents.runtime import run_agent
from app.schemas.allergy_contracts import (
    AllergyGuideDraftResult,
    AllergyGuideReviewResult,
    AllergyResearchResult,
    AllergySafetyRequest,
    AllergySafetyRunResult,
    AllergyTraceEvent,
)


def _event(
    trace: list[AllergyTraceEvent],
    actor: str,
    action: str,
    revision: int | None = None,
    details: str | None = None,
) -> None:
    """순번이 포함된 Trace Event를 실행 기록에 추가한다."""

    trace.append(
        AllergyTraceEvent(
            step=len(trace) + 1,
            actor=actor,
            action=action,
            revision=revision,
            details=details,
        )
    )


def _failure_reason(agent_result: dict[str, object]) -> str:
    """Agent 실패가 Tool 계층에서 발생했는지 일반 실패인지 구분한다."""

    error = str(agent_result.get("error") or "")
    return "tool_error" if "MCP" in error or "Tool" in error else "contract_rejected"


async def run_allergy_safety_guide(
    request: AllergySafetyRequest,
) -> AllergySafetyRunResult:
    """세 Agent를 실행하고 Reviewer 통과 또는 최대 3회에서 종료한다."""

    trace: list[AllergyTraceEvent] = []
    _event(trace, "orchestrator", "request_validated")

    _event(trace, "allergy_research_agent", "started")
    research_run = await run_agent(
        get_agent("allergy_research_agent"),
        request.message,
    )
    if research_run.get("result") is None:
        reason = _failure_reason(research_run)
        _event(trace, "allergy_research_agent", "failed", details=str(research_run.get("error")))
        return AllergySafetyRunResult(
            status="failed",
            termination_reason=reason,
            revision_count=0,
            error=str(research_run.get("error") or "Research Agent가 실패했습니다."),
            trace=trace,
        )

    try:
        research = AllergyResearchResult.model_validate(research_run["result"])
    except ValidationError as error:
        _event(trace, "contract_guard", "research_rejected", details=str(error))
        return AllergySafetyRunResult(
            status="failed",
            termination_reason="contract_rejected",
            revision_count=0,
            error=str(error),
            trace=trace,
        )


    if not research.completed:
        _event(trace, "contract_guard", "research_incomplete")
        return AllergySafetyRunResult(
            status="failed",
            termination_reason="research_failed",
            revision_count=0,
            error="조사 결과가 완료 상태가 아닙니다.",
            research=research,
            trace=trace,
        )

    _event(trace, "contract_guard", "research_verified")
    feedback: str | None = None
    final_review: AllergyGuideReviewResult | None = None

    for revision in range(1, 4):
        writer_context = {
            "research_result": research.model_dump(),
            "feedback": feedback,
            "revision": revision,
        }
        _event(trace, "allergy_guide_writer_agent", "started", revision)
        writer_run = await run_agent(
            get_agent("allergy_guide_writer_agent"),
            request.message,
            context=writer_context,
        )
        if writer_run.get("result") is None:
            reason = _failure_reason(writer_run)
            _event(trace, "allergy_guide_writer_agent", "failed", revision, str(writer_run.get("error")))
            return AllergySafetyRunResult(
                status="failed",
                termination_reason=reason,
                revision_count=revision,
                error=str(writer_run.get("error") or "Writer Agent가 실패했습니다."),
                research=research,
                trace=trace,
            )

        try:
            draft = AllergyGuideDraftResult.model_validate(writer_run["result"])
        except ValidationError as error:
            _event(trace, "contract_guard", "draft_rejected", revision, str(error))
            return AllergySafetyRunResult(
                status="failed",
                termination_reason="contract_rejected",
                revision_count=revision,
                error=str(error),
                research=research,
                trace=trace,
            )

        if draft.revision != revision:
            error = "초안의 수정 회차가 현재 실행 회차와 일치하지 않습니다."
            _event(trace, "contract_guard", "draft_rejected", revision, error)
            return AllergySafetyRunResult(
                status="failed",
                termination_reason="contract_rejected",
                revision_count=revision,
                error=error,
                research=research,
                trace=trace,
            )

        _event(trace, "contract_guard", "draft_verified", revision)
        reviewer_context = {
            "research_result": research.model_dump(),
            "draft_result": draft.model_dump(),
        }
        _event(trace, "allergy_guide_reviewer_agent", "started", revision)
        reviewer_run = await run_agent(
            get_agent("allergy_guide_reviewer_agent"),
            request.message,
            context=reviewer_context,
        )
        if reviewer_run.get("result") is None:
            reason = _failure_reason(reviewer_run)
            _event(trace, "allergy_guide_reviewer_agent", "failed", revision, str(reviewer_run.get("error")))
            return AllergySafetyRunResult(
                status="failed",
                termination_reason=reason,
                revision_count=revision,
                error=str(reviewer_run.get("error") or "Reviewer Agent가 실패했습니다."),
                research=research,
                trace=trace,
            )

        try:
            final_review = AllergyGuideReviewResult.model_validate(reviewer_run["result"])
        except ValidationError as error:
            _event(trace, "contract_guard", "review_rejected", revision, str(error))
            return AllergySafetyRunResult(
                status="failed",
                termination_reason="contract_rejected",
                revision_count=revision,
                error=str(error),
                research=research,
                trace=trace,
            )

        if final_review.passed:
            _event(trace, "allergy_guide_reviewer_agent", "passed", revision)
            _event(trace, "orchestrator", "evaluation_passed", revision)
            return AllergySafetyRunResult(
                status="completed",
                final_guide=draft.draft,
                termination_reason="evaluation_passed",
                revision_count=revision,
                research=research,
                final_review=final_review,
                trace=trace,
            )

        feedback = final_review.feedback
        _event(trace, "allergy_guide_reviewer_agent", "rejected", revision, feedback)

    _event(trace, "orchestrator", "max_revisions_exceeded", 3)
    return AllergySafetyRunResult(
        status="failed",
        termination_reason="max_revisions_exceeded",
        revision_count=3,
        error="세 번의 수정 안에 검토를 통과하지 못했습니다.",
        research=research,
        final_review=final_review,
        trace=trace,
    )
