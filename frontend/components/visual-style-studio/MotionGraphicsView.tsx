"use client";

import React from "react";

interface Props {
  type: "arrow" | "circle" | "callout" | "brush";
  color?: string;
  className?: string;
}

export const MotionGraphicsView: React.FC<Props> = ({
  type,
  color = "#00E297",
  className = "",
}) => {
  if (type === "arrow") {
    return (
      <svg
        viewBox="0 0 100 100"
        className={`w-16 h-16 pointer-events-none select-none drop-shadow-[0_2px_8px_rgba(0,0,0,0.6)] ${className}`}
      >
        <path
          d="M 15 85 Q 40 40 80 20"
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
        />
        <path
          d="M 60 16 L 82 20 L 78 42"
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (type === "circle") {
    return (
      <svg
        viewBox="0 0 100 100"
        className={`w-20 h-20 pointer-events-none select-none drop-shadow-[0_2px_8px_rgba(0,0,0,0.6)] ${className}`}
      >
        <ellipse
          cx="50"
          cy="50"
          rx="40"
          ry="36"
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeDasharray="4 2"
          strokeLinecap="round"
          className="animate-pulse"
        />
      </svg>
    );
  }

  if (type === "callout") {
    return (
      <div
        className={`px-3 py-1.5 rounded-lg border-2 bg-[#0C0F14]/90 backdrop-blur-xs shadow-xl pointer-events-none select-none ${className}`}
        style={{ borderColor: color }}
      >
        <span className="font-mono text-[9px] uppercase font-bold text-white block">
          Key Insight
        </span>
        <span className="font-sans text-[11px] text-neutral-300">
          Viral Retention Trigger
        </span>
      </div>
    );
  }

  // Brush highlight
  return (
    <div
      className={`h-2.5 rounded-full opacity-80 pointer-events-none select-none ${className}`}
      style={{
        backgroundColor: color,
        boxShadow: `0 0 10px ${color}`,
      }}
    />
  );
};
