"use client";

import { AlertTriangle, CheckCircle, Eye, ChevronDown, Users, MessageSquareWarning } from "lucide-react";
import type { SurveyReaction, SurveySummary, QuestionSummary } from "@/lib/types";

interface SurveyResultsViewProps {
  reactions: SurveyReaction[];
  summary: SurveySummary | null;
  questions: string[];
  respondingCount: number;
  totalPanel: number;
  isComplete: boolean;
  onRestart: () => void;
}

function ClarityGauge({ score }: { score: number }) {
  const color =
    score >= 4 ? "text-emerald-600" : score >= 3 ? "text-amber-600" : "text-red-600";
  const bgColor =
    score >= 4 ? "bg-emerald-500" : score >= 3 ? "bg-amber-500" : "bg-red-500";
  const label =
    score >= 4.5
      ? "Excellent"
      : score >= 3.5
        ? "Clear"
        : score >= 2.5
          ? "Needs Work"
          : "Confusing";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-[var(--color-bg)] rounded-full overflow-hidden">
        <div
          className={`h-full ${bgColor} rounded-full transition-all`}
          style={{ width: `${(score / 5) * 100}%` }}
        />
      </div>
      <span className={`text-xs font-semibold ${color}`}>
        {score.toFixed(1)} &mdash; {label}
      </span>
    </div>
  );
}

function FlagList({ flags, color }: { flags: string[]; color: "amber" | "red" | "blue" }) {
  if (flags.length === 0) return <span className="text-xs text-[var(--color-text-muted)]">None detected</span>;
  const colors = {
    amber: "bg-amber-50 text-amber-700 border-amber-200",
    red: "bg-red-50 text-red-700 border-red-200",
    blue: "bg-blue-50 text-blue-700 border-blue-200",
  };
  return (
    <div className="flex flex-wrap gap-1">
      {flags.map((flag, i) => (
        <span key={i} className={`text-[10px] px-2 py-0.5 rounded-full border ${colors[color]}`}>
          {flag}
        </span>
      ))}
    </div>
  );
}

