"use client";

import { useState, useCallback, useRef } from "react";
import Image from "next/image";
import { AlertCircle, Users } from "lucide-react";
import type {
  WorkflowStep,
  PanelFilters,
  Persona,
  Reaction,
  AggregatedResults,
  OptimizedMessage,
  UseCaseMode,
  ABReaction,
  ABSummary,
  SurveyReaction,
  SurveySummary,
} from "@/lib/types";
import { runBuildPanel, selectPanel, runWithPanel, continueAfterReview, runABTest, runSurveyPreTest } from "@/lib/api";
import { WorkflowStepper } from "@/components/workflow-stepper";
import { InputStep } from "@/components/input-step";
import { PanelView } from "@/components/panel-view";
import { ReactionsView } from "@/components/reactions-view";
import { SummaryView } from "@/components/summary-view";
import { OptimizationView } from "@/components/optimization-view";
import { FinalComparison } from "@/components/final-comparison";
import { ABTestInput } from "@/components/ab-test-input";
import { SurveyPreTestInput } from "@/components/survey-pretest-input";
import { ABResultsView } from "@/components/ab-results-view";
import { SurveyResultsView } from "@/components/survey-results-view";
import { LandingPage } from "@/components/landing-page";

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

const MODE_OPTIONS: { mode: UseCaseMode; label: string }[] = [
  { mode: "focus_group", label: "Focus Group" },
  { mode: "ab_copy_test", label: "A/B Test" },
  { mode: "survey_pretest", label: "Survey Pre-Test" },
];

