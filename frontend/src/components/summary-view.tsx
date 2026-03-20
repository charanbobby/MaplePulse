"use client";

import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  BarChart3,
  Users,
  ArrowRight,
} from "lucide-react";
import type { AggregatedResults, Reaction } from "@/lib/types";
import { cn } from "@/lib/cn";

function MetricCard({
  label,
  value,
  subtext,
  color,
}: {
  label: string;
  value: string;
  subtext?: string;
  color: string;
}) {
  return (
    <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-4 shadow-sm">
      <p className="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wide mb-1">
        {label}
      </p>
      <p className={cn("text-2xl font-bold font-[family-name:var(--font-mono)]", color)}>
        {value}
      </p>
      {subtext && (
        <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{subtext}</p>
      )}
    </div>
  );
}

function ToneBar({
  label,
  pct,
  color,
}: {
  label: string;
  pct: number;
  color: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-[var(--color-text-muted)] w-20 text-right">
        {label}
      </span>
      <div className="flex-1 h-4 bg-[var(--color-surface)] rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-700", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-[var(--color-text-muted)] w-10">
        {pct}%
      </span>
    </div>
  );
}

function SentimentDistribution({ reactions }: { reactions: Reaction[] }) {
  const positive = reactions.filter((r) => r.sentiment_score >= 4).length;
  const neutral = reactions.filter(
    (r) => r.sentiment_score === 3
  ).length;
  const negative = reactions.filter((r) => r.sentiment_score <= 2).length;
  const total = reactions.length;

  return (
    <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-4 shadow-sm">
      <p className="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wide mb-3">
        Sentiment Distribution
      </p>
      <div className="flex h-6 rounded-full overflow-hidden">
        {positive > 0 && (
          <div
            className="bg-emerald-500 transition-all duration-700"
            style={{ width: `${(positive / total) * 100}%` }}
          />
        )}
        {neutral > 0 && (
          <div
            className="bg-amber-400 transition-all duration-700"
            style={{ width: `${(neutral / total) * 100}%` }}
          />
        )}
        {negative > 0 && (
          <div
            className="bg-red-400 transition-all duration-700"
            style={{ width: `${(negative / total) * 100}%` }}
          />
        )}
      </div>
      <div className="flex justify-between mt-2 text-xs">
        <span className="text-emerald-600">Positive: {positive}</span>
        <span className="text-amber-600">Neutral: {neutral}</span>
        <span className="text-red-500">Negative: {negative}</span>
      </div>
    </div>
  );
}

interface SummaryViewProps {
  aggregate: AggregatedResults;
  reactions: Reaction[];
  round: 1 | 2;
  onContinue: () => void;
  continueLabel: string;
  canContinue?: boolean;
  /** Round 1 reactions — passed when round=2 so we can show how opinions shifted */
  round1Reactions?: Reaction[];
}

