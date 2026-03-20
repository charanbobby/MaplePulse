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
