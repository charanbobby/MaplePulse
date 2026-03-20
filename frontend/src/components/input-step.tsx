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

interface InputStepProps {
  onSubmit: (message: string, filters: PanelFilters) => void;
}

export function InputStep({ onSubmit }: InputStepProps) {
  const [message, setMessage] = useState("");
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
    onSubmit(message.trim(), filters);
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
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-semibold font-[family-name:var(--font-heading)]">
          Test Your Message
        </h2>
        <p className="text-[var(--color-text-muted)]">
          Enter a marketing statement, policy message, or product pitch. Our
          panel of AI-powered Canadian personas will react to it.
        </p>
      </div>

      {/* Message input */}
      <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] shadow-sm">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Enter your marketing message or statement to test..."
          rows={4}
          className="w-full px-4 py-3 rounded-t-xl bg-transparent text-[var(--color-text)] placeholder:text-[var(--color-text-light)] focus:outline-none resize-none text-base"
        />
        <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--color-border)]">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors cursor-pointer"
          >
            <SlidersHorizontal size={16} />
            Panel Filters
            {activeFilterCount > 0 && (
              <span className="ml-1 px-1.5 py-0.5 text-[10px] font-semibold rounded-full bg-[var(--color-primary)] text-white">
                {activeFilterCount}
              </span>
            )}
          </button>
          <button
            onClick={handleSubmit}
            disabled={!message.trim()}
            className="flex items-center gap-2 px-5 py-2 bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg font-medium text-sm transition-colors cursor-pointer"
          >
            <Send size={16} />
            Run Focus Group
          </button>
        </div>
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-4 space-y-4 shadow-sm">
          {/* Panel size + clear */}
          <div className="flex items-center justify-between">
            <div className="flex-1 max-w-xs">
              <label className="block text-sm font-medium mb-1.5">
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
              <div className="flex justify-between text-xs text-[var(--color-text-muted)]">
                <span>6</span>
                <span>20</span>
              </div>
            </div>
            {activeFilterCount > 0 && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 text-xs text-[var(--color-text-muted)] hover:text-red-500 transition-colors cursor-pointer"
              >
                <X size={12} />
                Clear all filters
              </button>
            )}
          </div>

          {/* Age range */}
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
                  className="w-16 px-2 py-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] text-xs text-center"
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
                  className="w-16 px-2 py-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] text-xs text-center"
                />
              </div>
            </div>
          )}

          {/* Filter dropdowns */}
          {options && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {FILTER_FIELDS.map(({ key, label, optionsKey }) => {
                const fieldOptions = options[optionsKey];
                if (!Array.isArray(fieldOptions) || fieldOptions.length === 0) return null;
                const currentValue = (filters[key] as string[] | undefined) ?? [];

                return (
                  <div key={key}>
                    <label className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">
                      {label}
                    </label>
                    <select
                      value={currentValue[0] || ""}
                      onChange={(e) => {
                        const val = e.target.value;
                        setFilters({
                          ...filters,
                          [key]: val ? [val] : undefined,
                        });
                      }}
                      className="w-full px-2 py-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] text-xs"
                    >
                      <option value="">All</option>
                      {(fieldOptions as string[]).map((opt) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </select>
                  </div>
                );
              })}
            </div>
          )}

          {!options && (
            <p className="text-xs text-[var(--color-text-muted)]">Loading filter options...</p>
          )}
        </div>
      )}

      {/* Example prompts */}
      <div className="space-y-2">
        <p className="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wide">
          Try an example
        </p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_STATEMENTS.map((s, i) => (
            <button
              key={i}
              onClick={() => setMessage(s)}
              className="text-xs px-3 py-1.5 rounded-full border border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] transition-colors cursor-pointer"
            >
              {s.slice(0, 60)}...
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
