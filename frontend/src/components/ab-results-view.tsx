"use client";

import { Trophy, BarChart3, Users, ChevronDown } from "lucide-react";
import type { ABReaction, ABSummary, VariantSummary } from "@/lib/types";

interface ABResultsViewProps {
  reactions: ABReaction[];
  summary: ABSummary | null;
  variants: string[];
  respondingCount: number;
  totalPanel: number;
  isComplete: boolean;
  onRestart: () => void;
}

function SentimentBar({ value, max = 5 }: { value: number; max?: number }) {
  const pct = (value / max) * 100;
  const color =
    value >= 4 ? "bg-emerald-500" : value >= 3 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-[var(--color-bg)] rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold w-8 text-right">{value.toFixed(1)}</span>
    </div>
  );
}

function ToneBar({ distribution }: { distribution: Record<string, number> }) {
  const colors: Record<string, string> = {
    natural: "bg-emerald-500",
    acceptable: "bg-blue-400",
    awkward: "bg-amber-500",
    offensive: "bg-red-500",
  };
  return (
    <div className="space-y-1">
      {["natural", "acceptable", "awkward", "offensive"].map((tone) => {
        const pct = distribution[tone] || 0;
        return (
          <div key={tone} className="flex items-center gap-2 text-[10px]">
            <span className="w-16 text-[var(--color-text-muted)] capitalize">{tone}</span>
            <div className="flex-1 h-1.5 bg-[var(--color-bg)] rounded-full overflow-hidden">
              <div className={`h-full ${colors[tone]} rounded-full`} style={{ width: `${pct}%` }} />
            </div>
            <span className="w-8 text-right text-[var(--color-text-muted)]">{pct}%</span>
          </div>
        );
      })}
    </div>
  );
}

