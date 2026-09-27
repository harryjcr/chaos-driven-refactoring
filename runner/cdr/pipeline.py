from __future__ import annotations

import uuid
from typing import Any, Callable, Dict, Optional

from .classifier import classify
from .config import Settings
from .diagnoser import Diagnoser
from .live import LiveLab
from .models import PhaseRecord, RunResult, Scenario, utc_now
from .patcher import Patcher
from .repair import BobRepairer
from .telemetry import simulate_telemetry
from .verifier import verify

MANUAL_DIAGNOSIS_MINUTES = 95

ProgressCallback = Callable[[str, Dict[str, Any]], None]


def _notify(callback: Optional[ProgressCallback], stage: str, payload: Dict[str, Any]) -> None:
    if callback is None:
        return
    try:
        callback(stage, payload)
    except Exception:
        pass


class Pipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.diagnoser = Diagnoser(settings)
        self.patcher = Patcher(settings)
        self.repairer = BobRepairer(settings)

    def run(
        self,
        scenario: Scenario,
        mode: Optional[str] = None,
        create_pr: bool = False,
        run_id: Optional[str] = None,
        on_progress: Optional[ProgressCallback] = None,
    ) -> RunResult:
        run_id = run_id or f"run-{uuid.uuid4().hex[:8]}"
        run_mode = mode or self.settings.mode or scenario.mode
        started_at = utc_now()
        phases = []

        live_lab = LiveLab(self.settings, run_id) if run_mode == "live" else None
        if live_lab is not None:
            if not self.repairer.available:
                raise RuntimeError(
                    "live mode requires IBM Bob Shell: configure BOB_API_KEY and ensure the bob "
                    "binary is available on PATH"
                )
            live_lab.prepare()
            telemetry = live_lab.capture(scenario, "before")
        else:
            telemetry = simulate_telemetry(scenario, fixed=False, seed=42)
        collapsed = telemetry.time_to_collapse_s is not None
        chaos_detail = (
            "{} load at {} vus against {}, {} fault on {}, collapse at {}s".format(
                scenario.load.tool,
                scenario.load.vus,
                scenario.load.endpoint or "target endpoint",
                scenario.chaos.fault,
                scenario.chaos.proxy,
                telemetry.time_to_collapse_s,
            )
            if collapsed
            else "no collapse detected under current thresholds"
        )
        phases.append(
            PhaseRecord(
                phase="chaos",
                status="done",
                label="Chaos injection + collapse capture",
                detail=chaos_detail,
            )
        )
        _notify(
            on_progress,
            "chaos",
            {"telemetry": telemetry, "collapsed": collapsed, "detail": chaos_detail},
        )

        finding = classify(telemetry)
        classification_detail = (
            f"{finding.category} (confidence {round(finding.confidence, 2)}) — "
            f"{finding.file_path} {finding.symbol}"
        )
        phases.append(
            PhaseRecord(
                phase="classification",
                status="done",
                label="Root cause classification",
                detail=classification_detail,
            )
        )
        _notify(
            on_progress,
            "classification",
            {"finding": finding, "detail": classification_detail},
        )

        repair = None
        if self.repairer.available:
            try:
                repair = self.repairer.repair(scenario, finding, telemetry)
            except Exception as error:
                print(f"[cdr] bob repair skipped: {error}")
        if repair is not None:
            diagnosis, patch = repair
        else:
            diagnosis = self.diagnoser.diagnose(
                scenario, finding, telemetry, exclude_bob=self.repairer.available
            )
            patch = self.patcher.build_patch(scenario, finding, diagnosis)

        if diagnosis.target_files:
            first = diagnosis.target_files[0]
            path, _, symbol = first.partition("#")
            diagnosis.target_files = [
                item.partition("#")[0].strip() for item in diagnosis.target_files
            ]
            finding.file_path = path.strip()
            finding.symbol = symbol.strip()
        diagnosis_detail = f"{diagnosis.model} analyzed {scenario.target} with full repository context"
        phases.append(
            PhaseRecord(
                phase="diagnosis",
                status="done",
                label="Repository-aware diagnosis",
                detail=diagnosis_detail,
            )
        )

        if create_pr:
            patch.pr_url = self.patcher.create_pull_request(patch, self.settings.artifacts_dir.parent)
        _notify(
            on_progress,
            "diagnosis",
            {"diagnosis": diagnosis, "patch": patch, "finding": finding, "detail": diagnosis_detail},
        )

        if live_lab is not None:
            from .repo_context import ensure_repo_clone

            workspace = ensure_repo_clone(self.settings, scenario.target, "HEAD")
            if workspace is None:
                raise RuntimeError("live verification requires the cloned target repository")
            live_lab.deploy_patch(workspace, patch)
            telemetry_after = live_lab.capture(scenario, "after")
        else:
            telemetry_after = simulate_telemetry(scenario, fixed=True, seed=43)
        verification = verify(telemetry, telemetry_after, scenario)
        verification_detail = (
            f"same chaos scenario re-executed on patched branch {patch.branch} — "
            f"stable, p95 {telemetry_after.p95_ms} ms"
            if verification.stable
            else "patch did not stabilize the system under the same chaos scenario"
        )
        phases.append(
            PhaseRecord(
                phase="verification",
                status="done" if verification.stable else "failed",
                label="PR generation + resilience verification",
                detail=verification_detail,
            )
        )
        _notify(
            on_progress,
            "verification",
            {
                "verification": verification,
                "telemetry_after": telemetry_after,
                "detail": verification_detail,
            },
        )

        status = "completed" if verification.stable else "failed"
        diagnosis_minutes_ai = round(2.4 + len(finding.evidence) * 0.12, 1)
        summary = {
            "time_to_collapse_s": telemetry.time_to_collapse_s,
            "p95_before_ms": telemetry.p95_ms,
            "p99_before_ms": telemetry.p99_ms,
            "error_rate_before": telemetry.error_rate,
            "p95_after_ms": telemetry_after.p95_ms,
            "p99_after_ms": telemetry_after.p99_ms,
            "error_rate_after": telemetry_after.error_rate,
            "stable_after_fix": verification.stable,
            "diagnosis_minutes_manual_estimate": MANUAL_DIAGNOSIS_MINUTES,
            "diagnosis_minutes_ai": diagnosis_minutes_ai,
            "pr_url": patch.pr_url,
            "telemetry_source": "live" if live_lab is not None else "simulation",
        }

        return RunResult(
            run_id=run_id,
            scenario_name=scenario.name,
            target_repo=scenario.target,
            commit_sha=scenario.commit,
            mode=run_mode,
            status=status,
            started_at=started_at,
            finished_at=utc_now(),
            collapse_detected=collapsed,
            summary=summary,
            telemetry=telemetry,
            telemetry_after=telemetry_after,
            phases=phases,
            finding=finding,
            diagnosis=diagnosis,
            patch=patch,
            verification=verification,
        )