export function SummaryView({
  aggregate,
  reactions,
  round,
  onContinue,
  continueLabel,
  canContinue = true,
  round1Reactions,
}: SummaryViewProps) {
  const sentimentColor =
    aggregate.avg_sentiment >= 3.5
      ? "text-emerald-600"
      : aggregate.avg_sentiment >= 2.5
      ? "text-amber-600"
      : "text-red-500";

  const relevanceColor =
    aggregate.relevance_pct >= 70
      ? "text-emerald-600"
      : aggregate.relevance_pct >= 40
      ? "text-amber-600"
      : "text-red-500";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold font-[family-name:var(--font-heading)]">
            Round {round} Summary
          </h2>
          <p className="text-sm text-[var(--color-text-muted)]">
            Aggregated results from {reactions.length} persona reactions
          </p>
        </div>
        <button
          onClick={onContinue}
          disabled={!canContinue}
          className={cn(
            "flex items-center gap-2 px-4 py-2 text-white rounded-lg text-sm font-medium transition-colors",
            canContinue
              ? "bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] cursor-pointer"
              : "bg-[var(--color-text-light)] cursor-not-allowed opacity-60"
          )}
        >
          {!canContinue && (
            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          )}
          {continueLabel}
          {canContinue && <ArrowRight size={16} />}
        </button>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          label="Avg Sentiment"
          value={aggregate.avg_sentiment.toFixed(1)}
          subtext="out of 5"
          color={sentimentColor}
        />
        <MetricCard
          label="Relevance"
          value={`${aggregate.relevance_pct}%`}
          subtext="weighted relevance"
          color={relevanceColor}
        />
        <MetricCard
          label="Natural Tone"
          value={`${aggregate.tone_distribution.natural || 0}%`}
          subtext="of reactions"
          color="text-emerald-600"
        />
        <MetricCard
          label="Awkward / Offensive"
          value={`${(aggregate.tone_distribution.awkward || 0) + (aggregate.tone_distribution.offensive || 0)}%`}
          subtext="need attention"
          color="text-red-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Sentiment distribution */}
        <SentimentDistribution reactions={reactions} />

        {/* Tone distribution */}
        <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-4 shadow-sm space-y-2">
          <p className="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wide mb-2">
            Tone Fit Distribution
          </p>
          <ToneBar label="Natural" pct={aggregate.tone_distribution.natural || 0} color="bg-emerald-500" />
          <ToneBar label="Acceptable" pct={aggregate.tone_distribution.acceptable || 0} color="bg-blue-500" />
          <ToneBar label="Awkward" pct={aggregate.tone_distribution.awkward || 0} color="bg-amber-500" />
          <ToneBar label="Offensive" pct={aggregate.tone_distribution.offensive || 0} color="bg-red-500" />
        </div>
      </div>

      {/* Cultural flags */}
      {aggregate.top_cultural_flags.length > 0 && (
        <div className="bg-orange-50 rounded-xl border border-orange-200 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={16} className="text-orange-600" />
            <p className="text-sm font-medium text-orange-800">
              Cultural Flags Raised
            </p>
          </div>
          <ul className="space-y-1">
            {aggregate.top_cultural_flags.map((flag) => (
              <li
                key={flag}
                className="text-sm text-orange-700 flex items-start gap-1.5"
              >
                <span className="text-orange-400 mt-1">-</span>
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Per-persona shift: Round 1 → Round 2 */}
      {round === 2 && round1Reactions && round1Reactions.length > 0 && (
        <div className="space-y-3">
          <div>
            <div className="flex items-center gap-2">
              <Users size={16} className="text-[var(--color-text-muted)]" />
              <h3 className="text-sm font-semibold text-[var(--color-text)] uppercase tracking-wide">
                Reaction Comparison by Persona
              </h3>
            </div>
            <p className="text-xs text-[var(--color-text-muted)] mt-1 ml-6">
              Each persona reacted to both messages independently — they have no
              memory of Round 1. Differences reflect how the optimized message
              lands with the same demographic profile, not a change of opinion.
            </p>
          </div>
          {reactions.map((r2) => {
            const r1 = round1Reactions.find(
              (r) => r.persona.uuid === r2.persona.uuid
            );
            if (!r1) return null;
            const sentimentDelta = r2.sentiment_score - r1.sentiment_score;
            const deltaLabel =
              sentimentDelta > 0
                ? `+${sentimentDelta.toFixed(1)}`
                : sentimentDelta.toFixed(1);
            const DeltaIcon =
              sentimentDelta > 0
                ? TrendingUp
                : sentimentDelta < 0
                ? TrendingDown
                : BarChart3;
            const deltaColor =
              sentimentDelta > 0
                ? "text-emerald-600"
                : sentimentDelta < 0
                ? "text-red-500"
                : "text-[var(--color-text-muted)]";
            return (
              <div
                key={r2.persona.uuid}
                className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-4 shadow-sm"
              >
                {/* Persona header + sentiment delta */}
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-semibold text-[var(--color-text)]">
                    {r2.persona.occupation}, {r2.persona.age} —{" "}
                    {r2.persona.planning_area}, {r2.persona.province}
                  </p>
                  <div className={cn("flex items-center gap-1 text-xs font-mono font-medium", deltaColor)}>
                    <DeltaIcon size={14} />
                    <span>{deltaLabel}</span>
                    <span className="text-[var(--color-text-muted)] ml-1">
                      sentiment {r1.sentiment_score}/5 → {r2.sentiment_score}/5
                    </span>
                  </div>
                </div>
                {/* Side-by-side reactions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="rounded-lg bg-[var(--color-surface)] p-3">
                    <p className="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1">
                      Round 1 — Original Message
                    </p>
                    <p className="text-sm italic text-[var(--color-text)]">
                      &ldquo;{r1.reaction}&rdquo;
                    </p>
                  </div>
                  <div className="rounded-lg bg-[var(--color-surface)] p-3">
                    <p className="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1">
                      Round 2 — Optimized Message
                    </p>
                    <p className="text-sm italic text-[var(--color-text)]">
                      &ldquo;{r2.reaction}&rdquo;
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
