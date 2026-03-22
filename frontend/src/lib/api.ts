/**
 * SSE client for the MaplePulse backend API.
 * Streams focus group results as they arrive from the LangGraph pipeline.
 */

export interface SSECallbacks {
  onStep: (data: { step: string; status: string }) => void;
  onClassify: (data: { use_case: string; confidence: number; reasoning: string; elapsed: number }) => void;
  onPanel: (data: { panel: any[] }) => void;
  onReactionR1: (data: any) => void;
  onSummaryR1: (data: any) => void;
  onOptimized: (data: { improved_message: string; changes_made: string[]; elapsed: number }) => void;
  onReactionR2: (data: any) => void;
  onSummaryR2: (data: any) => void;
  onDone: (data: { trace_id: string }) => void;
  onError: (error: string) => void;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// ── Build Panel (v3 panel-only mode) ──────────────────────────────

export interface BuildPanelCallbacks {
  onAudienceSpec: (data: any) => void;
  onContextProjection: (data: any) => void;
  onPanel: (data: { panel: any[] }) => void;
  onPanelMetadata: (data: any) => void;
  onAgentLog: (data: { messages: any[] }) => void;
  onDone: (data: any) => void;
  onError: (error: string) => void;
}

export async function runBuildPanel(
  audienceBrief: string,
  message: string,
  panelSize: number,
  callbacks: BuildPanelCallbacks,
  useCase: string = "localization",
): Promise<void> {
  const body = {
    audience_brief: audienceBrief,
    message,
    panel_size: panelSize,
    use_case: useCase,
  };

  try {
    const response = await fetch(`${BACKEND_URL}/api/build-panel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      callbacks.onError(`Backend error: ${response.status} ${response.statusText}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      callbacks.onError("No response body");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      let currentEvent = "";
      let currentData = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          currentData = line.slice(6);
        } else if (line === "" && currentEvent && currentData) {
          try {
            const data = JSON.parse(currentData);
            switch (currentEvent) {
              case "audience_spec":
                callbacks.onAudienceSpec(data);
                break;
              case "context_projection":
                callbacks.onContextProjection(data);
                break;
              case "panel":
                callbacks.onPanel(data);
                break;
              case "panel_metadata":
                callbacks.onPanelMetadata(data);
                break;
              case "agent_log":
                callbacks.onAgentLog(data);
                break;
              case "done":
                callbacks.onDone(data);
                break;
              case "error":
                callbacks.onError(data.message || "Unknown error");
                break;
            }
          } catch {
            // Skip malformed JSON
          }
          currentEvent = "";
          currentData = "";
        }
      }
    }
  } catch (err) {
    callbacks.onError(`Connection error: ${err instanceof Error ? err.message : String(err)}`);
  }
}

// ── Select Panel (quick, no LLM) ───────────────────────────────────

