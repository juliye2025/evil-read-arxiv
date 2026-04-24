"use client";

import { useState, useEffect } from "react";
import type { Paper, PaperAnalysis, PaperImage } from "@/lib/types";
import { fetchAnalysis, fetchPaperImages } from "@/lib/api";
import { useLanguage } from "@/components/LanguageContext";
import FeedbackButtons from "./FeedbackButtons";

const DOMAIN_COLORS: Record<string, string> = {
  "VLA模型": "bg-blue-900/50 text-[var(--accent-blue)]",
  "世界模型": "bg-green-900/50 text-[var(--accent-green)]",
  "大语言模型": "bg-orange-900/50 text-[var(--accent-orange)]",
};

interface PaperCardProps {
  paper: Paper;
  onFeedback: (rating: "like" | "neutral" | "dislike" | undefined) => void;
}

export default function PaperCard({ paper, onFeedback }: PaperCardProps) {
  const { t } = useLanguage();
  const [analysis, setAnalysis] = useState<PaperAnalysis | null>(
    paper.highlights || null
  );
  const [images, setImages] = useState<PaperImage[]>(paper.images || []);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [loadingImages, setLoadingImages] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(!!paper.highlights);
  const [lightboxImg, setLightboxImg] = useState<string | null>(null);

  // Reset state and load images when paper changes
  useEffect(() => {
    let cancelled = false;

    // Reset state for new paper
    setAnalysis(paper.highlights || null);
    setImages(paper.images || []);
    setShowAnalysis(!!paper.highlights);
    setLoadingAnalysis(false);
    setLightboxImg(null);

    // Load images (lightweight, cached on server)
    if (!paper.images?.length) {
      setLoadingImages(true);
      fetchPaperImages(paper.arxiv_id)
        .then((data) => { if (!cancelled) setImages(data); })
        .catch((err) => { if (!cancelled) console.error("Image loading failed:", err); })
        .finally(() => { if (!cancelled) setLoadingImages(false); });
    }

    return () => { cancelled = true; };
  }, [paper.arxiv_id, paper.highlights, paper.images]);

  const handleDeepDive = () => {
    if (analysis) {
      setShowAnalysis(true);
      return;
    }
    setShowAnalysis(true);
    setLoadingAnalysis(true);
    fetchAnalysis(paper.arxiv_id)
      .then((data) => setAnalysis(data))
      .catch((err) => console.error("Analysis failed:", err))
      .finally(() => setLoadingAnalysis(false));
  };

  const domainColor =
    DOMAIN_COLORS[paper.matched_domain] ||
    "bg-purple-900/50 text-[var(--accent-purple)]";

  const scoreColor =
    paper.scores.recommendation >= 8
      ? "bg-green-900/50 text-[var(--accent-green)]"
      : paper.scores.recommendation >= 6
        ? "bg-yellow-900/50 text-[var(--accent-orange)]"
        : "bg-red-900/50 text-[var(--accent-red)]";

  return (
    <div className="h-full flex flex-col px-4 pt-2 pb-0 lg:px-8 lg:pt-6 w-full">
      {/* Domain tags + score */}
      <div className="flex justify-between items-center mb-3 lg:mb-4 flex-shrink-0">
        <div className="flex gap-2 flex-wrap">
          <span
            className={`px-3 py-1 rounded-full text-xs lg:text-sm font-bold ${domainColor}`}
          >
            {paper.matched_domain}
          </span>
          {paper.categories.slice(0, 3).map((cat) => (
            <span
              key={cat}
              className="px-2 py-1 rounded-full text-[10px] lg:text-xs bg-[#0f3460] text-[var(--text-secondary)]"
            >
              {cat}
            </span>
          ))}
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs lg:text-sm font-bold ${scoreColor}`}
        >
          {paper.scores.recommendation.toFixed(1)}
        </span>
      </div>

      {/* Title */}
      <h1 className="text-xl lg:text-2xl font-bold text-white leading-snug mb-1 lg:mb-2 flex-shrink-0">
        {paper.title}
      </h1>

      {/* Authors + date */}
      <p className="text-xs lg:text-sm text-[var(--text-secondary)] mb-3 lg:mb-4 flex-shrink-0">
        {paper.authors.slice(0, 3).join(", ")}
        {paper.authors.length > 3 ? " et al." : ""}
        {paper.affiliations.length > 0 &&
          ` · ${paper.affiliations.slice(0, 2).join(", ")}`}
        {` · ${paper.published_date.slice(0, 10)}`}
      </p>

      {/* Content (scrollable) */}
      <div className="flex-1 overflow-y-auto space-y-3 lg:space-y-4 min-h-0 pr-1">
        {/* Image gallery */}
        {!loadingImages && images.length > 0 && (
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 flex-shrink-0">
            {images.slice(0, 6).map((img) => (
              <button
                key={img.filename}
                onClick={() => setLightboxImg(img.url)}
                className="flex-shrink-0 rounded-lg overflow-hidden border border-[var(--border)] hover:border-[var(--accent-blue)]/50 transition-colors bg-[var(--bg-secondary)]"
              >
                <img
                  src={img.url}
                  alt={img.filename}
                  className="h-28 lg:h-40 w-auto object-contain"
                  loading="lazy"
                />
              </button>
            ))}
          </div>
        )}
        {loadingImages && (
          <div className="flex gap-3 pb-2">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="flex-shrink-0 h-28 lg:h-40 w-36 lg:w-48 rounded-lg bg-[var(--bg-secondary)] animate-pulse"
              />
            ))}
          </div>
        )}

        {/* Chinese summary (always visible) */}
        {paper.summary && (
          <div className="bg-[var(--bg-secondary)] border-l-[3px] border-l-[var(--accent-blue)] rounded-r-lg p-3 lg:p-4">
            <div className="text-sm lg:text-base leading-relaxed text-[var(--text-primary)] opacity-90 whitespace-pre-line">
              {paper.summary}
            </div>
          </div>
        )}

        {/* Deep dive button / Detailed analysis */}
        {!showAnalysis ? (
          <button
            onClick={handleDeepDive}
            className="w-full py-2.5 lg:py-3 rounded-lg border border-[var(--accent-blue)]/40 bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] text-sm lg:text-base font-medium hover:bg-[var(--accent-blue)]/20 transition-colors flex items-center justify-center gap-2"
          >
            <span>🔍</span>
            {t("paper.deepDive")}
          </button>
        ) : loadingAnalysis ? (
          <div className="space-y-3">
            <div className="text-center text-xs text-[var(--text-secondary)] py-1">
              {t("paper.loadingAnalysis")}
            </div>
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bg-[var(--bg-secondary)] rounded-r-lg p-3 lg:p-4 border-l-[3px] border-l-[var(--border)]"
              >
                <div className="h-4 w-24 bg-[var(--border)] rounded animate-pulse mb-2" />
                <div className="space-y-2">
                  <div className="h-3 w-full bg-[var(--border)] rounded animate-pulse" />
                  <div className="h-3 w-4/5 bg-[var(--border)] rounded animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        ) : analysis ? (
          <>
            <ContentBlock
              icon="💡"
              title={t("paper.coreContribution")}
              content={analysis.contribution}
              borderColor="border-l-[var(--accent-blue)]"
              titleColor="text-[var(--accent-blue)]"
            />
            <ContentBlock
              icon="✨"
              title={t("paper.innovation")}
              content={analysis.innovation}
              borderColor="border-l-[var(--accent-purple)]"
              titleColor="text-[var(--accent-purple)]"
            />
            <ContentBlock
              icon="🔧"
              title={t("paper.methodSummary")}
              content={analysis.method}
              borderColor="border-l-[var(--accent-orange)]"
              titleColor="text-[var(--accent-orange)]"
            />
            <ContentBlock
              icon="📊"
              title={t("paper.keyResults")}
              content={analysis.results}
              borderColor="border-l-[var(--accent-green)]"
              titleColor="text-[var(--accent-green)]"
            />
          </>
        ) : null}

        {/* Keywords */}
        <div className="flex flex-wrap gap-1.5 lg:gap-2 pt-1 pb-2">
          {paper.matched_keywords.map((kw) => (
            <span
              key={kw}
              className="px-2 lg:px-3 py-0.5 lg:py-1 rounded-full text-[10px] lg:text-xs border border-[var(--border)] text-[var(--text-secondary)] bg-[var(--bg-card)]"
            >
              {kw}
            </span>
          ))}
        </div>
      </div>

      {/* Feedback buttons */}
      <div className="flex-shrink-0">
        <FeedbackButtons
          currentFeedback={paper.feedback}
          onFeedback={onFeedback}
          onViewPaper={() =>
            window.open(paper.arxiv_url || paper.pdf_url, "_blank")
          }
        />
      </div>

      {/* Lightbox */}
      {lightboxImg && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 lightbox-overlay"
          onClick={() => setLightboxImg(null)}
        >
          <button
            className="absolute top-4 right-4 text-white/70 hover:text-white text-3xl"
            onClick={() => setLightboxImg(null)}
          >
            &times;
          </button>
          <img
            src={lightboxImg}
            alt="Paper figure"
            className="max-w-[90vw] max-h-[85vh] object-contain rounded-lg"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}

function ContentBlock({
  icon,
  title,
  content,
  borderColor,
  titleColor,
}: {
  icon: string;
  title: string;
  content: string;
  borderColor: string;
  titleColor: string;
}) {
  return (
    <div
      className={`bg-[var(--bg-secondary)] border-l-[3px] ${borderColor} rounded-r-lg p-3 lg:p-4`}
    >
      <div className={`text-xs lg:text-sm font-bold mb-1 lg:mb-1.5 ${titleColor}`}>
        {icon} {title}
      </div>
      <div className="text-sm lg:text-base leading-relaxed text-[var(--text-primary)] opacity-85">
        {content}
      </div>
    </div>
  );
}
