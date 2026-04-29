"use client";

import type { Paper } from "@/lib/types";

const DOMAIN_COLORS: Record<string, string> = {
  "VLA模型": "border-l-[var(--accent-blue)] text-[var(--accent-blue)]",
  "世界模型": "border-l-[var(--accent-green)] text-[var(--accent-green)]",
  "大语言模型": "border-l-[var(--accent-orange)] text-[var(--accent-orange)]",
};

const FEEDBACK_EMOJI: Record<string, string> = {
  like: "👍",
  neutral: "😐",
  dislike: "👎",
};

interface PaperListItemProps {
  paper: Paper;
  isSelected: boolean;
  onClick: () => void;
}

export default function PaperListItem({
  paper,
  isSelected,
  onClick,
}: PaperListItemProps) {
  const domainStyle =
    DOMAIN_COLORS[paper.matched_domain] ||
    "border-l-[var(--accent-purple)] text-[var(--accent-purple)]";

  const scoreColor =
    paper.scores.recommendation >= 8
      ? "text-[var(--accent-green)]"
      : paper.scores.recommendation >= 6
        ? "text-[var(--accent-orange)]"
        : "text-[var(--accent-red)]";

  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-3 py-3 border-l-[3px] transition-colors ${domainStyle} ${
        isSelected
          ? "bg-[var(--bg-card)] border-l-[var(--accent-blue)]"
          : "bg-transparent border-l-transparent hover:bg-[var(--bg-secondary)]"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3
          className={`text-sm font-medium leading-snug line-clamp-2 ${
            isSelected ? "text-white" : "text-[var(--text-primary)]"
          }`}
        >
          {paper.title}
        </h3>
        <div className="flex-shrink-0 flex items-center gap-1.5">
          {paper.feedback && (
            <span className="text-sm">{FEEDBACK_EMOJI[paper.feedback]}</span>
          )}
          <span className={`text-xs font-bold ${scoreColor}`}>
            {paper.scores.recommendation.toFixed(1)}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-2 mt-1">
        <span className={`text-xs opacity-80`}>
          {paper.matched_domain}
        </span>
        <span className="text-xs text-[var(--text-secondary)]">
          {paper.authors.slice(0, 2).join(", ")}
          {paper.authors.length > 2 ? " et al." : ""}
        </span>
      </div>
      {/* Chinese summary preview */}
      <p className="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2 leading-relaxed">
        {paper.summary}
      </p>
    </button>
  );
}