function VariantCard({ vs, isWinner }: { vs: VariantSummary; isWinner: boolean }) {
  return (
    <div
      className={`rounded-xl border shadow-sm p-5 transition-all ${
        isWinner
          ? "border-[var(--color-primary)] bg-[var(--color-primary)]/5 ring-2 ring-[var(--color-primary)]/20"
          : "border-[var(--color-border)] bg-[var(--color-bg-card)]"
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-[var(--color-primary)]">
            Variant {vs.variant_label}
          </span>
          {isWinner && (
            <span className="flex items-center gap-1 text-xs font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
              <Trophy size={12} />
              Winner
            </span>
          )}
        </div>
        <span className="text-2xl font-bold text-[var(--color-primary)]">
          {vs.preference_pct}%
        </span>
      </div>

      <p className="text-sm text-[var(--color-text)] mb-4 italic">
        &ldquo;{vs.variant_text}&rdquo;
      </p>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-[10px] uppercase tracking-wide text-[var(--color-text-muted)] mb-1 block">
            Avg Sentiment
          </label>
          <SentimentBar value={vs.avg_sentiment} />
        </div>
        <div>
          <label className="text-[10px] uppercase tracking-wide text-[var(--color-text-muted)] mb-1 block">
            Relevance
          </label>
          <div className="text-sm font-semibold">{vs.relevance_pct}%</div>
        </div>
      </div>

      <div className="mt-3">
        <label className="text-[10px] uppercase tracking-wide text-[var(--color-text-muted)] mb-1 block">
          Tone Distribution
        </label>
        <ToneBar distribution={vs.tone_distribution} />
      </div>

      {vs.top_cultural_flags.length > 0 && (
        <div className="mt-3">
          <label className="text-[10px] uppercase tracking-wide text-[var(--color-text-muted)] mb-1 block">
            Cultural Flags
          </label>
          <div className="flex flex-wrap gap-1">
            {vs.top_cultural_flags.map((flag, i) => (
              <span
                key={i}
                className="text-[10px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200"
              >
                {flag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function ABResultsView({
  reactions,
  summary,
  variants,
  respondingCount,
  totalPanel,
  isComplete,
  onRestart,
}: ABResultsViewProps) {
  return (
    <div className="space-y-6">
      {/* Progress header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold font-[family-name:var(--font-heading)]">
            A/B Test Results
          </h2>
          <p className="text-sm text-[var(--color-text-muted)]">
            {isComplete
              ? `${reactions.filter((r) => !r.error).length} personas responded`
              : `${respondingCount} of ${totalPanel} personas responding...`}
          </p>
        </div>
        {isComplete && (
          <button
            onClick={onRestart}
            className="px-4 py-2 bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
          >
            New Test
          </button>
        )}
      </div>

      {/* Progress bar */}
      {!isComplete && (
        <div className="h-2 bg-[var(--color-bg)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--color-primary)] rounded-full transition-all duration-500"
            style={{ width: `${(respondingCount / totalPanel) * 100}%` }}
          />
        </div>
      )}

      {/* Summary cards — side by side */}
      {summary && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <BarChart3 size={18} className="text-[var(--color-primary)]" />
            <h3 className="text-lg font-semibold">Comparison</h3>
            <span className="text-xs text-[var(--color-text-muted)]">
              {summary.total_respondents} respondents &middot; {summary.elapsed}s
            </span>
          </div>

          <div className={`grid gap-4 ${summary.variant_summaries.length <= 2 ? "grid-cols-1 lg:grid-cols-2" : "grid-cols-1 lg:grid-cols-3"}`}>
            {summary.variant_summaries.map((vs) => (
              <VariantCard
                key={vs.variant_index}
                vs={vs}
                isWinner={vs.variant_index === summary.winner_index}
              />
            ))}
          </div>
        </div>
      )}

      {/* Individual reactions (collapsible) */}
      {reactions.length > 0 && (
        <details className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] shadow-sm">
          <summary className="px-4 py-3 text-sm font-medium cursor-pointer select-none flex items-center gap-2">
            <ChevronDown size={14} />
            <Users size={14} />
            Individual Reactions ({reactions.filter((r) => !r.error).length})
          </summary>
          <div className="px-4 py-3 space-y-4 border-t border-[var(--color-border)] max-h-[600px] overflow-y-auto">
            {reactions
              .filter((r) => !r.error)
              .map((r, i) => (
                <div
                  key={r.persona_id + "-" + i}
                  className="border-b border-[var(--color-border)] pb-4 last:border-0 last:pb-0"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-semibold text-[var(--color-primary)]">
                      {r.age} {r.sex}
                    </span>
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {r.occupation} &middot; {r.city}, {r.province}
                    </span>
                    <span className="ml-auto text-xs font-semibold text-[var(--color-primary)]">
                      Prefers {String.fromCharCode(64 + r.preferred_variant)}
                    </span>
                  </div>

                  <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${variants.length}, 1fr)` }}>
                    {r.variant_reactions.map((vr, vi) => (
                      <div
                        key={vi}
                        className={`rounded-lg p-2 text-xs ${
                          r.preferred_variant === vi + 1
                            ? "bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30"
                            : "bg-[var(--color-bg)]"
                        }`}
                      >
                        <div className="flex items-center gap-1 mb-1">
                          <span className="font-semibold">{String.fromCharCode(65 + vi)}</span>
                          <span className="text-[var(--color-text-muted)]">
                            {vr.sentiment_score}/5
                          </span>
                          <span
                            className={
                              vr.tone_fit === "natural"
                                ? "text-emerald-600"
                                : vr.tone_fit === "awkward"
                                  ? "text-amber-600"
                                  : vr.tone_fit === "offensive"
                                    ? "text-red-600"
                                    : "text-[var(--color-text-muted)]"
                            }
                          >
                            {vr.tone_fit}
                          </span>
                        </div>
                        <p className="text-[var(--color-text)]">&ldquo;{vr.reaction}&rdquo;</p>
                      </div>
                    ))}
                  </div>

                  <p className="text-xs text-[var(--color-text-muted)] mt-1 italic">
                    {r.preference_explanation}
                  </p>
                </div>
              ))}
          </div>
        </details>
      )}
    </div>
  );
}
