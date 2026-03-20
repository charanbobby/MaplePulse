// === MaplePulse Types ===

export interface Persona {
  uuid: string;
  age: number;
  sex: string;
  occupation: string;
  education_level: string;
  marital_status: string;
  planning_area: string;
  province: string;
  immigration_status: string;
  indigenous_identity: string;
  visible_minority: string;
  languages_spoken: string;
  housing: string;
  cultural_background: string;
  political_leaning: string;
  religion: string;
  top_concerns: string[];
  commute_mode: string;
  estimated_annual_income: number;
  income_bracket: string;
}

export interface Reaction {
  persona: Persona;
  reaction: string;
  sentiment_score: number;
  relevance: "irrelevant" | "somewhat" | "directly_relevant";
  tone_fit: "natural" | "acceptable" | "awkward" | "offensive";
  cultural_flags: string[];
  model_used?: string;
}

export interface AggregatedResults {
  avg_sentiment: number;
  relevance_pct: number;
  tone_distribution: Record<string, number>;
  top_cultural_flags: string[];
}

export interface OptimizedMessage {
  improved_message: string;
  changes_made: string[];
}

export interface FocusGroupRun {
  id: string;
  input_message: string;
  use_case: string;
  panel: Persona[];
  round1_reactions: Reaction[];
  round1_aggregate: AggregatedResults;
  optimized: OptimizedMessage;
  round2_reactions: Reaction[];
  round2_aggregate: AggregatedResults;
}

// Workflow step tracking
export type WorkflowStep =
  | "input"
  | "panel_selection"
  | "round1_responding"
  | "round1_summary"
  | "optimization"
  | "round2_responding"
  | "round2_summary"
  | "final_comparison";

export interface WorkflowState {
  step: WorkflowStep;
  message: string;
  use_case: string;
  filters: PanelFilters;
  panel: Persona[];
  round1_reactions: Reaction[];
  round1_aggregate: AggregatedResults | null;
  optimized: OptimizedMessage | null;
  round2_reactions: Reaction[];
  round2_aggregate: AggregatedResults | null;
  is_loading: boolean;
  responding_index: number; // tracks which persona is "responding" during animation
}

export interface PanelFilters {
  panel_size: number;
  province?: string[];
  age_range?: [number, number];
  sex?: string[];
  income_bracket?: string[];
  education_level?: string[];
  marital_status?: string[];
  immigration_status?: string[];
  indigenous_identity?: string[];
  visible_minority?: string[];
  political_leaning?: string[];
  religion?: string[];
  commute_mode?: string[];
  housing_type?: string[];
  languages?: string[];
  top_concerns?: string[];
}
