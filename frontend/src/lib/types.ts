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
  | "round1_review"
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

// === Use Case Mode ===
export type UseCaseMode = "focus_group" | "ab_copy_test" | "survey_pretest";

// === A/B Copy Test Types ===
export interface CopyVariantReaction {
  reaction: string;
  sentiment_score: number;
  relevance: "irrelevant" | "somewhat" | "directly_relevant";
  tone_fit: "natural" | "acceptable" | "awkward" | "offensive";
  cultural_flags: string[];
  preference_reason: string;
}

export interface ABReaction {
  persona_id: string;
  age: number;
  sex: string;
  province: string;
  city: string;
  occupation: string;
  income_bracket: string;
  variant_reactions: CopyVariantReaction[];
  preferred_variant: number; // 1-indexed
  preference_explanation: string;
  model_used?: string;
  error?: string;
}

export interface VariantSummary {
  variant_index: number;
  variant_label: string;
  variant_text: string;
  avg_sentiment: number;
  relevance_pct: number;
  tone_distribution: Record<string, number>;
  top_cultural_flags: string[];
  preference_count: number;
  preference_pct: number;
}

export interface ABSummary {
  variant_summaries: VariantSummary[];
  winner_index: number;
  winner_label: string;
  total_respondents: number;
  elapsed: number;
}

// === Survey Pre-Test Types ===
export interface SurveyQuestionReaction {
  question_index: number;
  comprehension: string;
  clarity_score: number;
  bias_flags: string[];
  ambiguity_flags: string[];
  cultural_flags: string[];
  would_answer_honestly: boolean;
  suggested_improvement: string;
}

export interface SurveyReaction {
  persona_id: string;
  age: number;
  sex: string;
  province: string;
  city: string;
  occupation: string;
  education_level: string;
  cultural_background: string;
  income_bracket: string;
  question_reactions: SurveyQuestionReaction[];
  overall_survey_impression: string;
  model_used?: string;
  error?: string;
}

export interface QuestionSummary {
  question_index: number;
  question_text: string;
  avg_clarity: number;
  honest_pct: number;
  top_bias_flags: string[];
  top_ambiguity_flags: string[];
  top_cultural_flags: string[];
  sample_comprehensions: string[];
  sample_improvements: string[];
}

export interface SurveySummary {
  question_summaries: QuestionSummary[];
  total_respondents: number;
  elapsed: number;
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
