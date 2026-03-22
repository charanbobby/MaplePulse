"use client";

import {
  ThumbsUp,
  ThumbsDown,
  Minus,
  AlertTriangle,
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
  const { persona, reaction: text, sentiment_score, relevance, tone_fit, cultural_flags } = reaction;

  return (
    <div
      className={cn(
        "bg-[var(--color-bg-card)] rounded-lg border transition-all duration-300",
        isActive
          ? "border-[var(--color-primary)]"
          : "border-[var(--color-border)]",
        isResponding && "animate-pulse"
      )}
      style={{
        animationDelay: `${index * 80}ms`,
        animationFillMode: "both",
      }}
    >
      {/* Header */}
      <div className="px-3 py-2 border-b border-[var(--color-border)] flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">
            {persona.age} {persona.sex} &middot; {persona.occupation}
          </p>
          <p className="text-[11px] text-[var(--color-text-muted)]">
            {persona.planning_area}, {persona.province}
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <SentimentBadge score={sentiment_score} />
          {relevance === "directly_relevant" ? (
            <ThumbsUp size={12} className="text-emerald-600" />
          ) : relevance === "somewhat" ? (
            <Minus size={12} className="text-amber-500" />
          ) : (
            <ThumbsDown size={12} className="text-red-400" />
          )}
        </div>
      </div>

      {/* Round 1 reaction (shown in Round 2 for comparison) */}
      {round1Reaction && !isResponding && (
        <div className="px-3 pt-2 pb-1">
          <div className="flex items-center gap-1.5 mb-0.5">
            <p className="text-[10px] text-[var(--color-text-light)]">Round 1</p>
            <SentimentBadge score={round1Reaction.sentiment_score} />
          </div>
          <p className="text-xs italic text-[var(--color-text-muted)]">
            &ldquo;{round1Reaction.reaction}&rdquo;
          </p>
          <div className="mt-1.5 border-t border-dashed border-[var(--color-border)]" />
        </div>
      )}

      {/* Reaction body */}
      <div className="px-3 py-2">
        {round1Reaction && !isResponding && (
          <p className="text-[10px] text-[var(--color-text-light)] mb-0.5">Round 2</p>
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
      {!isResponding && (cultural_flags.length > 0 || tone_fit) && (
        <div className="px-3 py-1.5 border-t border-[var(--color-border)] flex items-center gap-1.5 flex-wrap">
          <ToneBadge tone={tone_fit} />
          {cultural_flags.map((flag) => (
            <span
              key={flag}
              className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-surface)] text-[var(--color-text-muted)] flex items-center gap-0.5"
            >
              <AlertTriangle size={9} />
              {flag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
