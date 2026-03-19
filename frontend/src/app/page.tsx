"use client";

import { useState, useCallback, useRef } from "react";
import Image from "next/image";
import { AlertCircle, Users, X } from "lucide-react";
import type {
  WorkflowStep,
  PanelFilters,
  Persona,
  Reaction,
  AggregatedResults,
  OptimizedMessage,
} from "@/lib/types";
import { runFocusGroup } from "@/lib/api";
import { WorkflowStepper } from "@/components/workflow-stepper";
import { InputStep } from "@/components/input-step";
import { PanelView } from "@/components/panel-view";
import { ReactionsView } from "@/components/reactions-view";
import { SummaryView } from "@/components/summary-view";
import { OptimizationView } from "@/components/optimization-view";
import { FinalComparison } from "@/components/final-comparison";

/**
 * Tracks which steps have their data ready (arrived from SSE).
 * The user's current `step` is separate — they advance manually.
 */
interface DataReadyFlags {
  panel: boolean;
  round1_done: boolean;   // all R1 reactions received
  round1_summary: boolean;
  optimization: boolean;
  round2_done: boolean;   // all R2 reactions received
  round2_summary: boolean;
  final: boolean;
}

const INITIAL_FLAGS: DataReadyFlags = {
  panel: false,
  round1_done: false,
  round1_summary: false,
  optimization: false,
  round2_done: false,
  round2_summary: false,
  final: false,
};

