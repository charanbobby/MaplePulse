"use client";

import { useState, useMemo } from "react";
import {
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Trophy,
  AlertTriangle,
  RotateCcw,
  ThumbsUp,
  ThumbsDown,
  Minus,
  Check,
} from "lucide-react";
import type { AggregatedResults, OptimizedMessage } from "@/lib/types";
import { cn } from "@/lib/cn";
import { submitFeedback } from "@/lib/api";
import { EvalVote } from "./eval-vote";

// ── Word-level diff engine ──────────────────────────────────────────

type DiffToken = { text: string; type: "equal" | "removed" | "added"; group?: number };

function normalizeQuotes(text: string): string {
  return text
    .replace(/[\u2018\u2019\u2032]/g, "'")   // curly single quotes → straight
    .replace(/[\u201C\u201D\u2033]/g, '"');   // curly double quotes → straight
}

function computeWordDiff(oldText: string, newText: string): { removed: DiffToken[]; added: DiffToken[] } {
  const oldWords = normalizeQuotes(oldText).split(/(\s+)/);
  const newWords = normalizeQuotes(newText).split(/(\s+)/);

  // LCS table
  const m = oldWords.length;
  const n = newWords.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldWords[i - 1] === newWords[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack to build diff
  const removed: DiffToken[] = [];
  const added: DiffToken[] = [];
  let i = m, j = n;

  const removedRev: DiffToken[] = [];
  const addedRev: DiffToken[] = [];

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldWords[i - 1] === newWords[j - 1]) {
      removedRev.push({ text: oldWords[i - 1], type: "equal" });
      addedRev.push({ text: newWords[j - 1], type: "equal" });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      addedRev.push({ text: newWords[j - 1], type: "added" });
      j--;
    } else {
      removedRev.push({ text: oldWords[i - 1], type: "removed" });
      i--;
    }
  }

  removedRev.reverse();
  addedRev.reverse();

  // Assign group numbers, then merge groups separated by short equal bridges
  function assignAndMergeGroups(tokens: DiffToken[], changeType: "removed" | "added"): DiffToken[] {
    // First pass: assign raw group numbers
    let groupNum = 0;
    let inGroup = false;
    for (const token of tokens) {
      if (token.type === changeType) {
        if (!inGroup) { groupNum++; inGroup = true; }
        token.group = groupNum;
      } else {
        inGroup = false;
      }
    }

    // Second pass: merge adjacent groups separated by ≤ MAX_BRIDGE_WORDS real words
    // This prevents fragmentation when LCS misaligns common short words
    const MAX_BRIDGE_WORDS = 6;
    let merged = true;
    while (merged) {
      merged = false;
      const groups = new Set(tokens.filter(t => t.group != null).map(t => t.group!));
      const sortedGroups = Array.from(groups).sort((a, b) => a - b);

      for (let gi = 0; gi < sortedGroups.length - 1; gi++) {
        const curGroup = sortedGroups[gi];
        const nextGroup = sortedGroups[gi + 1];

        const lastOfCur = tokens.findLastIndex(t => t.group === curGroup);
        const firstOfNext = tokens.findIndex((t, idx) => idx > lastOfCur && t.group === nextGroup);

        if (lastOfCur < 0 || firstOfNext < 0) continue;

        const bridge = tokens.slice(lastOfCur + 1, firstOfNext);
        const bridgeWordCount = bridge.filter(t => t.text.trim().length > 0).length;

        if (bridgeWordCount <= MAX_BRIDGE_WORDS) {
          // Merge: absorb bridge into current group, relabel next → current
          for (const t of bridge) {
            t.type = changeType;
            t.group = curGroup;
          }
          for (const t of tokens) {
            if (t.group === nextGroup) t.group = curGroup;
          }
          merged = true;
          break;
        }
      }
    }

    // Renumber groups sequentially
    const uniqueGroups = Array.from(new Set(tokens.filter(t => t.group != null).map(t => t.group!)));
    uniqueGroups.sort((a, b) => {
      const ai = tokens.findIndex(t => t.group === a);
      const bi = tokens.findIndex(t => t.group === b);
      return ai - bi;
    });
    const renumber = new Map(uniqueGroups.map((g, i) => [g, i + 1]));
    for (const t of tokens) {
      if (t.group != null) t.group = renumber.get(t.group)!;
    }

    return tokens;
  }

  const removedResult = assignAndMergeGroups([...removedRev], "removed");
  const addedResult = assignAndMergeGroups([...addedRev], "added");

  return { removed: removedResult, added: addedResult };
}

