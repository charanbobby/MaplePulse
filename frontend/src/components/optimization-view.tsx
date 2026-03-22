"use client";

import { Sparkles, ArrowRight, Check } from "lucide-react";
import type { OptimizedMessage } from "@/lib/types";

interface OptimizationViewProps {
  originalMessage: string;
  optimized: OptimizedMessage;
  onContinue: () => void;
  canContinue?: boolean;
  continueLabel?: string;
}

export function OptimizationView({
  originalMessage,
  optimized,
  onContinue,
  canContinue = true,
  continueLabel = "Run Round 2",
}: OptimizationViewProps) {
  return (
    <div className="space-y-4 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold flex items-center gap-1.5">
            <Sparkles size={16} className="text-[var(--color-text-muted)]" />
            Optimized Message
          </h2>
          <p className="text-xs text-[var(--color-text-muted)]">
            Rewritten based on panel reactions
          </p>
        </div>
        <button
          onClick={onContinue}
          disabled={!canContinue}
          className={
            canContinue
              ? "flex items-center gap-2 px-4 py-1.5 bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
              : "flex items-center gap-2 px-4 py-1.5 bg-[var(--color-text-light)] text-white rounded-lg text-sm font-medium cursor-not-allowed opacity-50"
          }
        >
          {!canContinue && (
            <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
          )}
          {continueLabel}
          {canContinue && <ArrowRight size={14} />}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div className="bg-[var(--color-bg-card)] rounded-lg border border-[var(--color-border)] p-3">
          <p className="text-xs text-[var(--color-text-muted)] mb-1.5 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-400" /> Original
          </p>
          <p className="text-sm leading-relaxed text-[var(--color-text)]">
            {originalMessage}
          </p>
        </div>

        <div className="bg-[var(--color-bg-card)] rounded-lg border border-[var(--color-border)] p-3">
          <p className="text-xs text-[var(--color-text-muted)] mb-1.5 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500" /> Improved
          </p>
          <p className="text-sm leading-relaxed text-[var(--color-text)]">
            {optimized.improved_message}
          </p>
        </div>
      </div>

      <div className="bg-[var(--color-surface)] rounded-lg p-3">
        <p className="text-xs text-[var(--color-text-muted)] mb-1.5">Changes</p>
        <div className="space-y-1">
          {optimized.changes_made.map((change, i) => (
            <div key={i} className="flex items-start gap-1.5">
              <Check size={12} className="text-emerald-500 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-[var(--color-text)]">{change}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