export default function Home() {
  // User-controlled view
  const [step, setStep] = useState<WorkflowStep>("input");

  // Data state
  const [message, setMessage] = useState("");
  const [panel, setPanel] = useState<Persona[]>([]);
  const [round1Reactions, setRound1Reactions] = useState<Reaction[]>([]);
  const [round2Reactions, setRound2Reactions] = useState<Reaction[]>([]);
  const [respondingIndex, setRespondingIndex] = useState(0);
  const [r1Aggregate, setR1Aggregate] = useState<AggregatedResults | null>(null);
  const [r2Aggregate, setR2Aggregate] = useState<AggregatedResults | null>(null);
  const [optimized, setOptimized] = useState<OptimizedMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [traceId, setTraceId] = useState<string | null>(null);

  // Data-ready flags (SSE sets these, user navigates independently)
  const [ready, setReady] = useState<DataReadyFlags>(INITIAL_FLAGS);
  const readyRef = useRef<DataReadyFlags>(INITIAL_FLAGS);
  const markReady = (key: keyof DataReadyFlags) => {
    readyRef.current = { ...readyRef.current, [key]: true };
    setReady({ ...readyRef.current });
  };

  // Panel drawer
  const [showPanelDrawer, setShowPanelDrawer] = useState(false);

  // Is the pipeline currently running?
  const [isRunning, setIsRunning] = useState(false);

  // Refs for SSE callbacks
  const r1ReactionsRef = useRef<Reaction[]>([]);
  const r2ReactionsRef = useRef<Reaction[]>([]);
  const panelRef = useRef<Persona[]>([]);
  const stepRef = useRef<WorkflowStep>("input");

  // Keep stepRef in sync
  const setStepTracked = (s: WorkflowStep) => {
    stepRef.current = s;
    setStep(s);
  };

  const handleSubmit = useCallback(
    async (msg: string, filters: PanelFilters) => {
      // Reset all state
      setMessage(msg);
      setPanel([]);
      setRound1Reactions([]);
      setRound2Reactions([]);
      setRespondingIndex(0);
      setR1Aggregate(null);
      setR2Aggregate(null);
      setOptimized(null);
      setError(null);
      setTraceId(null);
      readyRef.current = { ...INITIAL_FLAGS };
      setReady({ ...INITIAL_FLAGS });
      r1ReactionsRef.current = [];
      r2ReactionsRef.current = [];
      panelRef.current = [];

      setIsRunning(true);
      setStepTracked("panel_selection");

      await runFocusGroup(
        msg,
        filters,
        {
          onStep: (_data) => {
            // We no longer auto-advance. The user controls navigation.
          },

          onClassify: (_data) => {},

          onPanel: (data) => {
            const personas = data.panel as Persona[];
            panelRef.current = personas;
            setPanel(personas);
            markReady("panel");
            // Auto-show panel (first step after submit, user expects this)
            setStepTracked("panel_selection");
          },

          onReactionR1: (data) => {
            if (data.error) return;
            const persona = panelRef.current.find(
              (p) => p.uuid === data.persona_id
            ) || _buildFallbackPersona(data);

            const reaction: Reaction = {
              persona,
              reaction: data.reaction,
              sentiment_score: data.sentiment_score,
              resonates: data.resonates,
              tone_fit: data.tone_fit,
              cultural_flags: data.cultural_flags || [],
              model_used: data.model_used,
            };

            r1ReactionsRef.current = [...r1ReactionsRef.current, reaction];
            setRound1Reactions([...r1ReactionsRef.current]);
            setRespondingIndex(r1ReactionsRef.current.length);
            // Don't auto-advance — user clicks "View Round 1" from panel
          },

          onSummaryR1: (data) => {
            setR1Aggregate({
              avg_sentiment: data.avg_sentiment,
              resonance_pct: data.resonance_pct,
              tone_distribution: data.tone_distribution,
              top_cultural_flags: data.top_cultural_flags,
            });
            markReady("round1_done");
            markReady("round1_summary");
            // Don't auto-advance — user clicks "View Summary"
          },

          onOptimized: (data) => {
            setOptimized({
              improved_message: data.improved_message,
              changes_made: data.changes_made,
            });
            markReady("optimization");
            // Don't auto-advance — user clicks "Next"
          },

          onReactionR2: (data) => {
            if (data.error) return;
            const persona = panelRef.current.find(
              (p) => p.uuid === data.persona_id
            ) || _buildFallbackPersona(data);

            const reaction: Reaction = {
              persona,
              reaction: data.reaction,
              sentiment_score: data.sentiment_score,
              resonates: data.resonates,
              tone_fit: data.tone_fit,
              cultural_flags: data.cultural_flags || [],
              model_used: data.model_used,
            };

            r2ReactionsRef.current = [...r2ReactionsRef.current, reaction];
            setRound2Reactions([...r2ReactionsRef.current]);
            setRespondingIndex(r2ReactionsRef.current.length);

            // Auto-advance to round2 ONLY if user clicked through to it
            if (stepRef.current === "round2_responding") {
              // Already there, just update
            }
          },

          onSummaryR2: (data) => {
            setR2Aggregate({
              avg_sentiment: data.avg_sentiment,
              resonance_pct: data.resonance_pct,
              tone_distribution: data.tone_distribution,
              top_cultural_flags: data.top_cultural_flags,
            });
            markReady("round2_done");
            markReady("round2_summary");
          },

          onDone: (data) => {
            setTraceId(data.trace_id);
            markReady("final");
            setIsRunning(false);
          },

          onError: (err) => {
            setError(err);
            setIsRunning(false);
          },
        }
      );
    },
    []
  );

  // Clickable stepper — can jump to any step that has data
  const handleStepClick = (targetStep: WorkflowStep) => {
    const canNavigate: Record<WorkflowStep, boolean> = {
      input: true,
      panel_selection: ready.panel,
      round1_responding: r1ReactionsRef.current.length > 0,
      round1_summary: ready.round1_summary,
      optimization: ready.optimization,
      round2_responding: r2ReactionsRef.current.length > 0,
      round2_summary: ready.round2_summary,
      final_comparison: ready.final,
    };
    if (canNavigate[targetStep]) {
      setStepTracked(targetStep);
    }
  };

  const handleRestart = () => {
    setStepTracked("input");
    setMessage("");
    setPanel([]);
    setRound1Reactions([]);
    setRound2Reactions([]);
    setRespondingIndex(0);
    setR1Aggregate(null);
    setR2Aggregate(null);
    setOptimized(null);
    setError(null);
    setTraceId(null);
    setIsRunning(false);
    readyRef.current = { ...INITIAL_FLAGS };
    setReady({ ...INITIAL_FLAGS });
    r1ReactionsRef.current = [];
    r2ReactionsRef.current = [];
    panelRef.current = [];
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-[var(--color-border)] bg-[var(--color-bg-card)]">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Image
              src="/logo-mark.png"
              alt="MaplePulse"
              width={390}
              height={630}
              className="h-10 w-auto object-contain"
              priority
            />
            <div>
              <h1 className="text-lg font-bold font-[family-name:var(--font-heading)] leading-tight">
                <span className="text-[#1a3a6b]">Maple</span><span className="text-[#1ab5b0]">Pulse</span>
              </h1>
              <p className="text-[10px] text-[var(--color-text-muted)] leading-tight">
                Synthetic Focus Group for Canada
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Panel drawer toggle */}
            {panel.length > 0 && step !== "panel_selection" && (
              <button
                onClick={() => setShowPanelDrawer(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] transition-colors cursor-pointer"
              >
                <Users size={14} />
                View Panel ({panel.length})
              </button>
            )}
            {traceId && (
              <a
                href={`${process.env.NEXT_PUBLIC_LANGFUSE_HOST || "https://us.cloud.langfuse.com"}/project/${process.env.NEXT_PUBLIC_LANGFUSE_PROJECT_ID || ""}/traces/${traceId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-[var(--color-primary)] hover:underline font-mono"
              >
                Trace: {traceId}
              </a>
            )}
            {isRunning && (
              <div className="flex items-center gap-1.5 text-xs text-[var(--color-cta)]">
                <div className="w-2 h-2 rounded-full bg-[var(--color-cta)] animate-pulse" />
                Pipeline running
              </div>
            )}
            <div className="text-xs text-[var(--color-text-light)] font-mono">
              5,000 personas
            </div>
          </div>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 py-2">
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 flex items-start gap-2">
            <AlertCircle size={16} className="text-red-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-red-800">Connection Error</p>
              <p className="text-xs text-red-600">{error}</p>
              <button
                onClick={handleRestart}
                className="text-xs text-red-700 underline mt-1 cursor-pointer"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stepper — clickable */}
      <div className="max-w-7xl mx-auto px-4 py-3">
        <WorkflowStepper currentStep={step} onStepClick={handleStepClick} ready={{ ...ready }} />
      </div>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-4 pb-16">
        {step === "input" && <InputStep onSubmit={handleSubmit} />}

        {step === "panel_selection" && panel.length > 0 && (
          <PanelView
            panel={panel}
            onContinue={() => setStepTracked("round1_responding")}
          />
        )}

        {step === "panel_selection" && panel.length === 0 && (
          <div className="flex items-center justify-center py-16">
            <div className="flex items-center gap-3 text-[var(--color-text-muted)]">
              <div className="w-5 h-5 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
              <span className="text-sm">Classifying intent & selecting panel...</span>
            </div>
          </div>
        )}

        {step === "round1_responding" && (
          <ReactionsView
            reactions={round1Reactions}
            respondingIndex={respondingIndex}
            round={1}
            onAllDone={() => setStepTracked("round1_summary")}
            isReady={ready.round1_summary}
          />
        )}

        {step === "round1_summary" && r1Aggregate && (
          <SummaryView
            aggregate={r1Aggregate}
            reactions={round1Reactions}
            round={1}
            onContinue={() => setStepTracked("optimization")}
            continueLabel={ready.optimization ? "View Optimization" : "Optimizing..."}
            canContinue={ready.optimization}
          />
        )}

        {step === "optimization" && optimized && (
          <OptimizationView
            originalMessage={message}
            optimized={optimized}
            onContinue={() => {
              setRespondingIndex(0);
              setStepTracked("round2_responding");
            }}
            canContinue={r2ReactionsRef.current.length > 0 || ready.round2_done}
            continueLabel={ready.round2_done || r2ReactionsRef.current.length > 0 ? "View Round 2" : "Running Round 2..."}
          />
        )}

        {step === "round2_responding" && (
          <ReactionsView
            reactions={round2Reactions}
            respondingIndex={respondingIndex}
            round={2}
            onAllDone={() => setStepTracked("round2_summary")}
            isReady={ready.round2_summary}
          />
        )}

        {step === "round2_summary" && r2Aggregate && (
          <SummaryView
            aggregate={r2Aggregate}
            reactions={round2Reactions}
            round={2}
            onContinue={() => setStepTracked("final_comparison")}
            continueLabel={ready.final ? "Final Comparison" : "Finalizing..."}
            canContinue={ready.final}
          />
        )}

        {step === "final_comparison" && r1Aggregate && r2Aggregate && optimized && (
          <FinalComparison
            originalMessage={message}
            optimized={optimized}
            round1={r1Aggregate}
            round2={r2Aggregate}
            onRestart={handleRestart}
          />
        )}
      </main>

      {/* Panel Drawer (slide-over) */}
      {showPanelDrawer && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setShowPanelDrawer(false)}
          />
          <div className="relative w-full max-w-2xl bg-[var(--color-bg)] overflow-y-auto shadow-2xl animate-[slideIn_0.2s_ease-out]">
            <div className="sticky top-0 bg-[var(--color-bg-card)] border-b border-[var(--color-border)] px-4 py-3 flex items-center justify-between z-10">
              <div className="flex items-center gap-2">
                <Users size={16} className="text-[var(--color-primary)]" />
                <h3 className="text-sm font-semibold">Panel — {panel.length} Personas</h3>
              </div>
              <button
                onClick={() => setShowPanelDrawer(false)}
                className="p-1 rounded hover:bg-[var(--color-surface)] transition-colors cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>
            <div className="p-4">
              <PanelView
                panel={panel}
                onContinue={() => setShowPanelDrawer(false)}
                hideHeader
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/** Build a fallback Persona from SSE reaction data when panel lookup fails. */
function _buildFallbackPersona(data: Record<string, unknown>): Persona {
  return {
    uuid: data.persona_id as string,
    age: data.age as number,
    sex: (data.sex as string) || "Unknown",
    occupation: data.occupation as string,
    province: data.province as string,
    planning_area: data.city as string,
    income_bracket: (data.income_bracket as string) || "Unknown",
    cultural_background: (data.cultural_background as string) || "",
    languages_spoken: (data.languages as string) || "",
    education_level: "",
    marital_status: "",
    immigration_status: "",
    indigenous_identity: "Non-Indigenous",
    visible_minority: "Not a visible minority",
    housing: "",
    political_leaning: "",
    religion: "",
    top_concerns: [],
    commute_mode: "",
    estimated_annual_income: 0,
  };
}
