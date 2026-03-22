"use client";

import {
  CheckCircle2,
} from "lucide-react";
import type { WorkflowStep, UseCaseMode } from "@/lib/types";
import { cn } from "@/lib/cn";

const ALL_STEPS: { key: WorkflowStep; label: string }[] = [
  { key: "input", label: "Input" },
  { key: "panel_selection", label: "Panel" },
  { key: "round1_responding", label: "Round 1" },
  { key: "round1_review", label: "Review" },
  { key: "round1_summary", label: "Summary" },
  { key: "optimization", label: "Optimize" },
  { key: "round2_responding", label: "Round 2" },
  { key: "round2_summary", label: "Compare" },
  { key: "final_comparison", label: "Final" },
];

const MODE_STEPS: Record<UseCaseMode, WorkflowStep[]> = {
  focus_group: [
    "input", "panel_selection", "round1_responding", "round1_review",
    "round1_summary", "optimization", "round2_responding", "round2_summary", "final_comparison",
  ],
  ab_copy_test: [
    "input", "panel_selection", "round1_responding", "final_comparison",
  ],
  survey_pretest: [
    "input", "panel_selection", "round1_responding", "final_comparison",
  ],
};

const MODE_LABELS: Partial<Record<UseCaseMode, Partial<Record<WorkflowStep, { label: string }>>>> = {
  ab_copy_test: {
    round1_responding: { label: "Testing" },
    final_comparison: { label: "Results" },
  },
  survey_pretest: {
    round1_responding: { label: "Evaluating" },
    final_comparison: { label: "Results" },
  },
};

interface WorkflowStepperProps {
  currentStep: WorkflowStep;
  onStepClick?: (step: WorkflowStep) => void;
  ready?: { [key: string]: boolean };
  mode?: UseCaseMode;
}

export function WorkflowStepper({ currentStep, onStepClick, ready, mode = "focus_group" }: WorkflowStepperProps) {
  const visibleKeys = MODE_STEPS[mode];
  const steps = visibleKeys.map((key) => {
    const base = ALL_STEPS.find((s) => s.key === key)!;
    const override = MODE_LABELS[mode]?.[key];
    return override ? { key, label: override.label } : base;
  });

  const currentIdx = visibleKeys.indexOf(currentStep);

  // Map step keys to ready flags for clickability
  const STEP_READY_MAP: Record<string, string | null> = {
    input: null, // always accessible
    panel_selection: "panel",
    round1_responding: "round1_done",
    round1_review: "round1_done",
    round1_summary: "round1_summary",
    optimization: "optimization",
    round2_responding: "round2_done",
    round2_summary: "round2_summary",
    final_comparison: "final",
  };

  return (
    <div className="flex items-center justify-center gap-0.5 overflow-x-auto">
      {steps.map((step, i) => {
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
                "px-3 py-1.5 rounded-md text-xs font-medium transition-all",
                isActive && "bg-[var(--color-primary)] text-white",
                isDone && "text-[var(--color-text)]",
                !isActive && !isDone && hasData && "text-emerald-600",
                !isActive && !isDone && !hasData && "text-[var(--color-text-light)]",
                isClickable && "cursor-pointer hover:opacity-80",
                !isClickable && "cursor-default"
              )}
            >
              {isDone && <CheckCircle2 size={12} className="inline mr-1 -mt-0.5" />}
              <span className="whitespace-nowrap">{step.label}</span>
            </button>
            {i < steps.length - 1 && (
              <div
                className={cn(
                  "w-3 h-px mx-0.5",
                  isDone ? "bg-[var(--color-text)]" : "bg-[var(--color-border)]"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
