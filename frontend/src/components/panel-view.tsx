"use client";

import {
  Loader2,
  X,
} from "lucide-react";
import type { Persona } from "@/lib/types";
import { cn } from "@/lib/cn";


const PROVINCE_COLORS: Record<string, string> = {};

function PersonaCard({
  persona,
  index,
  isAnimating,
  onRemove,
}: {
  persona: Persona;
  index: number;
  isAnimating: boolean;
  onRemove?: (uuid: string) => void;
}) {
  return (
    <div
      className={cn(
        "group relative bg-[var(--color-bg-card)] rounded-lg border border-[var(--color-border)] p-3 transition-all duration-300",
        isAnimating && "animate-[fadeIn_0.4s_ease-out]"
      )}
      style={{ animationDelay: `${index * 60}ms`, animationFillMode: "both" }}
    >
      {onRemove && (
        <button
          onClick={() => onRemove(persona.uuid)}
          className="absolute top-2 right-2 p-1 rounded-full opacity-0 group-hover:opacity-100 text-[var(--color-text-light)] hover:text-red-500 transition-all cursor-pointer"
          title="Remove"
        >
          <X size={12} />
        </button>
      )}
      <div className="flex items-center gap-2 mb-2 pr-6">
        <span className="text-sm font-semibold text-[var(--color-text)]">{persona.age}</span>
        <span className="text-sm text-[var(--color-text)]">{persona.sex}</span>
        <span className="text-xs text-[var(--color-text-muted)] ml-auto">{persona.province}</span>
      </div>

      <div className="space-y-0.5 text-xs text-[var(--color-text-muted)]">
        <p>{persona.occupation}</p>
        <p>{persona.planning_area} &middot; {persona.income_bracket}</p>
        <p>{persona.cultural_background}</p>
      </div>

      <div className="mt-2 flex flex-wrap gap-1">
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-surface)] text-[var(--color-text-muted)]">
          {persona.political_leaning}
        </span>
        {persona.indigenous_identity !== "Non-Indigenous" && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-surface)] text-[var(--color-text-muted)]">
            {persona.indigenous_identity}
          </span>
        )}
      </div>
    </div>
  );
}

interface PanelViewProps {
  panel: Persona[];
  onContinue?: () => void;
  onStop?: () => void;
  onRemovePersona?: (uuid: string) => void;
  /** When true, reactions are still loading — show waiting state on button */
  waitingForReactions?: boolean;
  /** When true, hide the header (used in the drawer) */
  hideHeader?: boolean;
}

export function PanelView({ panel, onContinue, onStop, onRemovePersona, waitingForReactions, hideHeader }: PanelViewProps) {
  return (
    <div className="space-y-4">
      {!hideHeader && (
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold">
              Panel &mdash; {panel.length} personas
            </h2>
            <p className="text-xs text-[var(--color-text-muted)]">
              {onRemovePersona
                ? "Hover to remove anyone who doesn't fit"
                : "Census-weighted synthetic personas"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {onStop && (
              <button
                onClick={onStop}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-[var(--color-text-muted)] hover:text-red-500 transition-colors cursor-pointer"
              >
                Cancel
              </button>
            )}
            {onContinue && (
              <button
                onClick={onContinue}
                disabled={waitingForReactions}
                className={cn(
                  "flex items-center gap-2 px-4 py-1.5 text-white rounded-lg text-sm font-medium transition-colors cursor-pointer",
                  waitingForReactions
                    ? "bg-[var(--color-text-muted)] cursor-wait"
                    : "bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)]"
                )}
              >
                {waitingForReactions && <Loader2 size={14} className="animate-spin" />}
                {waitingForReactions ? "Waiting..." : "Continue"}
              </button>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
        {panel.map((p, i) => (
          <PersonaCard key={p.uuid} persona={p} index={i} isAnimating onRemove={onRemovePersona} />
        ))}
      </div>
    </div>
  );
}