function QuestionCard({ qs }: { qs: QuestionSummary }) {
  const clarityColor =
    qs.avg_clarity >= 4 ? "border-emerald-300" : qs.avg_clarity >= 3 ? "border-amber-300" : "border-red-300";

  const hasIssues =
    qs.top_bias_flags.length > 0 || qs.top_ambiguity_flags.length > 0 || qs.top_cultural_flags.length > 0;

  return (
    <div className={`rounded-xl border-2 ${clarityColor} bg-[var(--color-bg-card)] shadow-sm p-5 space-y-4`}>
      {/* Question header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-bold text-[var(--color-primary)] bg-[var(--color-primary)]/10 px-2 py-0.5 rounded">
            Q{qs.question_index + 1}
          </span>
          {hasIssues ? (
            <AlertTriangle size={14} className="text-amber-500" />
          ) : (
            <CheckCircle size={14} className="text-emerald-500" />
          )}
        </div>
        <p className="text-sm font-medium text-[var(--color-text)]">{qs.question_text}</p>
      </div>

      {/* Clarity score */}
      <div>
        <label className="text-[10px] uppercase tracking-wide text-[var(--color-text-muted)] mb-1 block">
          Clarity Score
        </label>
        <ClarityGauge score={qs.avg_clarity} />
      </div>

      {/* Honesty rate */}
      <div className="flex items-center gap-2">
        <label className="text-[10px] uppercase tracking-wide text-[var(--color-text-muted)]" title="Percentage of respondents who feel this question allows them to give a truthful answer without being pushed toward a particular response">
          Neutral Wording
        </label>
        <span
          className={`text-xs font-semibold ${qs.honest_pct >= 80 ? "text-emerald-600" : qs.honest_pct >= 60 ? "text-amber-600" : "text-red-600"}`}
        >
          {qs.honest_pct}%
        </span>
      </div>

      {/* Flags */}
      <div className="space-y-2">
        <div>
          <label className="text-[10px] uppercase tracking-wide text-[var(--color-text-muted)] mb-1 block">
            Bias Flags
          </label>
          <FlagList flags={qs.top_bias_flags} color="red" />
        </div>
        <div>
          <label className="text-[10px] uppercase tracking-wide text-[var(--color-text-muted)] mb-1 block">
            Ambiguity Flags
          </label>
          <FlagList flags={qs.top_ambiguity_flags} color="amber" />
        </div>
        <div>
          <label className="text-[10px] uppercase tracking-wide text-[var(--color-text-muted)] mb-1 block">
            Cultural Assumptions
          </label>
          <FlagList flags={qs.top_cultural_flags} color="blue" />
        </div>
      </div>

      {/* Sample comprehensions */}
      {qs.sample_comprehensions.length > 0 && (
        <details>
          <summary className="text-xs font-medium text-[var(--color-text-muted)] cursor-pointer select-none flex items-center gap-1">
            <Eye size={12} />
            How respondents interpreted this ({qs.sample_comprehensions.length})
          </summary>
          <div className="mt-2 space-y-1.5 pl-4 border-l-2 border-[var(--color-border)]">
            {qs.sample_comprehensions.map((c, i) => (
              <p key={i} className="text-xs text-[var(--color-text)]">
                &ldquo;{c}&rdquo;
              </p>
            ))}
          </div>
        </details>
      )}

      {/* Suggested improvements — shown by default */}
      {qs.sample_improvements.length > 0 && (
        <div>
          <div className="text-xs font-medium text-[var(--color-text-muted)] flex items-center gap-1 mb-2">
            <MessageSquareWarning size={12} />
            Suggested Improvements
          </div>
          <div className="space-y-1.5 pl-4 border-l-2 border-[var(--color-primary)]/30">
            {qs.sample_improvements.map((imp, i) => (
              <p key={i} className="text-xs text-[var(--color-text)]">
                {imp}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function SurveyResultsView({
  reactions,
  summary,
  questions,
  respondingCount,
  totalPanel,
  isComplete,
  onRestart,
}: SurveyResultsViewProps) {
  return (
    <div className="space-y-6">
      {/* Progress header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold font-[family-name:var(--font-heading)]">
            Survey Pre-Test Results
          </h2>
          <p className="text-sm text-[var(--color-text-muted)]">
            {isComplete
              ? `${reactions.filter((r) => !r.error).length} personas evaluated ${questions.length} question${questions.length > 1 ? "s" : ""}`
              : `${respondingCount} of ${totalPanel} personas evaluating...`}
          </p>
        </div>
        {isComplete && (
          <button
            onClick={onRestart}
            className="px-4 py-2 bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
          >
            New Pre-Test
          </button>
        )}
      </div>

      {/* Progress bar */}
      {!isComplete && (
        <div className="h-2 bg-[var(--color-bg)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--color-primary)] rounded-full transition-all duration-500"
            style={{ width: `${(respondingCount / totalPanel) * 100}%` }}
          />
        </div>
      )}

      {/* Question summary cards */}
      {summary && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-[var(--color-text-muted)]">
              {summary.total_respondents} respondents &middot; {summary.elapsed}s
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {summary.question_summaries.map((qs) => (
              <QuestionCard key={qs.question_index} qs={qs} />
            ))}
          </div>
        </div>
      )}

      {/* Individual reactions (collapsible) */}
      {reactions.length > 0 && (
        <details className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] shadow-sm">
          <summary className="px-4 py-3 text-sm font-medium cursor-pointer select-none flex items-center gap-2">
            <ChevronDown size={14} />
            <Users size={14} />
            Individual Evaluations ({reactions.filter((r) => !r.error).length})
          </summary>
          <div className="px-4 py-3 space-y-4 border-t border-[var(--color-border)] max-h-[600px] overflow-y-auto">
            {reactions
              .filter((r) => !r.error)
              .map((r, i) => (
                <div
                  key={r.persona_id + "-" + i}
                  className="border-b border-[var(--color-border)] pb-4 last:border-0 last:pb-0"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-semibold text-[var(--color-primary)]">
                      {r.age} {r.sex}
                    </span>
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {r.occupation} &middot; {r.city}, {r.province}
                    </span>
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {r.education_level} &middot; {r.cultural_background}
                    </span>
                  </div>

                  <p className="text-xs text-[var(--color-text)] italic mb-2">
                    &ldquo;{r.overall_survey_impression}&rdquo;
                  </p>

                  <div className="space-y-1.5">
                    {r.question_reactions.map((qr, qi) => (
                      <div key={qi} className="flex items-start gap-2 text-xs">
                        <span className="font-semibold text-[var(--color-primary)] w-6 flex-shrink-0">
                          Q{(qr.question_index ?? qi) + 1}
                        </span>
                        <span
                          className={`w-6 flex-shrink-0 font-semibold ${
                            qr.clarity_score >= 4
                              ? "text-emerald-600"
                              : qr.clarity_score >= 3
                                ? "text-amber-600"
                                : "text-red-600"
                          }`}
                        >
                          {qr.clarity_score}/5
                        </span>
                        <span className="text-[var(--color-text)]">{qr.comprehension}</span>
                        {!qr.would_answer_honestly && (
                          <span className="text-red-500 text-[10px] flex-shrink-0 border border-red-200 bg-red-50 px-1.5 py-0.5 rounded" title="This persona feels the question wording pushes them toward a particular answer">leading wording</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        </details>
      )}
    </div>
  );
}