export default function Home() {
  // Landing page toggle
  const [showLanding, setShowLanding] = useState(true);

  // Use case mode
  const [mode, setMode] = useState<UseCaseMode>("focus_group");

  // User-controlled view
  const [step, setStep] = useState<WorkflowStep>("input");

  // Data state (focus group)
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

  // R1 review state — raw reaction dicts from backend for continue endpoint
  const [r1RawReactions, setR1RawReactions] = useState<any[]>([]);
  const r1RawReactionsRef = useRef<any[]>([]);
  const [excludedPersonaIds, setExcludedPersonaIds] = useState<Set<string>>(new Set());

  // Agentic panel build metadata (shown when audience brief was used)
  const [audienceSpec, setAudienceSpec] = useState<Record<string, unknown> | null>(null);
  const [contextProjection, setContextProjection] = useState<Record<string, unknown> | null>(null);
  const [panelMetadata, setPanelMetadata] = useState<Record<string, unknown> | null>(null);
  const [agentLog, setAgentLog] = useState<Array<{ role: string; content: string }>>([]);

  // A/B test state
  const [abVariants, setAbVariants] = useState<string[]>([]);
  const [abReactions, setAbReactions] = useState<ABReaction[]>([]);
  const [abSummary, setAbSummary] = useState<ABSummary | null>(null);
  const [abRespondingCount, setAbRespondingCount] = useState(0);
  const abReactionsRef = useRef<ABReaction[]>([]);

  // Survey pre-test state
  const [surveyQuestions, setSurveyQuestions] = useState<string[]>([]);
  const [surveyReactions, setSurveyReactions] = useState<SurveyReaction[]>([]);
  const [surveySummary, setSurveySummary] = useState<SurveySummary | null>(null);
  const [surveyRespondingCount, setSurveyRespondingCount] = useState(0);
  const surveyReactionsRef = useRef<SurveyReaction[]>([]);

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
  const messageRef = useRef("");
  const stepRef = useRef<WorkflowStep>("input");

  // Keep stepRef in sync
  const setStepTracked = (s: WorkflowStep) => {
    stepRef.current = s;
    setStep(s);
  };

  // ── Reset all state ─────────────────────────────────────────────────
  const resetState = () => {
    setPanel([]);
    setRound1Reactions([]);
    setRound2Reactions([]);
    setRespondingIndex(0);
    setR1Aggregate(null);
    setR2Aggregate(null);
    setOptimized(null);
    setError(null);
    setTraceId(null);
    setAudienceSpec(null);
    setContextProjection(null);
    setPanelMetadata(null);
    setAgentLog([]);
    readyRef.current = { ...INITIAL_FLAGS };
    setReady({ ...INITIAL_FLAGS });
    r1ReactionsRef.current = [];
    r2ReactionsRef.current = [];
    r1RawReactionsRef.current = [];
    setR1RawReactions([]);
    setExcludedPersonaIds(new Set());
    panelRef.current = [];
    // A/B + Survey state
    setAbVariants([]);
    setAbReactions([]);
    setAbSummary(null);
    setAbRespondingCount(0);
    abReactionsRef.current = [];
    setSurveyQuestions([]);
    setSurveyReactions([]);
    setSurveySummary(null);
    setSurveyRespondingCount(0);
    surveyReactionsRef.current = [];
  };

  // ── Phase 1: Build panel (single entry point) ──────────────────────
  const handleStart = useCallback(
    async (msg: string, audienceBrief: string, filters: PanelFilters) => {
      resetState();
      setMessage(msg);
      messageRef.current = msg;
      setIsRunning(true);
      setStepTracked("panel_selection");

      if (audienceBrief) {
        // Agentic panel build via /api/build-panel
        await runBuildPanel(audienceBrief, msg, filters.panel_size, {
          onAudienceSpec: (data) => setAudienceSpec(data),
          onContextProjection: (data) => setContextProjection(data),
          onPanel: (data) => {
            const personas = data.panel as Persona[];
            panelRef.current = personas;
            setPanel(personas);
            markReady("panel");
          },
          onPanelMetadata: (data) => setPanelMetadata(data),
          onAgentLog: (data) => {
            const messages = (data.messages || []).map((m: any) => ({
              role: m.role || m.type || "unknown",
              content: typeof m.content === "string" ? m.content : JSON.stringify(m.content),
            }));
            setAgentLog(messages);
          },
          onDone: () => setIsRunning(false),
          onError: (err) => { setError(err); setIsRunning(false); },
        });
      } else {
        // Quick panel selection via /api/select-panel
        try {
          const result = await selectPanel(filters.panel_size, filters);
          const personas = result.panel as Persona[];
          panelRef.current = personas;
          setPanel(personas);
          markReady("panel");
          setIsRunning(false);
        } catch (err) {
          setError(err instanceof Error ? err.message : String(err));
          setIsRunning(false);
        }
      }
    },
    []
  );

  // ── Phase 2: Run R1 reactions (pauses for human review after) ──────
  const handleContinueFromPanel = useCallback(async () => {
    setIsRunning(true);
    r1ReactionsRef.current = [];
    r2ReactionsRef.current = [];
    r1RawReactionsRef.current = [];
    setRound1Reactions([]);
    setRound2Reactions([]);
    setR1RawReactions([]);
    setExcludedPersonaIds(new Set());
    setRespondingIndex(0);
    setStepTracked("round1_responding");

    const panelData = panelRef.current;
    const msg = messageRef.current;

    await runWithPanel(panelData, msg, {
      onReactionR1: (data) => {
        // Store raw reaction data for sending back to continue endpoint
        r1RawReactionsRef.current = [...r1RawReactionsRef.current, data];
        setR1RawReactions([...r1RawReactionsRef.current]);

        if (data.error) return;
        const persona = panelRef.current.find(
          (p) => p.uuid === data.persona_id
        ) || _buildFallbackPersona(data);

        const reaction: Reaction = {
          persona,
          reaction: data.reaction,
          sentiment_score: data.sentiment_score,
          relevance: data.relevance,
          tone_fit: data.tone_fit,
          cultural_flags: data.cultural_flags || [],
          model_used: data.model_used,
        };

        r1ReactionsRef.current = [...r1ReactionsRef.current, reaction];
        setRound1Reactions([...r1ReactionsRef.current]);
        setRespondingIndex(r1ReactionsRef.current.length);
      },

      onReactionsFiltered: (data) => {
        // Auto-excluded personas — pre-check them in the review UI
        const autoExcluded = new Set(data.removed_personas.map((p: any) => p.persona_id));
        setExcludedPersonaIds(autoExcluded);
      },

      onR1Complete: (data) => {
        setTraceId(data.trace_id);
        markReady("round1_done");
        setIsRunning(false);
        // Auto-advance to review step
        setStepTracked("round1_review");
      },

      onError: (err) => {
        setError(err);
        setIsRunning(false);
      },
    });
  }, []);

  // ── Phase 3: Continue after human review ─────────────────────────
  const handleContinueFromReview = useCallback(async () => {
    setIsRunning(true);
    r2ReactionsRef.current = [];
    setRound2Reactions([]);
    setRespondingIndex(0);

    const msg = messageRef.current;
    const panelData = panelRef.current;

    // Filter raw reactions to only the ones the user kept
    const keptReactions = r1RawReactionsRef.current.filter(
      (r) => !r.error && !excludedPersonaIds.has(r.persona_id)
    );

    // Also update the displayed R1 reactions to match
    const keptDisplayReactions = r1ReactionsRef.current.filter(
      (r) => !excludedPersonaIds.has(r.persona.uuid)
    );
    r1ReactionsRef.current = keptDisplayReactions;
    setRound1Reactions([...keptDisplayReactions]);

    // Filter panel for R2 to only kept personas
    const keptPanel = panelData.filter(
      (p) => !excludedPersonaIds.has(p.uuid)
    );

    await continueAfterReview(msg, keptPanel, keptReactions, traceId || "", {
      onSummaryR1: (data) => {
        setR1Aggregate({
          avg_sentiment: data.avg_sentiment,
          relevance_pct: data.relevance_pct,
          tone_distribution: data.tone_distribution,
          top_cultural_flags: data.top_cultural_flags,
        });
        markReady("round1_summary");
        setStepTracked("round1_summary");
      },

      onOptimized: (data) => {
        setOptimized({
          improved_message: data.improved_message,
          changes_made: data.changes_made,
        });
        markReady("optimization");
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
          relevance: data.relevance,
          tone_fit: data.tone_fit,
          cultural_flags: data.cultural_flags || [],
          model_used: data.model_used,
        };

        r2ReactionsRef.current = [...r2ReactionsRef.current, reaction];
        setRound2Reactions([...r2ReactionsRef.current]);
        setRespondingIndex(r2ReactionsRef.current.length);
      },

      onSummaryR2: (data) => {
        setR2Aggregate({
          avg_sentiment: data.avg_sentiment,
          relevance_pct: data.relevance_pct,
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
    });
  }, [excludedPersonaIds, traceId]);

  // ── A/B Copy Test flow — Phase 1: just build panel + store variants ─
  const handleABTestStart = useCallback(
    async (variants: string[], audienceBrief: string, filters: PanelFilters) => {
      resetState();
      setAbVariants(variants);
      // Use first variant as the "message" for panel building context
      setMessage(variants[0]);
      messageRef.current = variants[0];
      setIsRunning(true);
      setStepTracked("panel_selection");

      if (audienceBrief) {
        await runBuildPanel(audienceBrief, variants[0], filters.panel_size, {
          onAudienceSpec: (data) => setAudienceSpec(data),
          onContextProjection: (data) => setContextProjection(data),
          onPanel: (data) => {
            const personas = data.panel as Persona[];
            panelRef.current = personas;
            setPanel(personas);
            markReady("panel");
          },
          onPanelMetadata: (data) => setPanelMetadata(data),
          onAgentLog: (data) => {
            const messages = (data.messages || []).map((m: any) => ({
              role: m.role || m.type || "unknown",
              content: typeof m.content === "string" ? m.content : JSON.stringify(m.content),
            }));
            setAgentLog(messages);
          },
          onDone: () => setIsRunning(false),
          onError: (err) => { setError(err); setIsRunning(false); },
        }, "ab_copy_test");
      } else {
        try {
          const result = await selectPanel(filters.panel_size, filters);
          const personas = result.panel as Persona[];
          panelRef.current = personas;
          setPanel(personas);
          markReady("panel");
          setIsRunning(false);
        } catch (err) {
          setError(err instanceof Error ? err.message : String(err));
          setIsRunning(false);
        }
      }
    },
    []
  );

  // ── A/B Copy Test flow — Phase 2: run test after panel review ──────
  const handleContinueFromPanelAB = useCallback(async () => {
    setIsRunning(true);
    setStepTracked("round1_responding");
    abReactionsRef.current = [];
    setAbRespondingCount(0);

    const panelData = panelRef.current;

    await runABTest(abVariants, panelData, "", {
      onTrace: (data) => setTraceId(data.trace_id),
      onABReaction: (data) => {
        abReactionsRef.current = [...abReactionsRef.current, data];
        setAbReactions([...abReactionsRef.current]);
        setAbRespondingCount(abReactionsRef.current.length);
      },
      onABSummary: (data) => {
        setAbSummary(data);
        markReady("round1_done");
        markReady("final");
      },
      onDone: (data) => {
        setTraceId(data.trace_id);
        setIsRunning(false);
        setStepTracked("final_comparison");
      },
      onError: (err) => {
        setError(err);
        setIsRunning(false);
      },
    });
  }, [abVariants]);

  // ── Survey Pre-Test flow — Phase 1: just build panel + store questions
  const handleSurveyStart = useCallback(
    async (questions: string[], audienceBrief: string, filters: PanelFilters) => {
      resetState();
      setSurveyQuestions(questions);
      setMessage(questions[0]);
      messageRef.current = questions[0];
      setIsRunning(true);
      setStepTracked("panel_selection");

      if (audienceBrief) {
        await runBuildPanel(audienceBrief, questions[0], filters.panel_size, {
          onAudienceSpec: (data) => setAudienceSpec(data),
          onContextProjection: (data) => setContextProjection(data),
          onPanel: (data) => {
            const personas = data.panel as Persona[];
            panelRef.current = personas;
            setPanel(personas);
            markReady("panel");
          },
          onPanelMetadata: (data) => setPanelMetadata(data),
          onAgentLog: (data) => {
            const messages = (data.messages || []).map((m: any) => ({
              role: m.role || m.type || "unknown",
              content: typeof m.content === "string" ? m.content : JSON.stringify(m.content),
            }));
            setAgentLog(messages);
          },
          onDone: () => setIsRunning(false),
          onError: (err) => { setError(err); setIsRunning(false); },
        }, "survey_pretest");
      } else {
        try {
          const result = await selectPanel(filters.panel_size, filters);
          const personas = result.panel as Persona[];
          panelRef.current = personas;
          setPanel(personas);
          markReady("panel");
          setIsRunning(false);
        } catch (err) {
          setError(err instanceof Error ? err.message : String(err));
          setIsRunning(false);
        }
      }
    },
    []
  );

  // ── Survey Pre-Test flow — Phase 2: run test after panel review ─────
  const handleContinueFromPanelSurvey = useCallback(async () => {
    setIsRunning(true);
    setStepTracked("round1_responding");
    surveyReactionsRef.current = [];
    setSurveyRespondingCount(0);

    const panelData = panelRef.current;

    await runSurveyPreTest(surveyQuestions, panelData, "", {
      onTrace: (data) => setTraceId(data.trace_id),
      onSurveyReaction: (data) => {
        surveyReactionsRef.current = [...surveyReactionsRef.current, data];
        setSurveyReactions([...surveyReactionsRef.current]);
        setSurveyRespondingCount(surveyReactionsRef.current.length);
      },
      onSurveySummary: (data) => {
        setSurveySummary(data);
        markReady("round1_done");
        markReady("final");
      },
      onDone: (data) => {
        setTraceId(data.trace_id);
        setIsRunning(false);
        setStepTracked("final_comparison");
      },
      onError: (err) => {
        setError(err);
        setIsRunning(false);
      },
    });
  }, [surveyQuestions]);

  // Clickable stepper — can jump to any step that has data
  const handleStepClick = (targetStep: WorkflowStep) => {
    const canNavigate: Record<WorkflowStep, boolean> = {
      input: true,
      panel_selection: ready.panel,
      round1_responding: r1ReactionsRef.current.length > 0 || abReactionsRef.current.length > 0 || surveyReactionsRef.current.length > 0,
      round1_review: ready.round1_done,
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

  const handleRemovePersona = (uuid: string) => {
    const updated = panelRef.current.filter((p) => p.uuid !== uuid);
    panelRef.current = updated;
    setPanel([...updated]);
  };

  const handleRestart = () => {
    setStepTracked("input");
    setMessage("");
    messageRef.current = "";
    setIsRunning(false);
    resetState();
  };

  // ── Render ─────────────────────────────────────────────────────────

  if (showLanding) {
    return <LandingPage onEnterApp={() => setShowLanding(false)} />;
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-[var(--color-border)] bg-[var(--color-bg-card)]">
        <div className="max-w-5xl mx-auto px-4 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Image
              src="/logo-mark.png"
              alt="MaplePulse"
              width={512}
              height={512}
              className="h-8 w-auto object-contain"
              priority
            />
            <div className="flex items-baseline gap-0">
              <span className="text-xl font-bold tracking-tight" style={{ color: "#C1272D" }}>Maple</span>
              <span className="text-xl font-bold tracking-tight" style={{ color: "#1B7B7E" }}>Pulse</span>
            </div>
            {isRunning && (
              <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] ml-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-pulse" />
                Running
              </div>
            )}
          </div>
          {panel.length > 0 && step !== "panel_selection" && (
            <button
              onClick={() => setShowPanelDrawer(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors cursor-pointer"
            >
              <Users size={14} />
              Panel ({panel.length})
            </button>
          )}
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="max-w-5xl mx-auto px-4 py-2">
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

      {/* Stepper */}
      {step !== "input" && (
        <div className="max-w-5xl mx-auto px-4 py-3">
          <WorkflowStepper currentStep={step} onStepClick={handleStepClick} ready={{ ...ready }} mode={mode} />
        </div>
      )}

      {/* Main content */}
      <main className="max-w-5xl mx-auto px-4 py-4 pb-16">

        {/* ── Mode Selector (only on input step) ── */}
        {step === "input" && (
          <div className="max-w-3xl mx-auto mb-6 flex justify-center">
            <div className="inline-flex rounded-lg bg-[var(--color-surface)] p-1 gap-0.5">
              {MODE_OPTIONS.map(({ mode: m, label }) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all cursor-pointer ${
                    mode === m
                      ? "bg-[var(--color-bg-card)] text-[var(--color-text)] shadow-sm"
                      : "text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Focus Group Mode ── */}
        {mode === "focus_group" && (
          <>
            {step === "input" && <InputStep onStart={handleStart} />}

            {step === "panel_selection" && panel.length > 0 && (
              <div className="space-y-4">
                {audienceSpec && (
                  <div className="flex flex-wrap gap-2 text-xs">
                    {Object.entries(audienceSpec).filter(([, v]) => v != null && v !== "" && !(Array.isArray(v) && v.length === 0)).map(([k, v]) => (
                      <span key={k} className="px-2 py-1 rounded-md bg-[var(--color-surface)] text-[var(--color-text-muted)]">
                        <span className="text-[var(--color-text-light)]">{k.replace(/_/g, " ")}: </span>
                        {Array.isArray(v) ? (v as string[]).join(", ")
                          : (typeof v === "object" && v !== null && "min" in v && "max" in v)
                            ? (k.includes("income")
                              ? `$${((v as Record<string, number>).min).toLocaleString()}–$${((v as Record<string, number>).max).toLocaleString()}`
                              : `${(v as Record<string, number>).min}–${(v as Record<string, number>).max}`)
                          : String(v)}
                      </span>
                    ))}
                  </div>
                )}

                <PanelView
                  panel={panel}
                  onContinue={!isRunning ? handleContinueFromPanel : undefined}
                  onStop={!isRunning ? handleRestart : undefined}
                  onRemovePersona={!isRunning ? handleRemovePersona : undefined}
                />
              </div>
            )}

            {step === "panel_selection" && panel.length === 0 && (
              <div className="flex items-center justify-center py-16">
                <div className="flex items-center gap-2 text-[var(--color-text-muted)]">
                  <div className="w-4 h-4 border-2 border-[var(--color-text-light)] border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm">Building panel...</span>
                </div>
              </div>
            )}

            {step === "round1_responding" && (
              <ReactionsView
                reactions={round1Reactions}
                respondingIndex={respondingIndex}
                round={1}
                onAllDone={() => setStepTracked("round1_review")}
                isReady={ready.round1_done}
                message={message}
                continueLabel="Review Reactions"
              />
            )}

            {step === "round1_review" && ready.round1_done && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-semibold">
                      Review Reactions
                    </h2>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      Deselect any that don&apos;t make sense.
                      {excludedPersonaIds.size > 0 && (
                        <span className="ml-1 text-amber-600 font-medium">
                          {excludedPersonaIds.size} excluded
                        </span>
                      )}
                    </p>
                  </div>
                  <button
                    onClick={handleContinueFromReview}
                    disabled={isRunning}
                    className="px-4 py-1.5 bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] text-white rounded-lg text-sm font-medium transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Continue ({round1Reactions.length - excludedPersonaIds.size})
                  </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
                  {round1Reactions.map((r, i) => {
                    const isExcluded = excludedPersonaIds.has(r.persona.uuid);
                    return (
                      <div
                        key={r.persona.uuid + "-review-" + i}
                        className={`relative rounded-lg border p-3 transition-all ${
                          isExcluded
                            ? "opacity-30 border-[var(--color-border)] bg-[var(--color-surface)]"
                            : "border-[var(--color-border)] bg-[var(--color-bg-card)]"
                        }`}
                      >
                        <button
                          onClick={() => {
                            setExcludedPersonaIds((prev) => {
                              const next = new Set(prev);
                              if (next.has(r.persona.uuid)) {
                                next.delete(r.persona.uuid);
                              } else {
                                next.add(r.persona.uuid);
                              }
                              return next;
                            });
                          }}
                          className="absolute top-2.5 right-2.5 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors cursor-pointer"
                          style={{
                            borderColor: isExcluded ? "var(--color-text-light)" : "var(--color-primary)",
                            backgroundColor: isExcluded ? "transparent" : "var(--color-primary)",
                          }}
                          title={isExcluded ? "Include" : "Exclude"}
                        >
                          {!isExcluded && (
                            <svg width="12" height="12" viewBox="0 0 14 14" fill="none">
                              <path d="M3 7L6 10L11 4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                          )}
                        </button>

                        <div className="pr-7">
                          <p className="text-sm font-medium mb-0.5">
                            {r.persona.age} {r.persona.sex} &middot; {r.persona.occupation}
                          </p>
                          <p className="text-sm text-[var(--color-text)] mb-1.5">&ldquo;{r.reaction}&rdquo;</p>
                          <div className="flex items-center gap-2 text-[11px] text-[var(--color-text-muted)]">
                            <span>{r.sentiment_score}/5</span>
                            <span>{r.tone_fit}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
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
                message={optimized?.improved_message ?? message}
                round1Reactions={round1Reactions}
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
                round1Reactions={round1Reactions}
              />
            )}

            {step === "final_comparison" && r1Aggregate && r2Aggregate && optimized && (
              <FinalComparison
                originalMessage={message}
                optimized={optimized}
                round1={r1Aggregate}
                round2={r2Aggregate}
                traceId={traceId}
                onRestart={handleRestart}
              />
            )}
          </>
        )}

        {/* ── A/B Copy Test Mode ── */}
        {mode === "ab_copy_test" && (
          <>
            {step === "input" && <ABTestInput onStart={handleABTestStart} />}

            {step === "panel_selection" && panel.length === 0 && (
              <div className="flex items-center justify-center py-16">
                <div className="flex items-center gap-2 text-[var(--color-text-muted)]">
                  <div className="w-4 h-4 border-2 border-[var(--color-text-light)] border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm">Building panel...</span>
                </div>
              </div>
            )}

            {step === "panel_selection" && panel.length > 0 && (
              <div className="space-y-4">
                <PanelView
                  panel={panel}
                  onContinue={!isRunning ? handleContinueFromPanelAB : undefined}
                  onStop={!isRunning ? handleRestart : undefined}
                  onRemovePersona={!isRunning ? handleRemovePersona : undefined}
                />
              </div>
            )}

            {(step === "round1_responding" || step === "final_comparison") && (
              <ABResultsView
                reactions={abReactions}
                summary={abSummary}
                variants={abVariants}
                respondingCount={abRespondingCount}
                totalPanel={panel.length}
                isComplete={!isRunning && abSummary !== null}
                onRestart={handleRestart}
              />
            )}
          </>
        )}

        {/* ── Survey Pre-Test Mode ── */}
        {mode === "survey_pretest" && (
          <>
            {step === "input" && <SurveyPreTestInput onStart={handleSurveyStart} />}

            {step === "panel_selection" && panel.length === 0 && (
              <div className="flex items-center justify-center py-16">
                <div className="flex items-center gap-2 text-[var(--color-text-muted)]">
                  <div className="w-4 h-4 border-2 border-[var(--color-text-light)] border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm">Building panel...</span>
                </div>
              </div>
            )}

            {step === "panel_selection" && panel.length > 0 && (
              <div className="space-y-4">
                <PanelView
                  panel={panel}
                  onContinue={!isRunning ? handleContinueFromPanelSurvey : undefined}
                  onStop={!isRunning ? handleRestart : undefined}
                  onRemovePersona={!isRunning ? handleRemovePersona : undefined}
                />
              </div>
            )}

            {(step === "round1_responding" || step === "final_comparison") && (
              <SurveyResultsView
                reactions={surveyReactions}
                summary={surveySummary}
                questions={surveyQuestions}
                respondingCount={surveyRespondingCount}
                totalPanel={panel.length}
                isComplete={!isRunning && surveySummary !== null}
                onRestart={handleRestart}
              />
            )}
          </>
        )}
      </main>

      {/* Panel Drawer */}
      {showPanelDrawer && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setShowPanelDrawer(false)}
          />
          <div className="relative w-full max-w-xl bg-[var(--color-bg)] overflow-y-auto shadow-xl animate-[slideIn_0.2s_ease-out]">
            <div className="sticky top-0 bg-[var(--color-bg-card)] border-b border-[var(--color-border)] px-4 py-2.5 flex items-center justify-between z-10">
              <span className="text-sm font-medium">{panel.length} personas</span>
              <button
                onClick={() => setShowPanelDrawer(false)}
                className="p-1 rounded hover:bg-[var(--color-surface)] transition-colors cursor-pointer text-[var(--color-text-muted)]"
              >
                <Users size={16} />
              </button>
            </div>
            <div className="p-3">
              <PanelView panel={panel} hideHeader />
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
