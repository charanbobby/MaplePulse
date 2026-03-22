"use client";

import { useState, useEffect } from "react";
import { Plus, Trash2, SlidersHorizontal, X, Send } from "lucide-react";
import type { PanelFilters } from "@/lib/types";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const EXAMPLE_AB_TESTS = [
  {
    label: "Banking app taglines",
    variants: [
      "Your money, your way. Banking that fits your life.",
      "Smart banking for modern Canadians. Join thousands who've switched.",
    ],
    brief: "Young professionals in Toronto and Vancouver, $60-100K",
  },
  {
    label: "Sustainable outdoor gear",
    variants: [
      "Adventure awaits — gear up with Canada's most sustainable outdoor brand.",
      "Built tough. Built green. Outdoor gear that respects the land.",
    ],
    brief: "Outdoor enthusiasts across BC and Alberta, environmentally conscious",
  },
  {
    label: "Healthcare platform (3 variants)",
    variants: [
      "Faster care starts here. Join Canada's #1 digital health platform.",
      "Your health, on your schedule. Virtual care when you need it most.",
      "Skip the wait. See a doctor online in minutes, not months.",
    ],
    brief: "Canadians 30-60, concerned about healthcare access",
  },
];

interface PanelOptions {
  total_personas: number;
  age_range: { min: number; max: number } | null;
  province: string[];
  sex: string[];
  income_bracket: string[];
  political_leaning: string[];
  languages: string[];
  [key: string]: unknown;
}

const FILTER_FIELDS: { key: keyof PanelFilters; label: string; optionsKey: keyof PanelOptions }[] = [
  { key: "province", label: "Province", optionsKey: "province" },
  { key: "sex", label: "Sex", optionsKey: "sex" },
  { key: "income_bracket", label: "Income Bracket", optionsKey: "income_bracket" },
  { key: "languages", label: "Language", optionsKey: "languages" },
  { key: "political_leaning", label: "Political Leaning", optionsKey: "political_leaning" },
];

interface ABTestInputProps {
  onStart: (variants: string[], audienceBrief: string, filters: PanelFilters) => void;
}

export function ABTestInput({ onStart }: ABTestInputProps) {
  const [variants, setVariants] = useState<string[]>(["", ""]);
  const [audienceBrief, setAudienceBrief] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<PanelFilters>({ panel_size: 12 });
  const [options, setOptions] = useState<PanelOptions | null>(null);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/panel-options`)
      .then((r) => r.json())
      .then((data) => setOptions(data))
      .catch(() => {});
  }, []);

  const updateVariant = (index: number, value: string) => {
    const updated = [...variants];
    updated[index] = value;
    setVariants(updated);
  };

  const addVariant = () => {
    if (variants.length < 5) setVariants([...variants, ""]);
  };

  const removeVariant = (index: number) => {
    if (variants.length > 2) setVariants(variants.filter((_, i) => i !== index));
  };

  const handleSubmit = () => {
    const nonEmpty = variants.filter((v) => v.trim());
    if (nonEmpty.length < 2) return;
    onStart(nonEmpty, audienceBrief.trim(), filters);
  };

  const loadExample = (example: typeof EXAMPLE_AB_TESTS[0]) => {
    setVariants(example.variants);
    setAudienceBrief(example.brief);
  };

  const canSubmit = variants.filter((v) => v.trim()).length >= 2;

  const activeFilterCount = Object.entries(filters).filter(([k, v]) => {
    if (k === "panel_size") return false;
    if (v === undefined) return false;
    return !Array.isArray(v) || v.length > 0;
  }).length;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="text-center space-y-1">
        <h2 className="text-lg font-semibold">
          A/B Copy Test
        </h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Enter 2-5 copy variants. Each persona will react to all variants and pick their favourite.
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
            placeholder="e.g. Young professionals in Toronto and Vancouver, $60-100K"
            rows={2}
            className="w-full px-3 py-2 bg-[var(--color-surface)] rounded-lg text-[var(--color-text)] placeholder:text-[var(--color-text-light)] focus:outline-none resize-none text-sm"
          />
        </div>

        <div className="border-t border-[var(--color-border)] mx-4" />

        {/* Copy Variants */}
        <div className="px-4 pt-3 pb-2 space-y-2">
          {variants.map((variant, i) => (
            <div key={i}>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-medium text-[var(--color-text-muted)]">
                  Variant {String.fromCharCode(65 + i)}
                </label>
                {variants.length > 2 && (
                  <button
                    onClick={() => removeVariant(i)}
                    className="p-0.5 text-[var(--color-text-light)] hover:text-red-500 transition-colors cursor-pointer"
                  >
                    <Trash2 size={12} />
                  </button>
                )}
              </div>
              <textarea
                value={variant}
                onChange={(e) => updateVariant(i, e.target.value)}
                placeholder={`Enter copy variant ${String.fromCharCode(65 + i)}...`}
                rows={2}
                className="w-full px-3 py-2 bg-[var(--color-surface)] rounded-lg text-[var(--color-text)] placeholder:text-[var(--color-text-light)] focus:outline-none resize-none text-sm"
              />
            </div>
          ))}

          {variants.length < 5 && (
            <button
              onClick={addVariant}
              className="w-full py-1.5 border border-dashed border-[var(--color-border)] rounded-lg text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors cursor-pointer flex items-center justify-center gap-1.5"
            >
              <Plus size={12} />
              Add Variant {String.fromCharCode(65 + variants.length)}
            </button>
          )}
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
            disabled={!canSubmit}
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
                onChange={(e) => setFilters({ ...filters, panel_size: parseInt(e.target.value) })}
                className="w-full accent-[var(--color-primary)]"
              />
            </div>
            {activeFilterCount > 0 && (
              <button
                onClick={() => setFilters({ panel_size: filters.panel_size })}
                className="flex items-center gap-1 text-xs text-[var(--color-text-muted)] hover:text-red-500 transition-colors cursor-pointer"
              >
                <X size={12} />
                Clear
              </button>
            )}
          </div>

          {options && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {FILTER_FIELDS.map(({ key, label, optionsKey }) => {
                const fieldOptions = options[optionsKey];
                if (!Array.isArray(fieldOptions) || fieldOptions.length === 0) return null;
                const currentValue = (filters[key] as string[] | undefined) ?? [];
                return (
                  <div key={key}>
                    <label className="block text-xs text-[var(--color-text-muted)] mb-0.5">{label}</label>
                    <select
                      value={currentValue[0] || ""}
                      onChange={(e) => setFilters({ ...filters, [key]: e.target.value ? [e.target.value] : undefined })}
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
        </div>
      )}

      {/* Examples */}
      <div className="flex flex-wrap gap-1 mt-1.5">
        {EXAMPLE_AB_TESTS.map((ex, i) => (
          <button
            key={i}
            onClick={() => loadExample(ex)}
            className="text-[10px] px-2 py-0.5 rounded-full text-[var(--color-text-light)] hover:text-[var(--color-text-muted)] transition-colors cursor-pointer"
          >
            {ex.label}
          </button>
        ))}
      </div>
    </div>
  );
}
