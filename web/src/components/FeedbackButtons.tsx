"use client";

import { useState } from "react";
import { useLanguage } from "@/components/LanguageContext";

interface FeedbackButtonsProps {
  currentFeedback?: "like" | "neutral" | "dislike";
  onFeedback: (rating: "like" | "neutral" | "dislike" | undefined) => void;
  onViewPaper: () => void;
}

function HeartIcon({ filled }: { filled: boolean }) {
  if (filled) {
    return (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 lg:w-7 lg:h-7">
        <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-6 h-6 lg:w-7 lg:h-7">
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
    </svg>
  );
}

function MinusCircleIcon({ filled }: { filled: boolean }) {
  if (filled) {
    return (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 lg:w-7 lg:h-7">
        <path fillRule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zm3 10.5a.75.75 0 000-1.5H9a.75.75 0 000 1.5h6z" clipRule="evenodd" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-6 h-6 lg:w-7 lg:h-7">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function ThumbDownIcon({ filled }: { filled: boolean }) {
  if (filled) {
    return (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 lg:w-7 lg:h-7">
        <path d="M15.73 5.25h1.035A7.465 7.465 0 0118 9.375a7.465 7.465 0 01-1.235 4.125h-.148c-.806 0-1.534.446-2.031 1.08a9.04 9.04 0 01-2.861 2.4c-.723.384-1.35.956-1.653 1.715a4.498 4.498 0 00-.322 1.672V21a.75.75 0 01-.75.75 2.25 2.25 0 01-2.25-2.25c0-1.152.26-2.243.723-3.218C7.74 15.724 7.366 15 6.748 15H3.622c-1.026 0-1.945-.694-2.054-1.715A12.134 12.134 0 011.5 12c0-2.848.992-5.464 2.649-7.521.388-.482.987-.729 1.605-.729H9.77a4.5 4.5 0 011.423.23l3.114 1.04a4.5 4.5 0 001.423.23zM21.669 13.773c.536-1.362.831-2.845.831-4.398 0-1.22-.182-2.398-.52-3.507-.26-.85-1.084-1.368-1.973-1.368H19.1c-.445 0-.72.498-.523.898.591 1.2.924 2.55.924 3.977a8.959 8.959 0 01-1.302 4.666c-.245.403.028.959.5.959h1.053c.832 0 1.612-.453 1.918-1.227z" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-6 h-6 lg:w-7 lg:h-7">
      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 15h2.25m8.024-9.75c.011.05.028.1.052.148.591 1.2.924 2.55.924 3.977a8.96 8.96 0 01-1.302 4.666c-.245.403.028.959.5.959H19.1c.832 0 1.612-.453 1.918-1.227.536-1.362.831-2.845.831-4.398 0-1.22-.182-2.398-.52-3.507-.26-.85-1.084-1.368-1.973-1.368H19.1c-.445 0-.72.498-.523.898zM15.73 5.25h1.035A7.465 7.465 0 0118 9.375a7.465 7.465 0 01-1.235 4.125h-.148c-.806 0-1.534.446-2.031 1.08a9.04 9.04 0 01-2.861 2.4c-.723.384-1.35.956-1.653 1.715a4.498 4.498 0 00-.322 1.672V21a.75.75 0 01-.75.75 2.25 2.25 0 01-2.25-2.25c0-1.152.26-2.243.723-3.218C7.74 15.724 7.366 15 6.748 15H3.622c-1.026 0-1.945-.694-2.054-1.715A12.134 12.134 0 011.5 12c0-2.848.992-5.464 2.649-7.521.388-.482.987-.729 1.605-.729H9.77a4.5 4.5 0 011.423.23l3.114 1.04a4.5 4.5 0 001.423.23z" />
    </svg>
  );
}

function ExternalLinkIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-6 h-6 lg:w-7 lg:h-7">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
    </svg>
  );
}

const actions = [
  {
    rating: "like" as const,
    labelKey: "feedback.like",
    activeColor: "text-rose-500",
    hoverBg: "hover:bg-rose-500/10",
  },
  {
    rating: "neutral" as const,
    labelKey: "feedback.neutral",
    activeColor: "text-amber-500",
    hoverBg: "hover:bg-amber-500/10",
  },
  {
    rating: "dislike" as const,
    labelKey: "feedback.dislike",
    activeColor: "text-zinc-400",
    hoverBg: "hover:bg-zinc-500/10",
  },
];

export default function FeedbackButtons({
  currentFeedback,
  onFeedback,
  onViewPaper,
}: FeedbackButtonsProps) {
  const [animating, setAnimating] = useState<string | null>(null);
  const { t } = useLanguage();

  function handleClick(rating: "like" | "neutral" | "dislike") {
    const isToggleOff = currentFeedback === rating;
    setAnimating(rating);
    setTimeout(() => setAnimating(null), 400);
    onFeedback(isToggleOff ? undefined : rating);
  }

  return (
    <div className="flex items-center justify-center gap-2 lg:gap-3 py-3 lg:py-4 border-t border-[var(--border)]">
      {actions.map((action) => {
        const isActive = currentFeedback === action.rating;
        const isAnimatingThis = animating === action.rating;

        return (
          <button
            key={action.rating}
            onClick={() => handleClick(action.rating)}
            className={`
              flex items-center gap-1.5 lg:gap-2 px-4 lg:px-5 py-2 lg:py-2.5 rounded-full
              transition-all duration-200
              ${isActive
                ? `${action.activeColor} bg-current/10 ring-1 ring-current/30`
                : `text-[var(--text-secondary)] ${action.hoverBg}`
              }
              ${isAnimatingThis && action.rating === "like" ? "animate-like-bounce" : ""}
              ${isAnimatingThis && action.rating === "dislike" ? "animate-shake" : ""}
              active:scale-95
            `}
          >
            {action.rating === "like" && (
              <HeartIcon filled={isActive} />
            )}
            {action.rating === "neutral" && (
              <MinusCircleIcon filled={isActive} />
            )}
            {action.rating === "dislike" && (
              <ThumbDownIcon filled={isActive} />
            )}
            <span className="text-xs lg:text-sm font-medium">{t(action.labelKey)}</span>
          </button>
        );
      })}

      <div className="w-px h-6 bg-[var(--border)] mx-1" />

      <button
        onClick={onViewPaper}
        className="flex items-center gap-1.5 lg:gap-2 px-4 lg:px-5 py-2 lg:py-2.5 rounded-full text-[var(--text-secondary)] hover:bg-blue-500/10 hover:text-[var(--accent-blue)] transition-all duration-200 active:scale-95"
      >
        <ExternalLinkIcon />
        <span className="text-xs lg:text-sm font-medium">{t("feedback.viewOriginal")}</span>
      </button>
    </div>
  );
}