function getChangeGroupCount(tokens: DiffToken[]): number {
  const groups = new Set(tokens.filter(t => t.group != null).map(t => t.group));
  return groups.size;
}

function DiffLine({ tokens, side }: { tokens: DiffToken[]; side: "removed" | "added" }) {
  const isRemoved = side === "removed";
  return (
    <p className="text-sm leading-relaxed font-mono whitespace-pre-wrap">
      {tokens.map((token, i) => {
        if (token.type === "equal") {
          return <span key={i}>{token.text}</span>;
        }
        const highlight = isRemoved
          ? "bg-red-200 text-red-900 rounded-sm px-0.5"
          : "bg-emerald-200 text-emerald-900 rounded-sm px-0.5";
        return (
          <span key={i} className="relative inline">
            <span className={highlight}>{token.text}</span>
          </span>
        );
      })}
    </p>
  );
}

function matchChangesToGroups(
  removedTokens: DiffToken[],
  addedTokens: DiffToken[],
  changesMade: string[],
): Map<number, string[]> {
  // Build word sets for each change group (combined removed+added)
  const groupWordSets = new Map<number, Set<string>>();
  const maxGroup = Math.max(getChangeGroupCount(removedTokens), getChangeGroupCount(addedTokens));

  for (let g = 1; g <= maxGroup; g++) {
    const words = new Set<string>();
    for (const t of removedTokens) {
      if (t.group === g) {
        const w = t.text.trim().toLowerCase().replace(/[^a-z0-9]/g, "");
        if (w.length > 1) words.add(w);
      }
    }
    for (const t of addedTokens) {
      if (t.group === g) {
        const w = t.text.trim().toLowerCase().replace(/[^a-z0-9]/g, "");
        if (w.length > 1) words.add(w);
      }
    }
    groupWordSets.set(g, words);
  }

  // Score each (group, change) pair
  const stopWords = new Set(["the", "to", "of", "in", "and", "or", "is", "it", "for", "with", "this", "that", "from", "was", "are", "be", "an", "as", "on", "by", "at", "not", "but", "its", "has", "had", "all", "can", "will", "one", "our", "out", "been", "have", "each", "make", "like", "just"]);

  const scoreMatrix: { group: number; changeIdx: number; score: number }[] = [];

  for (const [groupNum, groupWords] of groupWordSets) {
    changesMade.forEach((change, idx) => {
      const quotedPhrases = change.match(/'([^']+)'/g)?.map(q => q.replace(/'/g, "").toLowerCase()) || [];
      const quotedWords = new Set(quotedPhrases.flatMap(p => p.split(/\s+/).map(w => w.replace(/[^a-z0-9]/g, "")).filter(w => w.length > 1)));

      let score = 0;
      for (const qw of quotedWords) {
        if (groupWords.has(qw)) score += 3;
      }

      const allChangeWords = change.toLowerCase().split(/\s+/).map(w => w.replace(/[^a-z0-9]/g, "")).filter(w => w.length > 2 && !stopWords.has(w));
      for (const cw of allChangeWords) {
        if (!quotedWords.has(cw) && groupWords.has(cw)) score += 1;
      }

      if (score > 0) scoreMatrix.push({ group: groupNum, changeIdx: idx, score });
    });
  }

  // Allow multiple changes per group: assign each change to its best-scoring group
  scoreMatrix.sort((a, b) => b.score - a.score);
  const groupToChanges = new Map<number, string[]>();
  const usedChanges = new Set<number>();

  for (const { group, changeIdx, score } of scoreMatrix) {
    if (usedChanges.has(changeIdx)) continue;
    if (score < 2) continue;
    const existing = groupToChanges.get(group) || [];
    existing.push(changesMade[changeIdx]);
    groupToChanges.set(group, existing);
    usedChanges.add(changeIdx);
  }

  // Remaining unmatched changes go to the group with the most changes (likely the biggest diff region)
  // or if no groups matched at all, to group 1
  const unmatchedChanges = changesMade.filter((_, i) => !usedChanges.has(i));
  if (unmatchedChanges.length > 0 && maxGroup > 0) {
    // Find the largest group (most tokens)
    let largestGroup = 1;
    let largestSize = 0;
    for (let g = 1; g <= maxGroup; g++) {
      const size = (groupWordSets.get(g)?.size || 0);
      if (size > largestSize) { largestSize = size; largestGroup = g; }
    }
    const existing = groupToChanges.get(largestGroup) || [];
    existing.push(...unmatchedChanges);
    groupToChanges.set(largestGroup, existing);
  }

  return groupToChanges;
}

