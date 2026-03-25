"use client";

import { useState } from "react";
import { Plus, Trash2, SlidersHorizontal, Send } from "lucide-react";
import type { PanelFilters } from "@/lib/types";

const EXAMPLE_AB_TESTS = [
  {
    label: "Banking app taglines",
    variants: [
      "Your money, your way. Banking that fits your life.",
      "Smart banking for modern Canadians. Join thousands who've switched.",
    ],
    brief: "New immigrants navigating Canadian banking for the first time",
  },
  {
    label: "Sustainable outdoor gear",
    variants: [
      "Adventure awaits — gear up with Canada's most sustainable outdoor brand.",
      "Built tough. Built green. Outdoor gear that respects the land.",
    ],
    brief: "Environmentally conscious families in BC and Alberta",
  },
  {
    label: "Healthcare platform (3 variants)",
    variants: [
      "Faster care starts here. Join Canada's #1 digital health platform.",
      "Your health, on your schedule. Virtual care when you need it most.",
      "Skip the wait. See a doctor online in minutes, not months.",
    ],
    brief: "Rural Canadians concerned about healthcare wait times",
  },
];

interface ABTestInputProps {
  onStart: (variants: string[], audienceBrief: string, filters: PanelFilters) => void;
}

export function ABTestInput({ onStart }: ABTestInputProps) {
  const [variants, setVariants] = useState<string[]>(["", ""]);
  const [audienceBrief, setAudienceBrief] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<PanelFilters>({ panel_size: 12 });

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
            placeholder="Describe by demographics, income, culture, values, concerns, or life stage..."
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

        {/* Examples */}
        <div className="flex flex-wrap gap-1 px-4 pb-2">
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

        {/* Actions */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--color-border)]">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors cursor-pointer"
          >
            <SlidersHorizontal size={14} />
            Panel Size: {filters.panel_size}
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

      {/* Panel size slider */}
      {showFilters && (
        <div className="bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-4">
          <label className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">
            Panel Size: {filters.panel_size}
          </label>
          <input
            type="range"
            min={6}
            max={20}
            value={filters.panel_size}
            onChange={(e) => setFilters({ ...filters, panel_size: parseInt(e.target.value) })}
            className="w-full max-w-xs accent-[var(--color-primary)]"
          />
        </div>
      )}

    </div>
  );
}
