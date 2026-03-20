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

// ── Word-level diff engine ──────────────────────────────────────────

type DiffToken = { text: string; type: "equal" | "removed" | "added"; group?: number };

function computeWordDiff(oldText: string, newText: string): { removed: DiffToken[]; added: DiffToken[] } {
  const oldWords = oldText.split(/(\s+)/);
  const newWords = newText.split(/(\s+)/);

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
    const MAX_BRIDGE_WORDS = 3;
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
    <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-4 shadow-sm">
      <p className="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wide mb-2">
        {label}
      </p>
      <div className="flex items-end gap-3">
        <div>
          <p className="text-xs text-[var(--color-text-light)]">Before</p>
          <p className="text-lg font-mono font-semibold text-[var(--color-text-muted)]">
            {before.toFixed(1)}
            {unit}
          </p>
        </div>
        <ArrowRight size={16} className="text-[var(--color-text-light)] mb-2" />
        <div>
          <p className="text-xs text-[var(--color-text-light)]">After</p>
          <p
            className={cn(
              "text-lg font-mono font-semibold",
              improved ? "text-emerald-600" : "text-red-500"
            )}
          >
            {after.toFixed(1)}
            {unit}
          </p>
        </div>
        <div
          className={cn(
            "flex items-center gap-0.5 text-sm font-mono font-medium ml-auto mb-1",
            improved ? "text-emerald-600" : "text-red-500"
          )}
        >
          {improved ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {deltaStr}
          {unit}
        </div>
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
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
            <Trophy size={20} className="text-amber-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold font-[family-name:var(--font-heading)]">
              Final Results
            </h2>
            <p className="text-sm text-[var(--color-text-muted)]">
              Before vs. After optimization — same panel, same personas
            </p>
          </div>
        </div>
        <button
          onClick={onRestart}
          className="flex items-center gap-2 px-4 py-2 border border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-surface)] rounded-lg text-sm font-medium transition-colors cursor-pointer"
        >
          <RotateCcw size={16} />
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

      {/* Diff view — Diffchecker style */}
      <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] shadow-sm overflow-hidden">
        {/* Diff header */}
        <div className="grid grid-cols-1 lg:grid-cols-2 border-b border-[var(--color-border)]">
          <div className="flex items-center justify-between px-5 py-3 border-b lg:border-b-0 lg:border-r border-[var(--color-border)] bg-red-50/50">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-400" />
              <span className="text-sm font-semibold text-red-700">Original</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
              <span>Sentiment: <strong className="text-red-500">{round1.avg_sentiment.toFixed(1)}/5</strong></span>
              <span>Relevance: <strong className="text-red-500">{round1.relevance_pct}%</strong></span>
            </div>
          </div>
          <div className="flex items-center justify-between px-5 py-3 bg-emerald-50/50">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-emerald-400" />
              <span className="text-sm font-semibold text-emerald-700">Optimized</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
              <span>Sentiment: <strong className="text-emerald-600">{round2.avg_sentiment.toFixed(1)}/5</strong></span>
              <span>Relevance: <strong className="text-emerald-600">{round2.relevance_pct}%</strong></span>
            </div>
          </div>
        </div>

        {/* Diff body */}
        <div className="grid grid-cols-1 lg:grid-cols-2">
          <div className="px-5 py-4 border-b lg:border-b-0 lg:border-r border-[var(--color-border)] bg-red-50/20">
            <DiffLine tokens={diff.removed} side="removed" />
          </div>
          <div className="px-5 py-4 bg-emerald-50/20">
            <DiffLine tokens={diff.added} side="added" />
          </div>
        </div>

        {/* Change count summary bar */}
        <div className="px-5 py-2.5 border-t border-[var(--color-border)] bg-[var(--color-surface)] flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-sm bg-red-300" />
            {diff.removed.filter(t => t.type === "removed").length} words removed
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-sm bg-emerald-300" />
            {diff.added.filter(t => t.type === "added").length} words added
          </span>
          <span>{totalGroups} change region{totalGroups !== 1 ? "s" : ""}</span>
        </div>
      </div>

      {/* Change annotations — tagged to feedback */}
      {totalGroups > 0 && (
        <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-5 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)] mb-3">
            Change Annotations
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
      <div
        className={cn(
          "rounded-xl border p-5",
          sentimentDelta > 0
            ? "bg-emerald-50 border-emerald-200"
            : sentimentDelta < 0
            ? "bg-red-50 border-red-200"
            : "bg-gray-50 border-gray-200"
        )}
      >
        <div className="flex items-center gap-2 mb-2">
          {sentimentDelta > 0 ? (
            <TrendingUp size={18} className="text-emerald-600" />
          ) : sentimentDelta < 0 ? (
            <TrendingDown size={18} className="text-red-500" />
          ) : (
            <AlertTriangle size={18} className="text-amber-500" />
          )}
          <p className="font-semibold text-sm">
            {sentimentDelta > 0
              ? `Sentiment improved by ${sentimentDelta.toFixed(1)} points (${((sentimentDelta / round1.avg_sentiment) * 100).toFixed(0)}% increase)`
              : sentimentDelta < 0
              ? `Sentiment decreased by ${Math.abs(sentimentDelta).toFixed(1)} points`
              : "Sentiment unchanged between rounds"}
          </p>
        </div>
        <p className="text-sm text-[var(--color-text-muted)]">
          {relevanceDelta !== 0
            ? `Relevance ${relevanceDelta > 0 ? "improved" : "dropped"} from ${round1.relevance_pct}% to ${round2.relevance_pct}% (${relevanceDelta > 0 ? "+" : ""}${relevanceDelta}pp).`
            : `Relevance held steady at ${round1.relevance_pct}%.`}
          {" "}
          {(() => {
            const flagsBefore = round1.top_cultural_flags.length;
            const flagsAfter = round2.top_cultural_flags.length;
            if (flagsAfter < flagsBefore) return `Cultural flags reduced from ${flagsBefore} to ${flagsAfter}.`;
            if (flagsAfter > flagsBefore) return `Cultural flags increased from ${flagsBefore} to ${flagsAfter}.`;
            return flagsBefore === 0 ? "No cultural flags in either round." : `Cultural flags unchanged (${flagsBefore}).`;
          })()}
        </p>
      </div>


      {/* Feedback */}
      {traceId && (
        <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-5 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)] mb-3">
            How was this optimization?
          </p>
          {feedbackSent ? (
            <div className="flex items-center gap-2 text-sm text-emerald-600">
              <Check size={16} />
              <span>
                Feedback recorded: <strong>{feedbackSent}</strong>
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleFeedback("good")}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-emerald-200 text-emerald-700 hover:bg-emerald-50 text-sm font-medium transition-colors cursor-pointer"
              >
                <ThumbsUp size={16} />
                Good
              </button>
              <button
                onClick={() => handleFeedback("partial")}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-amber-200 text-amber-700 hover:bg-amber-50 text-sm font-medium transition-colors cursor-pointer"
              >
                <Minus size={16} />
                Partial
              </button>
              <button
                onClick={() => handleFeedback("bad")}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-red-200 text-red-700 hover:bg-red-50 text-sm font-medium transition-colors cursor-pointer"
              >
                <ThumbsDown size={16} />
                Bad
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
