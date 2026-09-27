import Link from "next/link";
import { notFound } from "next/navigation";
import { AutoRefresh } from "@/components/auto-refresh";
import { ComparisonChart } from "@/components/comparison-chart";
import { DiffViewer } from "@/components/diff-viewer";
import { MetricCard } from "@/components/metric-card";
import { PhaseTimeline } from "@/components/phase-timeline";
import { StatusBadge } from "@/components/status-badge";
import { getRunDetail } from "@/lib/data";
import {
  categoryLabel,
  formatConfidence,
  formatDateTime,
  formatDuration,
  formatMs,
  formatPercent,
} from "@/lib/format";
import { getRunProgress, isActiveStatus } from "@/lib/progress";

export const dynamic = "force-dynamic";

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const detail = await getRunDetail(id);
  if (!detail) {
    notFound();
  }
  const { run, samples, samples_after, phases, finding, diagnosis, patch, verification } = detail;
  const isActive = isActiveStatus(run.status);
  const progress = getRunProgress(run, phases);
  const improvement = verification?.improvement_pct ?? {};
  const isLiveEvidence = run.mode === "live" && run.summary.telemetry_source === "live";

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 border-b border-white/10 pb-6 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <Link href="/" className="text-xs text-zinc-500 transition hover:text-cyan-300">
            ← All runs
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{run.scenario_name}</h1>
            <StatusBadge status={run.status} />
            <AutoRefresh active={isActive} intervalMs={5000} />
          </div>
          <p className="font-mono text-xs text-zinc-500">
            {run.id} · {run.target_repo}@{run.commit_sha} · {run.mode} mode
          </p>
          {isActive ? (
            <div className="max-w-md">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-cyan-300">{progress.label}</span>
                <span className="font-mono text-zinc-500">
                  phase {Math.min(progress.donePhases + 1, progress.totalPhases)}/
                  {progress.totalPhases} · {progress.percent}%
                </span>
              </div>
              <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-cyan-400 transition-all duration-700"
                  style={{ width: `${progress.percent}%` }}
                />
              </div>
            </div>
          ) : null}
        </div>
        <div className="text-left text-xs text-zinc-500 sm:text-right">
          <p>Started {formatDateTime(run.started_at)} UTC</p>
          <p>Finished {formatDateTime(run.finished_at)} UTC</p>
          {patch?.pr_url ? (
            <a
              href={patch.pr_url}
              className="mt-1 inline-block text-cyan-300 underline-offset-4 hover:underline"
            >
              View generated PR →
            </a>
          ) : null}
        </div>
      </div>

      <section
        className={`rounded-xl border p-4 ${
          isLiveEvidence
            ? "border-emerald-500/25 bg-emerald-500/5"
            : "border-amber-500/25 bg-amber-500/5"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className={`font-mono text-xs font-semibold ${isLiveEvidence ? "text-emerald-300" : "text-amber-300"}`}>
            {isLiveEvidence ? "LIVE EVIDENCE" : "SIMULATED DEMONSTRATION"}
          </p>
          <p className="text-xs text-zinc-400">
            {isLiveEvidence
              ? "Measured with k6 + Toxiproxy before and after rebuilding the Bob-patched service."
              : "Deterministic telemetry for UI and pipeline development; not a physical resilience claim."}
          </p>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          label="Time to collapse"
          value={formatDuration(run.summary.time_to_collapse_s)}
          sub={run.collapse_detected ? "collapse reproduced under chaos" : "no collapse detected"}
          tone="bad"
        />
        <MetricCard
          label="p95 latency"
          value={
            <span>
              {formatMs(run.summary.p95_before_ms)}{" "}
              <span className="text-sm text-zinc-500">→</span>{" "}
              {formatMs(run.summary.p95_after_ms)}
            </span>
          }
          sub="before → after verified fix"
          tone="good"
        />
        <MetricCard
          label="Error rate"
          value={`${formatPercent(run.summary.error_rate_before)} → ${formatPercent(run.summary.error_rate_after)}`}
          sub="5xx / timeouts before → after"
          tone="info"
        />
        <MetricCard
          label="Diagnosis time"
          value={
            typeof run.summary.diagnosis_minutes_ai === "number"
              ? `${run.summary.diagnosis_minutes_ai.toFixed(1)} min`
              : "—"
          }
          sub={
            typeof run.summary.diagnosis_minutes_manual_estimate === "number"
              ? `vs ~${run.summary.diagnosis_minutes_manual_estimate} min manual SRE`
              : "AI vs manual SRE estimate"
          }
          tone="info"
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <ComparisonChart title="Latency under identical chaos load" before={samples} after={samples_after} metric="p95" />
        <ComparisonChart title="Error rate under identical chaos load" before={samples} after={samples_after} metric="errorRate" />
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
        <div className="space-y-6">
          <div className="rounded-xl border border-white/10 bg-zinc-900/60 p-5">
            <h2 className="mb-4 text-sm font-medium text-zinc-200">Execution timeline</h2>
            <PhaseTimeline phases={phases} />
          </div>

          {finding ? (
            <div className="rounded-xl border border-white/10 bg-zinc-900/60 p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-medium text-zinc-200">Root cause finding</h2>
                <span className="rounded-full bg-rose-500/15 px-2.5 py-1 text-xs font-medium text-rose-300 ring-1 ring-inset ring-rose-500/30">
                  {categoryLabel(finding.category)}
                </span>
              </div>
              <p className="mt-3 text-xs text-zinc-500">
                Confidence {formatConfidence(finding.confidence)} ·{" "}
                <span className="font-mono">
                  {finding.file_path}
                </span>{" "}
                {finding.symbol ? (
                  <span className="font-mono text-cyan-300">{finding.symbol}</span>
                ) : null}
              </p>
              <p className="mt-3 text-sm leading-relaxed text-zinc-300">{finding.root_cause}</p>
              <ul className="mt-4 space-y-2">
                {finding.evidence.map((item) => (
                  <li key={item} className="flex gap-2 text-xs leading-relaxed text-zinc-400">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-cyan-400" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>

        <div className="space-y-6">
          {verification ? (
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-medium text-emerald-200">Resilience verification</h2>
                <span className="rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-medium text-emerald-300 ring-1 ring-inset ring-emerald-500/30">
                  {verification.stable ? "STABLE AFTER FIX" : "STILL UNSTABLE"}
                </span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3">
                {Object.entries(improvement).map(([key, value]) => (
                  <div key={key} className="rounded-lg border border-white/10 bg-zinc-950/60 p-3">
                    <p className="text-[11px] uppercase tracking-wider text-zinc-500">
                      {key.replace(/_/g, " ")}
                    </p>
                    <p className="mt-1 text-lg font-semibold tabular-nums text-emerald-300">
                      −{value.toFixed(1)}%
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {diagnosis ? (
            <div className="rounded-xl border border-white/10 bg-zinc-900/60 p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-medium text-zinc-200">Repository-aware diagnosis</h2>
                <div className="text-right">
                  <span className="block font-mono text-[11px] text-zinc-500">
                    {diagnosis.model}
                  </span>
                  {diagnosis.bob_task_id ? (
                    <span className="block font-mono text-[11px] text-amber-300">
                      IBM Bob task {diagnosis.bob_task_id.slice(0, 8)}
                      {typeof diagnosis.bobcoins === "number"
                        ? ` · ${diagnosis.bobcoins.toFixed(2)} Bobcoins consumed`
                        : ""}
                    </span>
                  ) : null}
                </div>
              </div>
              <div className="mt-3 space-y-2 text-sm leading-relaxed text-zinc-300">
                {diagnosis.analysis_md.split("\n").map((line, index) => {
                  if (line.startsWith("## ")) {
                    return (
                      <h3 key={index} className="pt-2 text-xs font-semibold uppercase tracking-wider text-cyan-300">
                        {line.replace("## ", "")}
                      </h3>
                    );
                  }
                  if (line.trim() === "") {
                    return null;
                  }
                  return <p key={index}>{line}</p>;
                })}
              </div>
              <p className="mt-4 rounded-lg border border-white/10 bg-zinc-950/60 p-3 text-xs text-zinc-400">
                <span className="font-medium text-zinc-300">Proposed change: </span>
                {diagnosis.proposed_change}
              </p>
              {diagnosis.target_files && diagnosis.target_files.length > 0 ? (
                <p className="mt-3 text-xs text-zinc-400">
                  <span className="font-medium text-zinc-300">Identified locations: </span>
                  <span className="font-mono text-cyan-300">
                    {diagnosis.target_files.join(", ")}
                  </span>
                </p>
              ) : null}
            </div>
          ) : null}

          {patch ? (
            <div className="rounded-xl border border-white/10 bg-zinc-900/60 p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-medium text-zinc-200">Generated patch</h2>
                <span className="font-mono text-[11px] text-zinc-500">{patch.branch}</span>
              </div>
              <p className="mt-2 text-xs text-zinc-500">
                {patch.files_changed.join(", ")}
              </p>
              {patch.source === "bob-shell" ? (
                <p className="mt-1 font-mono text-[11px] text-amber-300">
                  Patch generated by IBM Bob
                  {patch.bob_task_id ? ` · task ${patch.bob_task_id.slice(0, 8)}` : ""}
                  {typeof patch.bobcoins === "number"
                    ? ` · ${patch.bobcoins.toFixed(2)} Bobcoins consumed`
                    : ""}
                </p>
              ) : (
                <p className="mt-1 font-mono text-[11px] text-zinc-500">
                  Template patch (Bob Shell unavailable)
                </p>
              )}
              <div className="mt-3">
                <DiffViewer diff={patch.diff} />
              </div>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}
