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
  /** The original message being reacted to */
  message?: string;
  /** Round 1 reactions — passed when round=2 to show previous reaction per persona */
  round1Reactions?: Reaction[];
  /** Custom label for the continue button */
  continueLabel?: string;
}

export function ReactionsView({
  reactions,
  respondingIndex,
  round,
  onAllDone,
  isReady,
  message,
  round1Reactions,
  continueLabel,
}: ReactionsViewProps) {
  const allDone = isReady || respondingIndex >= reactions.length;

  return (
    <div className="space-y-4">
      {message && (
        <div className="bg-[var(--color-surface)] rounded-lg px-4 py-3">
          <p className="text-xs text-[var(--color-text-muted)] mb-0.5">
            {round === 2 ? "Optimized" : "Original"}
          </p>
          <p className="text-sm text-[var(--color-text)] whitespace-pre-wrap">{message}</p>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold">
            Round {round} Reactions
          </h2>
          <p className="text-xs text-[var(--color-text-muted)]">
            {isReady
              ? `${reactions.length} responses`
              : `${respondingIndex} of ${reactions.length || "?"} responding...`}
          </p>
        </div>
        <button
          onClick={onAllDone}
          disabled={!isReady}
          className={
            isReady
              ? "px-4 py-1.5 bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
              : "px-4 py-1.5 bg-[var(--color-text-light)] text-white rounded-lg text-sm font-medium cursor-not-allowed opacity-50"
          }
        >
          {isReady ? (continueLabel || "View Summary") : "Waiting..."}
        </button>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1 bg-[var(--color-surface)] rounded-full overflow-hidden">
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
            round1Reaction={
              round1Reactions?.find((r1) => r1.persona.uuid === r.persona.uuid)
            }
          />
        ))}
      </div>
    </div>
  );
}
