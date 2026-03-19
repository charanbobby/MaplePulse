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
          <h2 className="text-xl font-semibold font-[family-name:var(--font-heading)] flex items-center gap-2">
            <Sparkles size={20} className="text-[var(--color-cta)]" />
            Optimized Message
          </h2>
          <p className="text-sm text-[var(--color-text-muted)]">
            AI-rewritten based on panel reactions and cultural flags
          </p>
        </div>
        <button
          onClick={onContinue}
          disabled={!canContinue}
          className={
            canContinue
              ? "flex items-center gap-2 px-4 py-2 bg-[var(--color-cta)] hover:bg-[var(--color-cta-hover)] text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
              : "flex items-center gap-2 px-4 py-2 bg-[var(--color-text-light)] text-white rounded-lg text-sm font-medium cursor-not-allowed opacity-60"
          }
        >
          {!canContinue && (
            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          )}
          {continueLabel}
          {canContinue && <ArrowRight size={16} />}
        </button>
      </div>

      {/* Before / After comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Original */}
        <div className="bg-[var(--color-bg-card)] rounded-xl border border-red-200 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-red-400" />
            <p className="text-xs font-medium uppercase tracking-wide text-red-600">
              Original Message
            </p>
          </div>
          <p className="text-sm leading-relaxed text-[var(--color-text)]">
            {originalMessage}
          </p>
        </div>

        {/* Improved */}
        <div className="bg-[var(--color-bg-card)] rounded-xl border border-emerald-200 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <p className="text-xs font-medium uppercase tracking-wide text-emerald-600">
              Improved Message
            </p>
          </div>
          <p className="text-sm leading-relaxed text-[var(--color-text)]">
            {optimized.improved_message}
          </p>
        </div>
      </div>

      {/* Changes made */}
      <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-4 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)] mb-3">
          Changes Made
        </p>
        <div className="space-y-2">
          {optimized.changes_made.map((change, i) => (
            <div key={i} className="flex items-start gap-2">
              <Check
                size={14}
                className="text-emerald-500 mt-0.5 flex-shrink-0"
              />
              <p className="text-sm text-[var(--color-text)]">{change}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