export async function selectPanel(
  panelSize: number,
  filters: import("@/lib/types").PanelFilters,
): Promise<{ panel: any[] }> {
  const { panel_size, ...filterFields } = filters;
  const cleanFilters: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(filterFields)) {
    if (Array.isArray(value) && value.length > 0) {
      cleanFilters[key] = value;
    } else if (value != null && !Array.isArray(value)) {
      cleanFilters[key] = value;
    }
  }

  const response = await fetch(`${BACKEND_URL}/api/select-panel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      panel_size: panelSize,
      filters: Object.keys(cleanFilters).length > 0 ? cleanFilters : undefined,
      seed: Math.floor(Math.random() * 99999),
    }),
  });

  if (!response.ok) {
    throw new Error(`Backend error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

// ── Run With Panel (reactions pipeline) ─────────────────────────────

export interface RunWithPanelCallbacks {
  onReactionR1: (data: any) => void;
  onReactionsFiltered?: (data: { kept: number; removed: number; removed_personas: any[] }) => void;
  onR1Complete: (data: { trace_id: string; elapsed: number; auto_removed_ids: string[] }) => void;
  onError: (error: string) => void;
}

export interface ContinueAfterReviewCallbacks {
  onSummaryR1: (data: any) => void;
  onOptimized: (data: { improved_message: string; changes_made: string[]; elapsed: number }) => void;
  onReactionR2: (data: any) => void;
  onSummaryR2: (data: any) => void;
  onDone: (data: { trace_id: string }) => void;
  onError: (error: string) => void;
}

export async function runWithPanel(
  panel: any[],
  message: string,
  callbacks: RunWithPanelCallbacks,
): Promise<void> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/run-with-panel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ panel, message }),
    });

    if (!response.ok) {
      callbacks.onError(`Backend error: ${response.status} ${response.statusText}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      callbacks.onError("No response body");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      let currentEvent = "";
      let currentData = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          currentData = line.slice(6);
        } else if (line === "" && currentEvent && currentData) {
          try {
            const data = JSON.parse(currentData);
            switch (currentEvent) {
              case "reaction_r1":
                callbacks.onReactionR1(data);
                break;
              case "reactions_filtered":
                callbacks.onReactionsFiltered?.(data);
                break;
              case "r1_complete":
                callbacks.onR1Complete(data);
                break;
              case "error":
                callbacks.onError(data.message || "Unknown error");
                break;
            }
          } catch {
            // Skip malformed JSON
          }
          currentEvent = "";
          currentData = "";
        }
      }
    }
  } catch (err) {
    callbacks.onError(`Connection error: ${err instanceof Error ? err.message : String(err)}`);
  }
}

// ── Continue After Review (summary → optimize → R2) ────────────────

export async function continueAfterReview(
  message: string,
  panel: any[],
  r1Reactions: any[],
  traceId: string,
  callbacks: ContinueAfterReviewCallbacks,
): Promise<void> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/continue-after-review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        panel,
        r1_reactions: r1Reactions,
        trace_id: traceId,
      }),
    });

    if (!response.ok) {
      callbacks.onError(`Backend error: ${response.status} ${response.statusText}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      callbacks.onError("No response body");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      let currentEvent = "";
      let currentData = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          currentData = line.slice(6);
        } else if (line === "" && currentEvent && currentData) {
          try {
            const data = JSON.parse(currentData);
            switch (currentEvent) {
              case "summary_r1":
                callbacks.onSummaryR1(data);
                break;
              case "optimized":
                callbacks.onOptimized(data);
                break;
              case "reaction_r2":
                callbacks.onReactionR2(data);
                break;
              case "summary_r2":
                callbacks.onSummaryR2(data);
                break;
              case "done":
                callbacks.onDone(data);
                break;
              case "error":
                callbacks.onError(data.message || "Unknown error");
                break;
            }
          } catch {
            // Skip malformed JSON
          }
          currentEvent = "";
          currentData = "";
        }
      }
    }
  } catch (err) {
    callbacks.onError(`Connection error: ${err instanceof Error ? err.message : String(err)}`);
  }
}

// ── A/B Copy Test ───────────────────────────────────────────────────

export interface ABTestCallbacks {
  onTrace: (data: { trace_id: string }) => void;
  onABReaction: (data: any) => void;
  onABSummary: (data: any) => void;
  onDone: (data: { trace_id: string }) => void;
  onError: (error: string) => void;
}

