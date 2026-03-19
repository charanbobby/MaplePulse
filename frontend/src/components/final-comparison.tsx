"use client";

import {
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Trophy,
  AlertTriangle,
  RotateCcw,
  MessageSquare,
} from "lucide-react";
import type { AggregatedResults, OptimizedMessage } from "@/lib/types";
import { cn } from "@/lib/cn";

function DeltaCard({
  label,
  before,
  after,
  unit,
  higherIsBetter,
}: {
  label: string;
  before: number;
  after: number;
  unit: string;
  higherIsBetter: boolean;
}) {
  const delta = after - before;
  const improved = higherIsBetter ? delta > 0 : delta < 0;
  const deltaStr = delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1);

  return (
    <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-4 shadow-sm">
      <p className="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wide mb-2">
        {label}
      </p>
      <div className="flex items-end gap-3">
        <div>
          <p className="text-xs text-[var(--color-text-light)]">Before</p>
          <p className="text-lg font-mono font-semibold text-[var(--color-text-muted)]">
            {before.toFixed(1)}
            {unit}
          </p>
        </div>
        <ArrowRight size={16} className="text-[var(--color-text-light)] mb-2" />
        <div>
          <p className="text-xs text-[var(--color-text-light)]">After</p>
          <p
            className={cn(
              "text-lg font-mono font-semibold",
              improved ? "text-emerald-600" : "text-red-500"
            )}
          >
            {after.toFixed(1)}
            {unit}
          </p>
        </div>
        <div
          className={cn(
            "flex items-center gap-0.5 text-sm font-mono font-medium ml-auto mb-1",
            improved ? "text-emerald-600" : "text-red-500"
          )}
        >
          {improved ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {deltaStr}
          {unit}
        </div>
      </div>
    </div>
  );
}

interface FinalComparisonProps {
  originalMessage: string;
  optimized: OptimizedMessage;
  round1: AggregatedResults;
  round2: AggregatedResults;
  onRestart: () => void;
}

export function FinalComparison({
  originalMessage,
  optimized,
  round1,
  round2,
  onRestart,
}: FinalComparisonProps) {
  const sentimentDelta = round2.avg_sentiment - round1.avg_sentiment;
  const resonanceDelta = round2.resonance_pct - round1.resonance_pct;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
            <Trophy size={20} className="text-amber-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold font-[family-name:var(--font-heading)]">
              Final Results
            </h2>
            <p className="text-sm text-[var(--color-text-muted)]">
              Before vs. After optimization — same panel, same personas
            </p>
          </div>
        </div>
        <button
          onClick={onRestart}
          className="flex items-center gap-2 px-4 py-2 border border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-surface)] rounded-lg text-sm font-medium transition-colors cursor-pointer"
        >
          <RotateCcw size={16} />
          New Test
        </button>
      </div>

      {/* Delta cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <DeltaCard
          label="Avg Sentiment"
          before={round1.avg_sentiment}
          after={round2.avg_sentiment}
          unit=""
          higherIsBetter
        />
        <DeltaCard
          label="Resonance"
          before={round1.resonance_pct}
          after={round2.resonance_pct}
          unit="%"
          higherIsBetter
        />
        <DeltaCard
          label="Perfect Tone"
          before={round1.tone_distribution.perfect || 0}
          after={round2.tone_distribution.perfect || 0}
          unit="%"
          higherIsBetter
        />
        <DeltaCard
          label="Off Tone"
          before={round1.tone_distribution.off || 0}
          after={round2.tone_distribution.off || 0}
          unit="%"
          higherIsBetter={false}
        />
      </div>

      {/* Messages side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-[var(--color-bg-card)] rounded-xl border border-red-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare size={16} className="text-red-500" />
            <p className="text-sm font-semibold text-red-600">
              Original Message
            </p>
          </div>
          <p className="text-sm leading-relaxed">{originalMessage}</p>
          <div className="mt-4 pt-3 border-t border-red-100 flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
            <span>
              Sentiment:{" "}
              <strong className="text-red-500">{round1.avg_sentiment.toFixed(1)}</strong>
            </span>
            <span>
              Resonance:{" "}
              <strong className="text-red-500">{round1.resonance_pct}%</strong>
            </span>
          </div>
        </div>

        <div className="bg-[var(--color-bg-card)] rounded-xl border border-emerald-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare size={16} className="text-emerald-500" />
            <p className="text-sm font-semibold text-emerald-600">
              Optimized Message
            </p>
          </div>
          <p className="text-sm leading-relaxed">
            {optimized.improved_message}
          </p>
          <div className="mt-4 pt-3 border-t border-emerald-100 flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
            <span>
              Sentiment:{" "}
              <strong className="text-emerald-600">
                {round2.avg_sentiment.toFixed(1)}
              </strong>
            </span>
            <span>
              Resonance:{" "}
              <strong className="text-emerald-600">
                {round2.resonance_pct}%
              </strong>
            </span>
          </div>
        </div>
      </div>

      {/* Improvement summary */}
      <div
        className={cn(
          "rounded-xl border p-5",
          sentimentDelta > 0
            ? "bg-emerald-50 border-emerald-200"
            : sentimentDelta < 0
            ? "bg-red-50 border-red-200"
            : "bg-gray-50 border-gray-200"
        )}
      >
        <div className="flex items-center gap-2 mb-2">
          {sentimentDelta > 0 ? (
            <TrendingUp size={18} className="text-emerald-600" />
          ) : sentimentDelta < 0 ? (
            <TrendingDown size={18} className="text-red-500" />
          ) : (
            <AlertTriangle size={18} className="text-amber-500" />
          )}
          <p className="font-semibold text-sm">
            {sentimentDelta > 0
              ? `Sentiment improved by ${sentimentDelta.toFixed(1)} points (${((sentimentDelta / round1.avg_sentiment) * 100).toFixed(0)}% increase)`
              : sentimentDelta < 0
              ? `Sentiment decreased by ${Math.abs(sentimentDelta).toFixed(1)} points`
              : "Sentiment unchanged between rounds"}
          </p>
        </div>
        <p className="text-sm text-[var(--color-text-muted)]">
          {resonanceDelta !== 0
            ? `Resonance ${resonanceDelta > 0 ? "improved" : "dropped"} from ${round1.resonance_pct}% to ${round2.resonance_pct}% (${resonanceDelta > 0 ? "+" : ""}${resonanceDelta}pp).`
            : `Resonance held steady at ${round1.resonance_pct}%.`}
          {" "}
          {(() => {
            const flagsBefore = round1.top_cultural_flags.length;
            const flagsAfter = round2.top_cultural_flags.length;
            if (flagsAfter < flagsBefore) return `Cultural flags reduced from ${flagsBefore} to ${flagsAfter}.`;
            if (flagsAfter > flagsBefore) return `Cultural flags increased from ${flagsBefore} to ${flagsAfter}.`;
            return flagsBefore === 0 ? "No cultural flags in either round." : `Cultural flags unchanged (${flagsBefore}).`;
          })()}
        </p>
      </div>

      {/* Changes made */}
      <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-5 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)] mb-3">
          Key Optimizations Applied
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {optimized.changes_made.map((change, i) => (
            <div key={i} className="flex items-start gap-2 text-sm">
              <span className="text-emerald-500 font-bold">+</span>
              <span>{change}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
