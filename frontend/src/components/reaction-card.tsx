"use client";

import {
  ThumbsUp,
  ThumbsDown,
  Minus,
  AlertTriangle,
  Cpu,
  MapPin,
  Briefcase,
} from "lucide-react";
import type { Reaction } from "@/lib/types";
import { cn } from "@/lib/cn";

function SentimentBadge({ score }: { score: number }) {
  const color =
    score >= 4
      ? "bg-emerald-100 text-emerald-700"
      : score >= 3
      ? "bg-amber-100 text-amber-700"
      : "bg-red-100 text-red-700";
  return (
    <span className={cn("text-xs px-2 py-0.5 rounded-full font-mono font-medium", color)}>
      {score}/5
    </span>
  );
}

function ToneBadge({ tone }: { tone: string }) {
  const styles: Record<string, string> = {
    natural: "bg-emerald-100 text-emerald-700",
    acceptable: "bg-blue-100 text-blue-700",
    awkward: "bg-amber-100 text-amber-700",
    offensive: "bg-red-100 text-red-700",
  };
  return (
    <span className={cn("text-[10px] px-1.5 py-0.5 rounded font-medium", styles[tone] || "bg-gray-100 text-gray-700")}>
      {tone}
    </span>
  );
}

interface ReactionCardProps {
  reaction: Reaction;
  index: number;
  isActive: boolean;
  isResponding: boolean;
  /** The same persona's Round 1 reaction, shown for context in Round 2 */
  round1Reaction?: Reaction;
}

export function ReactionCard({
  reaction,
  index,
  isActive,
  isResponding,
  round1Reaction,
}: ReactionCardProps) {
  const { persona, reaction: text, sentiment_score, relevance, tone_fit, cultural_flags, model_used } = reaction;

  return (
    <div
      className={cn(
        "bg-[var(--color-bg-card)] rounded-xl border shadow-sm transition-all duration-300",
        isActive
          ? "border-[var(--color-primary)] ring-2 ring-[var(--color-primary)]/20"
          : "border-[var(--color-border)]",
        isResponding && "animate-pulse"
      )}
      style={{
        animationDelay: `${index * 100}ms`,
        animationFillMode: "both",
      }}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-[var(--color-primary)]/10 flex items-center justify-center text-xs font-bold text-[var(--color-primary)]">
            {persona.age}
          </div>
          <div>
            <p className="text-sm font-medium">
              {persona.sex}, {persona.occupation}
            </p>
            <div className="flex items-center gap-2 text-[10px] text-[var(--color-text-muted)]">
              <span className="flex items-center gap-0.5">
                <MapPin size={10} />
                {persona.planning_area}, {persona.province}
              </span>
              <span className="flex items-center gap-0.5">
                <Briefcase size={10} />
                {persona.income_bracket}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <SentimentBadge score={sentiment_score} />
          {relevance === "directly_relevant" ? (
            <ThumbsUp size={14} className="text-emerald-600" />
          ) : relevance === "somewhat" ? (
            <Minus size={14} className="text-amber-500" />
          ) : (
            <ThumbsDown size={14} className="text-red-400" />
          )}
        </div>
      </div>

      {/* Round 1 reaction (shown in Round 2 for comparison) */}
      {round1Reaction && !isResponding && (
        <div className="px-4 pt-3 pb-1">
          <p className="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1">
            Round 1 — Original Message
          </p>
          <p className="text-xs leading-relaxed italic text-[var(--color-text-muted)]">
            &ldquo;{round1Reaction.reaction}&rdquo;
          </p>
          <div className="flex items-center gap-1.5 mt-1">
            <SentimentBadge score={round1Reaction.sentiment_score} />
            {round1Reaction.relevance === "directly_relevant" ? (
              <ThumbsUp size={11} className="text-emerald-600" />
            ) : round1Reaction.relevance === "somewhat" ? (
              <Minus size={11} className="text-amber-500" />
            ) : (
              <ThumbsDown size={11} className="text-red-400" />
            )}
          </div>
          <div className="mt-2 border-t border-dashed border-[var(--color-border)]" />
        </div>
      )}

      {/* Reaction body */}
      <div className="px-4 py-3">
        {round1Reaction && !isResponding && (
          <p className="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1">
            Round 2 — Optimized Message
          </p>
        )}
        {isResponding ? (
          <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)] animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)] animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)] animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
            Thinking...
          </div>
        ) : (
          <p className="text-sm leading-relaxed italic text-[var(--color-text)]">
            &ldquo;{text}&rdquo;
          </p>
        )}
      </div>

      {/* Footer */}
      {!isResponding && (
        <div className="px-4 py-2 border-t border-[var(--color-border)] flex items-center justify-between">
          <div className="flex items-center gap-1.5 flex-wrap">
            <ToneBadge tone={tone_fit} />
            {cultural_flags.map((flag) => (
              <span
                key={flag}
                className="text-[10px] px-1.5 py-0.5 rounded bg-orange-50 text-orange-700 flex items-center gap-0.5"
              >
                <AlertTriangle size={9} />
                {flag}
              </span>
            ))}
          </div>
          {model_used && (
            <span className="text-[10px] text-[var(--color-text-light)] flex items-center gap-0.5">
              <Cpu size={9} />
              {model_used}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
