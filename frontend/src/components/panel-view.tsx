"use client";

import { useState } from "react";
import {
  MapPin,
  Briefcase,
  DollarSign,
  GraduationCap,
  Languages,
  Heart,
  Loader2,
  Database,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { Persona } from "@/lib/types";
import { cn } from "@/lib/cn";

/** Maps each persona field to its data source for provenance display. */
const DATA_SOURCES: { field: string; source: string; detail: string }[] = [
  { field: "Age, Sex, Province", source: "StatCan Census 2021", detail: "2021 Census of Population — demographic distributions" },
  { field: "Planning Area / City", source: "StatCan Census 2021", detail: "Census subdivisions and planning regions" },
  { field: "Occupation", source: "StatCan NOC 2021", detail: "National Occupational Classification exemplar job titles" },
  { field: "Education Level", source: "StatCan Census 2021", detail: "Census education attainment by age and province" },
  { field: "Income", source: "Job Bank Canada 2025", detail: "Wages by NOC code + province, age-adjusted within quartiles" },
  { field: "Languages", source: "StatCan Census 2021", detail: "Mother tongue + knowledge of official languages" },
  { field: "Cultural Background", source: "StatCan Census 2021", detail: "Ethnic/cultural origins by province" },
  { field: "Indigenous Identity", source: "StatCan Census 2021", detail: "Aboriginal identity by province" },
  { field: "Visible Minority", source: "StatCan Census 2021", detail: "Visible minority status by province" },
  { field: "Immigration Status", source: "StatCan Census 2021", detail: "Immigration and citizenship data" },
  { field: "Religion", source: "StatCan Census 2021", detail: "100+ religious affiliations by province — 53.3% Christian, 34.6% no religion" },
  { field: "Housing", source: "StatCan Census 2021", detail: "Dwelling type and tenure distributions" },
  { field: "Political Leaning", source: "CES + Angus Reid", detail: "Canadian Election Study + Angus Reid Values surveys" },
  { field: "Top Concerns", source: "Environics + Angus Reid", detail: "Provincial concern priorities from survey research" },
  { field: "Commute Mode", source: "StatCan Journey to Work", detail: "Census 2021 commuting data — 80.9% drive, 11.9% transit" },
];

const PROVINCE_COLORS: Record<string, string> = {
  Ontario: "bg-blue-100 text-blue-700",
  Quebec: "bg-indigo-100 text-indigo-700",
  "British Columbia": "bg-emerald-100 text-emerald-700",
  Alberta: "bg-amber-100 text-amber-700",
  Manitoba: "bg-rose-100 text-rose-700",
  Saskatchewan: "bg-lime-100 text-lime-700",
  "Nova Scotia": "bg-cyan-100 text-cyan-700",
  "New Brunswick": "bg-teal-100 text-teal-700",
  "Newfoundland and Labrador": "bg-sky-100 text-sky-700",
  "Prince Edward Island": "bg-pink-100 text-pink-700",
};

function PersonaCard({
  persona,
  index,
  isAnimating,
}: {
  persona: Persona;
  index: number;
  isAnimating: boolean;
}) {
  return (
    <div
      className={cn(
        "bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] p-4 shadow-sm transition-all duration-300",
        isAnimating && "animate-[fadeIn_0.4s_ease-out]"
      )}
      style={{ animationDelay: `${index * 80}ms`, animationFillMode: "both" }}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-[var(--color-primary)]/10 flex items-center justify-center text-sm font-semibold text-[var(--color-primary)]">
              {persona.age}
            </div>
            <div>
              <p className="text-sm font-semibold">{persona.sex}</p>
              <p className="text-xs text-[var(--color-text-muted)]">
                {persona.cultural_background}
              </p>
            </div>
          </div>
        </div>
        <span
          className={cn(
            "text-xs px-2 py-0.5 rounded-full font-medium",
            PROVINCE_COLORS[persona.province] || "bg-gray-100 text-gray-700"
          )}
        >
          {persona.province}
        </span>
      </div>

      <div className="space-y-1.5 text-xs text-[var(--color-text-muted)]">
        <div className="flex items-center gap-1.5">
          <Briefcase size={12} />
          <span>{persona.occupation}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <MapPin size={12} />
          <span>{persona.planning_area}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <DollarSign size={12} />
          <span>{persona.income_bracket}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <GraduationCap size={12} />
          <span>{persona.education_level}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Languages size={12} />
          <span>{persona.languages_spoken}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Heart size={12} />
          <span>{persona.top_concerns.join(", ")}</span>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-1">
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-surface)] text-[var(--color-text-muted)]">
          {persona.political_leaning}
        </span>
        {persona.indigenous_identity !== "Non-Indigenous" && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700">
            {persona.indigenous_identity}
          </span>
        )}
        {persona.visible_minority !== "Not a visible minority" && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700">
            {persona.visible_minority}
          </span>
        )}
      </div>
    </div>
  );
}

interface PanelViewProps {
  panel: Persona[];
  onContinue: () => void;
  /** When true, reactions are still loading — show waiting state on button */
  waitingForReactions?: boolean;
  /** When true, hide the header (used in the drawer) */
  hideHeader?: boolean;
}

export function PanelView({ panel, onContinue, waitingForReactions, hideHeader }: PanelViewProps) {
  const [showSources, setShowSources] = useState(false);

  return (
    <div className="space-y-4">
      {!hideHeader && (
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold font-[family-name:var(--font-heading)]">
              Your Panel — {panel.length} Canadians
            </h2>
            <p className="text-sm text-[var(--color-text-muted)]">
              Sampled from 5,000 census-weighted personas across Canada
            </p>
          </div>
          <button
            onClick={onContinue}
            disabled={waitingForReactions}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-white rounded-lg text-sm font-medium transition-colors cursor-pointer",
              waitingForReactions
                ? "bg-[var(--color-text-muted)] cursor-wait"
                : "bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)]"
            )}
          >
            {waitingForReactions && <Loader2 size={14} className="animate-spin" />}
            {waitingForReactions ? "Waiting for reactions..." : "View Round 1"}
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {panel.map((p, i) => (
          <PersonaCard key={p.uuid} persona={p} index={i} isAnimating />
        ))}
      </div>

      {/* Data Sources — collapsible */}
      <div className="border border-[var(--color-border)] rounded-xl overflow-hidden">
        <button
          onClick={() => setShowSources(!showSources)}
          className="w-full flex items-center justify-between px-4 py-2.5 bg-[var(--color-surface)] hover:bg-[var(--color-border)]/30 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2 text-xs font-medium text-[var(--color-text-muted)]">
            <Database size={13} />
            Data Sources — where each persona field comes from
          </div>
          {showSources ? <ChevronUp size={14} className="text-[var(--color-text-muted)]" /> : <ChevronDown size={14} className="text-[var(--color-text-muted)]" />}
        </button>
        {showSources && (
          <div className="px-4 py-3 bg-[var(--color-bg-card)]">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-1.5">
              {DATA_SOURCES.map((ds) => (
                <div key={ds.field} className="flex items-baseline gap-1.5 text-[11px]">
                  <span className="font-medium text-[var(--color-text)] whitespace-nowrap">{ds.field}</span>
                  <span className="text-[var(--color-text-light)]" title={ds.detail}>{ds.source}</span>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-[var(--color-text-light)] mt-3 pt-2 border-t border-[var(--color-border)]">
              All personas are synthetic — generated from statistical distributions, not individual records. Income is derived from Job Bank 2025 median wages by NOC occupation code and province, age-adjusted within quartiles.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
