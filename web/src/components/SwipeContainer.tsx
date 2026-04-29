"use client";

import { useState, useRef, useCallback, useEffect, type ReactNode } from "react";

interface SwipeContainerProps {
  currentIndex: number;
  totalItems: number;
  onSwipe: (direction: "up" | "down") => void;
  children: ReactNode;
}

export default function SwipeContainer({
  currentIndex,
  totalItems,
  onSwipe,
  children,
}: SwipeContainerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const touchStartY = useRef(0);
  const [dragOffset, setDragOffset] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);

  const handleSwipe = useCallback(
    (direction: "up" | "down") => {
      if (isTransitioning) return;
      if (direction === "up" && currentIndex >= totalItems - 1) return;
      if (direction === "down" && currentIndex <= 0) return;

      setIsTransitioning(true);
      setDragOffset(direction === "up" ? -window.innerHeight : window.innerHeight);

      setTimeout(() => {
        onSwipe(direction);
        setDragOffset(0);
        setIsTransitioning(false);
      }, 400);
    },
    [currentIndex, totalItems, isTransitioning, onSwipe]
  );

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartY.current = e.touches[0].clientY;
  }, []);

  const handleTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (isTransitioning) return;
      const delta = touchStartY.current - e.touches[0].clientY;
      setDragOffset(-delta * 0.3);
    },
    [isTransitioning]
  );

  const handleTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      if (isTransitioning) return;
      const delta = touchStartY.current - e.changedTouches[0].clientY;
      setDragOffset(0);
      if (Math.abs(delta) > 80) {
        handleSwipe(delta > 0 ? "up" : "down");
      }
    },
    [isTransitioning, handleSwipe]
  );

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "ArrowUp" || e.key === "k") handleSwipe("down");
      if (e.key === "ArrowDown" || e.key === "j") handleSwipe("up");
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleSwipe]);

  const wheelTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    function handleWheel(e: WheelEvent) {
      e.preventDefault();
      if (wheelTimeout.current) return;
      if (Math.abs(e.deltaY) < 30) return;
      handleSwipe(e.deltaY > 0 ? "up" : "down");
      wheelTimeout.current = setTimeout(() => {
        wheelTimeout.current = null;
      }, 500);
    }

    el.addEventListener("wheel", handleWheel, { passive: false });
    return () => el.removeEventListener("wheel", handleWheel);
  }, [handleSwipe]);

  return (
    <div
      ref={containerRef}
      className="h-full w-full overflow-hidden relative"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <div
        className="h-full w-full"
        style={{
          transform: `translateY(${dragOffset}px)`,
          transition: isTransitioning
            ? "transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)"
            : "transform 0.1s ease-out",
        }}
      >
        {children}
      </div>

      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex flex-col items-center gap-0.5 text-[var(--border)] text-xs pointer-events-none">
        {currentIndex > 0 && <span>&#9650;</span>}
        <span className="[writing-mode:vertical-lr] text-[9px]">
          {currentIndex + 1}/{totalItems}
        </span>
        {currentIndex < totalItems - 1 && <span>&#9660;</span>}
      </div>
    </div>
  );
}