export async function runABTest(
  variants: string[],
  panel: any[],
  audienceBrief: string,
  callbacks: ABTestCallbacks,
): Promise<void> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/ab-test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ variants, panel, audience_brief: audienceBrief }),
    });

    if (!response.ok) {
      callbacks.onError(`Backend error: ${response.status} ${response.statusText}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      callbacks.onError("No response body");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      let currentEvent = "";
      let currentData = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          currentData = line.slice(6);
        } else if (line === "" && currentEvent && currentData) {
          try {
            const data = JSON.parse(currentData);
            switch (currentEvent) {
              case "trace":
                callbacks.onTrace(data);
                break;
              case "ab_reaction":
                callbacks.onABReaction(data);
                break;
              case "ab_summary":
                callbacks.onABSummary(data);
                break;
              case "done":
                callbacks.onDone(data);
                break;
              case "error":
                callbacks.onError(data.message || "Unknown error");
                break;
            }
          } catch {
            // Skip malformed JSON
          }
          currentEvent = "";
          currentData = "";
        }
      }
    }
  } catch (err) {
    callbacks.onError(`Connection error: ${err instanceof Error ? err.message : String(err)}`);
  }
}

// ── Survey Pre-Test ─────────────────────────────────────────────────

export interface SurveyPreTestCallbacks {
  onTrace: (data: { trace_id: string }) => void;
  onSurveyReaction: (data: any) => void;
  onSurveySummary: (data: any) => void;
  onDone: (data: { trace_id: string }) => void;
  onError: (error: string) => void;
}

export async function runSurveyPreTest(
  questions: string[],
  panel: any[],
  audienceBrief: string,
  callbacks: SurveyPreTestCallbacks,
): Promise<void> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/survey-pretest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ questions, panel, audience_brief: audienceBrief }),
    });

    if (!response.ok) {
      callbacks.onError(`Backend error: ${response.status} ${response.statusText}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      callbacks.onError("No response body");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      let currentEvent = "";
      let currentData = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          currentData = line.slice(6);
        } else if (line === "" && currentEvent && currentData) {
          try {
            const data = JSON.parse(currentData);
            switch (currentEvent) {
              case "trace":
                callbacks.onTrace(data);
                break;
              case "survey_reaction":
                callbacks.onSurveyReaction(data);
                break;
              case "survey_summary":
                callbacks.onSurveySummary(data);
                break;
              case "done":
                callbacks.onDone(data);
                break;
              case "error":
                callbacks.onError(data.message || "Unknown error");
                break;
            }
          } catch {
            // Skip malformed JSON
          }
          currentEvent = "";
          currentData = "";
        }
      }
    }
  } catch (err) {
    callbacks.onError(`Connection error: ${err instanceof Error ? err.message : String(err)}`);
  }
}

// ── Feedback ────────────────────────────────────────────────────────

export async function submitFeedback(
  traceId: string,
  value: "good" | "bad" | "partial",
  comment?: string,
): Promise<void> {
  await fetch(`${BACKEND_URL}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ trace_id: traceId, value, comment }),
  });
}

export async function runFocusGroup(
  message: string,
  filters: import("@/lib/types").PanelFilters,
  callbacks: SSECallbacks,
): Promise<void> {
  // Build the filters object, omitting empty arrays
  const { panel_size, ...filterFields } = filters;
  const cleanFilters: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(filterFields)) {
    if (Array.isArray(value) && value.length > 0) {
      cleanFilters[key] = value;
    } else if (value != null && !Array.isArray(value)) {
      cleanFilters[key] = value;
    }
  }

  const body = {
    message,
    panel_size,
    filters: Object.keys(cleanFilters).length > 0 ? cleanFilters : undefined,
    seed: Math.floor(Math.random() * 99999),
  };

  try {
    const response = await fetch(`${BACKEND_URL}/api/focus-group`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      callbacks.onError(`Backend error: ${response.status} ${response.statusText}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      callbacks.onError("No response body");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events from buffer
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // keep incomplete line in buffer

      let currentEvent = "";
      let currentData = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          currentData = line.slice(6);
        } else if (line === "" && currentEvent && currentData) {
          // Complete event
          try {
            const data = JSON.parse(currentData);
            switch (currentEvent) {
              case "step":
                callbacks.onStep(data);
                break;
              case "classify":
                callbacks.onClassify(data);
                break;
              case "panel":
                callbacks.onPanel(data);
                break;
              case "reaction_r1":
                callbacks.onReactionR1(data);
                break;
              case "summary_r1":
                callbacks.onSummaryR1(data);
                break;
              case "optimized":
                callbacks.onOptimized(data);
                break;
              case "reaction_r2":
                callbacks.onReactionR2(data);
                break;
              case "summary_r2":
                callbacks.onSummaryR2(data);
                break;
              case "done":
                callbacks.onDone(data);
                break;
            }
          } catch {
            // Skip malformed JSON
          }
          currentEvent = "";
          currentData = "";
        }
      }
    }
  } catch (err) {
    callbacks.onError(`Connection error: ${err instanceof Error ? err.message : String(err)}`);
  }
}
