"use client";

import {
  MessageSquare,
  Users,
  Play,
  BarChart3,
  Sparkles,
  RotateCcw,
  Trophy,
  CheckCircle2,
} from "lucide-react";
import type { WorkflowStep } from "@/lib/types";
import { cn } from "@/lib/cn";

const STEPS: { key: WorkflowStep; label: string; icon: React.ElementType }[] = [
  { key: "input", label: "Input", icon: MessageSquare },
  { key: "panel_selection", label: "Panel", icon: Users },
  { key: "round1_responding", label: "Round 1", icon: Play },
  { key: "round1_summary", label: "Summary", icon: BarChart3 },
  { key: "optimization", label: "Optimize", icon: Sparkles },
  { key: "round2_responding", label: "Round 2", icon: RotateCcw },
  { key: "round2_summary", label: "Compare", icon: BarChart3 },
  { key: "final_comparison", label: "Final", icon: Trophy },
];

const STEP_ORDER = STEPS.map((s) => s.key);

interface WorkflowStepperProps {
  currentStep: WorkflowStep;
  onStepClick?: (step: WorkflowStep) => void;
  ready?: { [key: string]: boolean };
}

export function WorkflowStepper({ currentStep, onStepClick, ready }: WorkflowStepperProps) {
  const currentIdx = STEP_ORDER.indexOf(currentStep);

  // Map step keys to ready flags for clickability
  const STEP_READY_MAP: Record<string, string | null> = {
    input: null, // always accessible
    panel_selection: "panel",
    round1_responding: "round1_done",
    round1_summary: "round1_summary",
    optimization: "optimization",
    round2_responding: "round2_done",
    round2_summary: "round2_summary",
    final_comparison: "final",
  };

  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-2">
      {STEPS.map((step, i) => {
        const Icon = step.icon;
        const isActive = i === currentIdx;
        const isDone = i < currentIdx;
        const readyKey = STEP_READY_MAP[step.key];
        const hasData = readyKey === null || (ready && ready[readyKey]);
        const isClickable = !!onStepClick && (isActive || isDone || !!hasData);

        return (
          <div key={step.key} className="flex items-center">
            <button
              onClick={() => isClickable && onStepClick?.(step.key)}
              disabled={!isClickable}
              className={cn(
                "flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                isActive && "bg-[var(--color-primary)] text-white shadow-md",
                isDone && "bg-[var(--color-primary)]/10 text-[var(--color-primary)]",
                !isActive && !isDone && hasData && "bg-emerald-50 text-emerald-600",
                !isActive && !isDone && !hasData && "bg-[var(--color-surface)] text-[var(--color-text-muted)]",
                isClickable && "cursor-pointer hover:opacity-80",
                !isClickable && "cursor-default"
              )}
            >
              {isDone ? (
                <CheckCircle2 size={16} />
              ) : (
                <Icon size={16} />
              )}
              <span className="hidden sm:inline whitespace-nowrap">{step.label}</span>
            </button>
            {i < STEPS.length - 1 && (
              <div
                className={cn(
                  "w-4 h-0.5 mx-0.5",
                  isDone ? "bg-[var(--color-primary)]" : "bg-[var(--color-border)]"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