function DeltaCard({
  label,
  before,
  after,
  unit,
  higherIsBetter,
}: {
  label: string;
  before: number;
  after: number;
  unit: string;
  higherIsBetter: boolean;
}) {
  const delta = after - before;
  const improved = higherIsBetter ? delta > 0 : delta < 0;
  const deltaStr = delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1);

  return (
    <div className="bg-[var(--color-bg-card)] rounded-lg border border-[var(--color-border)] p-3">
      <p className="text-xs text-[var(--color-text-muted)] mb-1">{label}</p>
      <div className="flex items-baseline gap-2">
        <span className="text-[var(--color-text-light)] font-mono text-sm">{before.toFixed(1)}{unit}</span>
        <ArrowRight size={12} className="text-[var(--color-text-light)]" />
        <span className={cn("font-mono text-lg font-semibold", improved ? "text-emerald-600" : "text-red-500")}>
          {after.toFixed(1)}{unit}
        </span>
        <span className={cn("text-xs font-mono ml-auto", improved ? "text-emerald-600" : "text-red-500")}>
          {deltaStr}{unit}
        </span>
      </div>
    </div>
  );
}

interface FinalComparisonProps {
  originalMessage: string;
  optimized: OptimizedMessage;
  round1: AggregatedResults;
  round2: AggregatedResults;
  traceId: string | null;
  onRestart: () => void;
}

