"use client";

import Image from "next/image";
import { ArrowRight, Users, GitCompare, ClipboardCheck, Play } from "lucide-react";

interface VideoCard {
  title: string;
  description: string;
  youtubeId: string; // YouTube video ID — replace with real IDs
}

const VIDEOS: VideoCard[] = [
  {
    title: "What It Does",
    description: "Real scenarios, real reactions, 6 minutes.",
    youtubeId: "mj6Ts8MwIII",
  },
  {
    title: "How It Works",
    description: "The tech behind the panel engine.",
    youtubeId: "PLACEHOLDER_TECHNICAL",
  },
];

const FEATURES = [
  {
    icon: Users,
    title: "Focus Group",
    description: "Reactions from a matched panel + optimized rewrite.",
  },
  {
    icon: GitCompare,
    title: "A/B Copy Test",
    description: "Two variants, same panel, clear winner.",
  },
  {
    icon: ClipboardCheck,
    title: "Survey Pre-Test",
    description: "Catch bias and ambiguity before you send it.",
  },
];

interface LandingPageProps {
  onEnterApp: () => void;
}

export function LandingPage({ onEnterApp }: LandingPageProps) {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-[var(--color-border)] bg-[var(--color-bg-card)]">
        <div className="max-w-5xl mx-auto px-4 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Image
              src="/logo-mark.png"
              alt="MaplePulse"
              width={512}
              height={512}
              className="h-8 w-auto object-contain"
              priority
            />
            <div className="flex items-baseline gap-0">
              <span className="text-xl font-bold tracking-tight" style={{ color: "#C1272D" }}>Maple</span>
              <span className="text-xl font-bold tracking-tight" style={{ color: "#1B7B7E" }}>Pulse</span>
            </div>
          </div>
          <button
            onClick={onEnterApp}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
          >
            Try it
            <ArrowRight size={14} />
          </button>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-4 pt-16 pb-12 text-center">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-3">
          Synthetic focus groups for Canada
        </h1>
        <p className="text-base text-[var(--color-text-muted)] max-w-lg mx-auto mb-8">
          Describe your audience. Get instant reactions from AI personas built on real Canadian data.
        </p>
        <button
          onClick={onEnterApp}
          className="inline-flex items-center gap-2 px-6 py-2.5 bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] text-white rounded-lg font-medium transition-colors cursor-pointer"
        >
          Get started
          <ArrowRight size={16} />
        </button>
        <p className="text-xs text-[var(--color-text-light)] mt-3">
          A first filter, not a replacement for real research.
        </p>
      </section>

      {/* Features */}
      <section className="max-w-4xl mx-auto px-4 pb-16">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {FEATURES.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5"
            >
              <Icon size={20} className="text-[var(--color-text-muted)] mb-3" />
              <h3 className="text-sm font-semibold mb-1">{title}</h3>
              <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">{description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Videos */}
      <section className="max-w-4xl mx-auto px-4 pb-20">
        <h2 className="text-lg font-semibold text-center mb-6">See it in action</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl mx-auto">
          {VIDEOS.map(({ title, description, youtubeId }) => (
            <div
              key={title}
              className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl overflow-hidden"
            >
              {/* Video embed — replace PLACEHOLDER IDs with real YouTube video IDs */}
              <div className="relative w-full aspect-video bg-[var(--color-surface)]">
                {youtubeId.startsWith("PLACEHOLDER") ? (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="flex flex-col items-center gap-2 text-[var(--color-text-light)]">
                      <Play size={32} />
                      <span className="text-xs">Coming soon</span>
                    </div>
                  </div>
                ) : (
                  <iframe
                    src={`https://www.youtube.com/embed/${youtubeId}`}
                    title={title}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    className="absolute inset-0 w-full h-full"
                  />
                )}
              </div>
              <div className="p-4">
                <h3 className="text-sm font-semibold mb-1">{title}</h3>
                <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">{description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--color-border)] py-6 text-center">
        <p className="text-xs text-[var(--color-text-light)]">
          MaplePulse — AI personas grounded in real Canadian data. Not a replacement for real research.
        </p>
      </footer>
    </div>
  );
}
