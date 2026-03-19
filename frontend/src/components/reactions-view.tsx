"use client";

import { ReactionCard } from "./reaction-card";
import type { Reaction } from "@/lib/types";

interface ReactionsViewProps {
  reactions: Reaction[];
  respondingIndex: number;
  round: 1 | 2;
  onAllDone: () => void;
  /** When true, the summary data is ready and the "View Summary" button is enabled */
  isReady?: boolean;
}

export function ReactionsView({
  reactions,
  respondingIndex,
  round,
  onAllDone,
  isReady,
}: ReactionsViewProps) {
  const allDone = isReady || respondingIndex >= reactions.length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold font-[family-name:var(--font-heading)]">
            Round {round} — Persona Reactions
          </h2>
          <p className="text-sm text-[var(--color-text-muted)]">
            {isReady
              ? `All ${reactions.length} responses received`
              : `${respondingIndex} of ${reactions.length || "?"} responding...`}
          </p>
        </div>
        <button
          onClick={onAllDone}
          disabled={!isReady}
          className={
            isReady
              ? "px-4 py-2 bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
              : "px-4 py-2 bg-[var(--color-text-light)] text-white rounded-lg text-sm font-medium cursor-not-allowed opacity-60"
          }
        >
          {isReady ? "View Summary" : "Waiting for all responses..."}
        </button>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1.5 bg-[var(--color-surface)] rounded-full overflow-hidden">
        <div
          className="h-full bg-[var(--color-primary)] transition-all duration-500 rounded-full"
          style={{
            width: reactions.length > 0 ? `${(respondingIndex / reactions.length) * 100}%` : "0%",
          }}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {reactions.map((r, i) => (
          <ReactionCard
            key={r.persona.uuid + "-" + i}
            reaction={r}
            index={i}
            isActive={i === respondingIndex - 1}
            isResponding={false}
          />
        ))}
      </div>
    </div>
  );
}