export function FinalComparison({
  originalMessage,
  optimized,
  round1,
  round2,
  traceId,
  onRestart,
}: FinalComparisonProps) {
  const sentimentDelta = round2.avg_sentiment - round1.avg_sentiment;
  const relevanceDelta = round2.relevance_pct - round1.relevance_pct;

  const [feedbackSent, setFeedbackSent] = useState<"good" | "bad" | "partial" | null>(null);

  // Compute word-level diff
  const diff = useMemo(
    () => computeWordDiff(originalMessage, optimized.improved_message),
    [originalMessage, optimized.improved_message]
  );

  // Match change groups to changes_made feedback
  const groupAnnotations = useMemo(
    () => matchChangesToGroups(diff.removed, diff.added, optimized.changes_made),
    [diff, optimized.changes_made]
  );

  const totalGroups = Math.max(getChangeGroupCount(diff.removed), getChangeGroupCount(diff.added));

  const handleFeedback = async (value: "good" | "bad" | "partial") => {
    if (!traceId) return;
    setFeedbackSent(value);
    await submitFeedback(traceId, value);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold">Final Results</h2>
          <p className="text-xs text-[var(--color-text-muted)]">
            Before vs. after optimization
          </p>
        </div>
        <button
          onClick={onRestart}
          className="flex items-center gap-2 px-3 py-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-text)] rounded-lg text-sm font-medium transition-colors cursor-pointer"
        >
          <RotateCcw size={14} />
          New Test
        </button>
      </div>

      {/* Delta cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <DeltaCard
          label="Avg Sentiment"
          before={round1.avg_sentiment}
          after={round2.avg_sentiment}
          unit=""
          higherIsBetter
        />
        <DeltaCard
          label="Relevance"
          before={round1.relevance_pct}
          after={round2.relevance_pct}
          unit="%"
          higherIsBetter
        />
        <DeltaCard
          label="Natural Tone"
          before={round1.tone_distribution.natural || 0}
          after={round2.tone_distribution.natural || 0}
          unit="%"
          higherIsBetter
        />
        <DeltaCard
          label="Awkward Tone"
          before={round1.tone_distribution.awkward || 0}
          after={round2.tone_distribution.awkward || 0}
          unit="%"
          higherIsBetter={false}
        />
      </div>

      {/* Diff view */}
      <div className="bg-[var(--color-bg-card)] rounded-lg border border-[var(--color-border)] overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-2 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-2 px-4 py-2 border-b lg:border-b-0 lg:border-r border-[var(--color-border)]">
            <div className="w-2 h-2 rounded-full bg-red-400" />
            <span className="text-xs font-medium text-[var(--color-text-muted)]">Original</span>
          </div>
          <div className="flex items-center gap-2 px-4 py-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400" />
            <span className="text-xs font-medium text-[var(--color-text-muted)]">Optimized</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2">
          <div className="px-4 py-3 border-b lg:border-b-0 lg:border-r border-[var(--color-border)]">
            <DiffLine tokens={diff.removed} side="removed" />
          </div>
          <div className="px-4 py-3">
            <DiffLine tokens={diff.added} side="added" />
          </div>
        </div>
      </div>

      {/* Change annotations */}
      {totalGroups > 0 && (
        <div className="bg-[var(--color-bg-card)] rounded-lg border border-[var(--color-border)] p-4">
          <p className="text-xs font-medium text-[var(--color-text-muted)] mb-2">
            Changes
          </p>
          <div className="space-y-2.5">
            {Array.from({ length: totalGroups }, (_, i) => i + 1).map((groupNum) => {
              const removedWords = diff.removed
                .filter(t => t.group === groupNum)
                .map(t => t.text.trim())
                .filter(Boolean)
                .join(" ");
              const addedWords = diff.added
                .filter(t => t.group === groupNum)
                .map(t => t.text.trim())
                .filter(Boolean)
                .join(" ");
              const annotations = groupAnnotations.get(groupNum) || [];

              return (
                <div key={groupNum} className="flex items-start gap-3 text-sm">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[var(--color-primary)] text-white text-xs font-bold flex items-center justify-center mt-0.5">
                    {groupNum}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      {removedWords && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-red-100 text-red-700 text-xs font-mono">
                          <span className="font-bold">&minus;</span> {removedWords}
                        </span>
                      )}
                      {removedWords && addedWords && (
                        <ArrowRight size={12} className="text-[var(--color-text-light)]" />
                      )}
                      {addedWords && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 text-xs font-mono">
                          <span className="font-bold">+</span> {addedWords}
                        </span>
                      )}
                    </div>
                    {annotations.map((annotation, ai) => (
                      <p key={ai} className="text-xs text-[var(--color-text-muted)] italic mt-1">
                        {annotation}
                      </p>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Improvement summary */}
      {(() => {
        const naturalBefore = round1.tone_distribution.natural || 0;
        const naturalAfter = round2.tone_distribution.natural || 0;
        const naturalDelta = naturalAfter - naturalBefore;
        const awkwardBefore = round1.tone_distribution.awkward || 0;
        const awkwardAfter = round2.tone_distribution.awkward || 0;
        const awkwardDelta = awkwardAfter - awkwardBefore;
        const flagsBefore = round1.top_cultural_flags.length;
        const flagsAfter = round2.top_cultural_flags.length;

        // Collect wins and losses
        const wins: string[] = [];
        const losses: string[] = [];
        const neutral: string[] = [];

        // Sentiment
        if (sentimentDelta > 0.05) wins.push(`Sentiment improved by ${sentimentDelta.toFixed(1)} points`);
        else if (sentimentDelta < -0.05) losses.push(`Sentiment dipped by ${Math.abs(sentimentDelta).toFixed(1)} points`);
        else neutral.push("Sentiment held steady");

        // Relevance
        if (relevanceDelta > 0) wins.push(`Relevance up ${relevanceDelta}pp to ${round2.relevance_pct}%`);
        else if (relevanceDelta < 0) losses.push(`Relevance down ${Math.abs(relevanceDelta)}pp to ${round2.relevance_pct}%`);
        else neutral.push(`Relevance steady at ${round1.relevance_pct}%`);

        // Natural tone
        if (naturalDelta > 0) wins.push(`Natural tone up ${naturalDelta.toFixed(0)}pp to ${naturalAfter.toFixed(0)}%`);
        else if (naturalDelta < 0) losses.push(`Natural tone down ${Math.abs(naturalDelta).toFixed(0)}pp`);

        // Awkward tone
        if (awkwardDelta < 0) wins.push(`Awkward tone reduced from ${awkwardBefore.toFixed(0)}% to ${awkwardAfter.toFixed(0)}%`);
        else if (awkwardDelta > 0) losses.push(`Awkward tone increased to ${awkwardAfter.toFixed(0)}%`);
        else if (awkwardBefore === 0 && awkwardAfter === 0) {} // skip if both zero

        // Cultural flags
        if (flagsAfter < flagsBefore) wins.push(`Cultural flags reduced from ${flagsBefore} to ${flagsAfter}`);
        else if (flagsAfter > flagsBefore) losses.push(`Cultural flags increased from ${flagsBefore} to ${flagsAfter}`);
        else if (flagsBefore === 0) {} // skip if none

        // Overall verdict
        const overallPositive = wins.length > losses.length;
        const allNeutral = wins.length === 0 && losses.length === 0;

        return (
          <div
            className={cn(
              "rounded-xl border p-5",
              overallPositive
                ? "bg-emerald-50 border-emerald-200"
                : allNeutral
                ? "bg-gray-50 border-gray-200"
                : wins.length === losses.length
                ? "bg-amber-50 border-amber-200"
                : "bg-red-50 border-red-200"
            )}
          >
            <div className="flex items-center gap-2 mb-2">
              {overallPositive ? (
                <TrendingUp size={18} className="text-emerald-600" />
              ) : allNeutral ? (
                <Minus size={18} className="text-gray-500" />
              ) : wins.length === losses.length ? (
                <AlertTriangle size={18} className="text-amber-500" />
              ) : (
                <TrendingDown size={18} className="text-red-500" />
              )}
              <p className="font-semibold text-sm">
                {overallPositive
                  ? `Optimization improved ${wins.length} metric${wins.length !== 1 ? "s" : ""}`
                  : allNeutral
                  ? "No significant changes between rounds"
                  : wins.length === losses.length
                  ? "Mixed results — some metrics improved, others declined"
                  : `${losses.length} metric${losses.length !== 1 ? "s" : ""} declined`}
              </p>
            </div>
            {wins.length > 0 && (
              <div className="flex flex-wrap gap-x-1 text-sm text-emerald-700 mb-1">
                <span className="font-medium">Improved:</span>
                {wins.map((w, i) => (
                  <span key={i}>
                    {w}{i < wins.length - 1 ? "." : "."}
                  </span>
                ))}
              </div>
            )}
            {losses.length > 0 && (
              <div className="flex flex-wrap gap-x-1 text-sm text-red-600 mb-1">
                <span className="font-medium">Declined:</span>
                {losses.map((l, i) => (
                  <span key={i}>
                    {l}{i < losses.length - 1 ? "." : "."}
                  </span>
                ))}
              </div>
            )}
            {neutral.length > 0 && (
              <div className="flex flex-wrap gap-x-1 text-sm text-[var(--color-text-muted)]">
                <span className="font-medium">Unchanged:</span>
                {neutral.map((n, i) => (
                  <span key={i}>
                    {n}{i < neutral.length - 1 ? "." : "."}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })()}


      {/* Eval voting */}
      <div className="flex items-center gap-6 pt-1 border-t border-[var(--color-border)]">
        <EvalVote
          evalType="brand_voice"
          label="Brand voice preserved?"
          traceId={traceId || undefined}
          meta={{ original_message: originalMessage, optimized_message: optimized.improved_message }}
        />
        <EvalVote
          evalType="optimization_faithfulness"
          label="No hallucinated claims?"
          traceId={traceId || undefined}
          meta={{ original_message: originalMessage, optimized_message: optimized.improved_message, changes_made: optimized.changes_made }}
        />
      </div>

      {/* Feedback */}
      {traceId && (
        <div className="flex items-center gap-3 pt-2">
          <span className="text-xs text-[var(--color-text-muted)]">Rate this result:</span>
          {feedbackSent ? (
            <span className="text-xs text-emerald-600 flex items-center gap-1">
              <Check size={12} /> {feedbackSent}
            </span>
          ) : (
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => handleFeedback("good")}
                className="p-1.5 rounded-md text-[var(--color-text-light)] hover:text-emerald-600 hover:bg-emerald-50 transition-colors cursor-pointer"
              >
                <ThumbsUp size={14} />
              </button>
              <button
                onClick={() => handleFeedback("partial")}
                className="p-1.5 rounded-md text-[var(--color-text-light)] hover:text-amber-600 hover:bg-amber-50 transition-colors cursor-pointer"
              >
                <Minus size={14} />
              </button>
              <button
                onClick={() => handleFeedback("bad")}
                className="p-1.5 rounded-md text-[var(--color-text-light)] hover:text-red-500 hover:bg-red-50 transition-colors cursor-pointer"
              >
                <ThumbsDown size={14} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
