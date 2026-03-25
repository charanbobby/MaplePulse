"use client";

import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { logEval } from "@/lib/api";
import { cn } from "@/lib/cn";

interface EvalVoteProps {
  evalType: string;
  label: string;
  traceId?: string;
  personaId?: string;
  meta?: Record<string, unknown>;
  /** compact mode for inline use in cards */
  compact?: boolean;
}

export function EvalVote({ evalType, label, traceId, personaId, meta, compact }: EvalVoteProps) {
  const [vote, setVote] = useState<"thumbs_up" | "thumbs_down" | null>(null);

  const handleVote = (v: "thumbs_up" | "thumbs_down") => {
    if (vote) return; // already voted
    setVote(v);
    logEval(evalType, { traceId, personaId, vote: v, meta });
  };

  if (vote) {
    return (
      <span className={cn(
        "inline-flex items-center gap-1 text-[10px]",
        vote === "thumbs_up" ? "text-emerald-600" : "text-red-500"
      )}>
        {vote === "thumbs_up" ? <ThumbsUp size={10} /> : <ThumbsDown size={10} />}
        {!compact && label}
      </span>
    );
  }

  return (
    <span className={cn(
      "inline-flex items-center gap-1",
      compact ? "text-[10px]" : "text-xs"
    )}>
      {!compact && <span className="text-[var(--color-text-muted)]">{label}</span>}
      {compact && <span className="text-[var(--color-text-light)]">{label}</span>}
      <button
        onClick={() => handleVote("thumbs_up")}
        className="p-0.5 rounded text-[var(--color-text-light)] hover:text-emerald-600 hover:bg-emerald-50 transition-colors cursor-pointer"
        title={`${label}: Yes`}
      >
        <ThumbsUp size={compact ? 10 : 12} />
      </button>
      <button
        onClick={() => handleVote("thumbs_down")}
        className="p-0.5 rounded text-[var(--color-text-light)] hover:text-red-500 hover:bg-red-50 transition-colors cursor-pointer"
        title={`${label}: No`}
      >
        <ThumbsDown size={compact ? 10 : 12} />
      </button>
    </span>
  );
}
