"use client";

import { useState, useEffect } from "react";
import { Send, SlidersHorizontal, X } from "lucide-react";
import type { PanelFilters } from "@/lib/types";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const EXAMPLE_STATEMENTS = [
  "Canada is a land of opportunity where hard work leads to prosperity for all.",
  "Our new banking app makes managing your money effortless — built for modern Canadians.",
  "Join thousands of Canadians who trust our healthcare platform for faster, smarter care.",
  "Experience the Canadian dream with our new line of sustainable outdoor gear.",
];

/** Shape returned by /api/panel-options (subset we use) */
interface PanelOptions {
  total_personas: number;
  age_range: { min: number; max: number } | null;
  province: string[];
  sex: string[];
  income_bracket: string[];
  political_leaning: string[];
  languages: string[];
  [key: string]: unknown; // backend sends more fields — we ignore them
}

/** Filter config for rendering — curated for marketing relevance */
const FILTER_FIELDS: { key: keyof PanelFilters; label: string; optionsKey: keyof PanelOptions }[] = [
  { key: "province", label: "Province", optionsKey: "province" },
  { key: "sex", label: "Sex", optionsKey: "sex" },
  { key: "income_bracket", label: "Income Bracket", optionsKey: "income_bracket" },
  { key: "languages", label: "Language", optionsKey: "languages" },
  { key: "political_leaning", label: "Political Leaning", optionsKey: "political_leaning" },
];

const EXAMPLE_BRIEFS = [
  "Young parents in suburban Ontario, worried about screen time, household income $60-100K",
  "Retirees considering downsizing from houses to condos in BC and Alberta",
  "Gen Z urban professionals in Montreal and Toronto, environmentally conscious, $40-80K",
  "Rural Canadians across the Prairies, concerned about cost of living and healthcare access",
];

interface InputStepProps {
  onStart: (message: string, audienceBrief: string, filters: PanelFilters) => void;
}

