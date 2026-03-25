"use client";

import { useState } from "react";
import { Send, SlidersHorizontal } from "lucide-react";
import type { PanelFilters } from "@/lib/types";

const EXAMPLE_STATEMENTS = [
  "Canada is a land of opportunity where hard work leads to prosperity for all.",
  "Our new banking app makes managing your money effortless — built for modern Canadians.",
  "Join thousands of Canadians who trust our healthcare platform for faster, smarter care.",
  "Experience the Canadian dream with our new line of sustainable outdoor gear.",
];

const EXAMPLE_BRIEFS = [
  "South Asian immigrants settling in the GTA, first-time homebuyers",
  "French Canadians in Quebec and New Brunswick, culturally proud, cost-conscious",
  "Indigenous communities across Northern Canada, focused on healthcare access",
  "Conservative voters in Alberta worried about carbon tax and energy jobs",
  "Muslim families, halal-conscious, shopping for grocery delivery",
  "Middle-income families ($50-80K) comparing grocery delivery services",
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

  const handleSubmit = () => {
    if (!message.trim()) return;
    onStart(message.trim(), audienceBrief.trim(), filters);
  };

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
            placeholder="Describe by demographics, income, culture, values, concerns, or life stage..."
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
            Panel Size: {filters.panel_size}
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
            onChange={(e) =>
              setFilters({ ...filters, panel_size: parseInt(e.target.value) })
            }
            className="w-full max-w-xs accent-[var(--color-primary)]"
          />
        </div>
      )}
    </div>
  );
}
