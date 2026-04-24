"use client";

interface ProgressBarProps {
  current: number;
  total: number;
  date: string;
  feedbackCount: number;
}

export default function ProgressBar({
  current,
  total,
  date,
  feedbackCount,
}: ProgressBarProps) {
  const progress = total > 0 ? ((current + 1) / total) * 100 : 0;

  return (
    <div className="flex-shrink-0 px-4 py-2 flex items-center justify-between bg-[var(--bg-primary)]/80 backdrop-blur-sm">
      <div className="flex items-center gap-2">
        <span className="text-sm lg:text-base">📅</span>
        <span className="text-xs lg:text-sm font-bold">{date}</span>
      </div>

      <div className="flex-1 mx-4 h-1 lg:h-1.5 bg-[var(--border)] rounded-full overflow-hidden">
        <div
          className="h-full bg-[var(--accent-blue)] rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex items-center gap-2">
        <span className="bg-[var(--accent-blue)] text-[var(--bg-primary)] px-2 py-0.5 rounded-full text-[10px] lg:text-xs font-bold">
          {current + 1}/{total}
        </span>
        {feedbackCount > 0 && (
          <span className="text-[10px] lg:text-xs text-[var(--accent-green)]">
            ✓{feedbackCount}
          </span>
        )}
      </div>
    </div>
  );
}