export function InputStep({ onStart }: InputStepProps) {
  const [message, setMessage] = useState("");
  const [audienceBrief, setAudienceBrief] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<PanelFilters>({
    panel_size: 12,
  });
  const [options, setOptions] = useState<PanelOptions | null>(null);

  // Fetch filter options from backend
  useEffect(() => {
    fetch(`${BACKEND_URL}/api/panel-options`)
      .then((r) => r.json())
      .then((data) => setOptions(data))
      .catch(() => {}); // silently fail — filters just won't show options
  }, []);

  const handleSubmit = () => {
    if (!message.trim()) return;
    onStart(message.trim(), audienceBrief.trim(), filters);
  };

  // Count active filters (age_range counts if changed from full range)
  const activeFilterCount = Object.entries(filters).filter(([k, v]) => {
    if (k === "panel_size") return false;
    if (v === undefined) return false;
    if (k === "age_range" && options?.age_range) {
      const [min, max] = v as [number, number];
      return min !== options.age_range.min || max !== options.age_range.max;
    }
    return !Array.isArray(v) || v.length > 0;
  }).length;

  const clearFilters = () => setFilters({ panel_size: filters.panel_size });

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div className="text-center space-y-1">
        <h2 className="text-lg font-semibold">
          Test your message with a Canadian panel
        </h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Describe your audience, paste your copy, and get reactions from AI personas.
        </p>
      </div>

      <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)]">
        {/* Audience Brief */}
        <div className="px-4 pt-4 pb-2">
          <label className="text-xs font-medium text-[var(--color-text-muted)] mb-1.5 block">
            Target Audience
          </label>
          <textarea
            value={audienceBrief}
            onChange={(e) => setAudienceBrief(e.target.value)}
            placeholder="e.g. Young parents in suburban Ontario, household income $60-100K"
            rows={2}
            className="w-full px-3 py-2 bg-[var(--color-surface)] rounded-lg text-[var(--color-text)] placeholder:text-[var(--color-text-light)] focus:outline-none resize-none text-sm"
          />
          <div className="flex flex-wrap gap-1 mt-1.5">
            {EXAMPLE_BRIEFS.map((b, i) => (
              <button
                key={i}
                onClick={() => setAudienceBrief(b)}
                className="text-[10px] px-2 py-0.5 rounded-full text-[var(--color-text-light)] hover:text-[var(--color-text-muted)] transition-colors cursor-pointer"
              >
                {b.slice(0, 40)}...
              </button>
            ))}
          </div>
        </div>

        <div className="border-t border-[var(--color-border)] mx-4" />

        {/* Message input */}
        <div className="px-4 pt-3 pb-2">
          <label className="text-xs font-medium text-[var(--color-text-muted)] mb-1.5 block">
            Content to Test
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter your marketing message or statement..."
            rows={4}
            className="w-full px-3 py-2 bg-[var(--color-surface)] rounded-lg text-[var(--color-text)] placeholder:text-[var(--color-text-light)] focus:outline-none resize-none text-sm"
          />
          <div className="flex flex-wrap gap-1 mt-1.5">
            {EXAMPLE_STATEMENTS.map((s, i) => (
              <button
                key={i}
                onClick={() => setMessage(s)}
                className="text-[10px] px-2 py-0.5 rounded-full text-[var(--color-text-light)] hover:text-[var(--color-text-muted)] transition-colors cursor-pointer"
              >
                {s.slice(0, 45)}...
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--color-border)]">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors cursor-pointer"
          >
            <SlidersHorizontal size={14} />
            Filters
            {activeFilterCount > 0 && (
              <span className="ml-0.5 px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-[var(--color-surface)] text-[var(--color-text)]">
                {activeFilterCount}
              </span>
            )}
          </button>
          <button
            onClick={handleSubmit}
            disabled={!message.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] disabled:opacity-30 disabled:cursor-not-allowed text-white rounded-lg font-medium text-sm transition-colors cursor-pointer"
          >
            <Send size={14} />
            Run
          </button>
        </div>
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex-1 max-w-xs">
              <label className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">
                Panel Size: {filters.panel_size}
              </label>
              <input
                type="range"
                min={6}
                max={20}
                value={filters.panel_size}
                onChange={(e) =>
                  setFilters({ ...filters, panel_size: parseInt(e.target.value) })
                }
                className="w-full accent-[var(--color-primary)]"
              />
            </div>
            {activeFilterCount > 0 && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 text-xs text-[var(--color-text-muted)] hover:text-red-500 transition-colors cursor-pointer"
              >
                <X size={12} />
                Clear
              </button>
            )}
          </div>

          {options?.age_range && (
            <div>
              <label className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">
                Age Range
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={options.age_range.min}
                  max={options.age_range.max}
                  value={filters.age_range?.[0] ?? options.age_range.min}
                  onChange={(e) => {
                    const min = Math.max(options.age_range!.min, Math.min(parseInt(e.target.value) || options.age_range!.min, filters.age_range?.[1] ?? options.age_range!.max));
                    setFilters({ ...filters, age_range: [min, filters.age_range?.[1] ?? options.age_range!.max] });
                  }}
                  className="w-14 px-2 py-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] text-xs text-center"
                />
                <span className="text-xs text-[var(--color-text-muted)]">to</span>
                <input
                  type="number"
                  min={options.age_range.min}
                  max={options.age_range.max}
                  value={filters.age_range?.[1] ?? options.age_range.max}
                  onChange={(e) => {
                    const max = Math.min(options.age_range!.max, Math.max(parseInt(e.target.value) || options.age_range!.max, filters.age_range?.[0] ?? options.age_range!.min));
                    setFilters({ ...filters, age_range: [filters.age_range?.[0] ?? options.age_range!.min, max] });
                  }}
                  className="w-14 px-2 py-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] text-xs text-center"
                />
              </div>
            </div>
          )}

          {options && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {FILTER_FIELDS.map(({ key, label, optionsKey }) => {
                const fieldOptions = options[optionsKey];
                if (!Array.isArray(fieldOptions) || fieldOptions.length === 0) return null;
                const currentValue = (filters[key] as string[] | undefined) ?? [];
                return (
                  <div key={key}>
                    <label className="block text-xs text-[var(--color-text-muted)] mb-0.5">
                      {label}
                    </label>
                    <select
                      value={currentValue[0] || ""}
                      onChange={(e) => {
                        const val = e.target.value;
                        setFilters({ ...filters, [key]: val ? [val] : undefined });
                      }}
                      className="w-full px-2 py-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] text-xs"
                    >
                      <option value="">All</option>
                      {(fieldOptions as string[]).map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  </div>
                );
              })}
            </div>
          )}

          {!options && (
            <p className="text-xs text-[var(--color-text-muted)]">Loading options...</p>
          )}
        </div>
      )}
    </div>
  );
}
