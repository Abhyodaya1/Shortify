"use client";

import React from "react";
import { BackgroundPreset } from "./types";

interface Props {
  preset: BackgroundPreset;
  isSelected: boolean;
  onSelect: (preset: BackgroundPreset) => void;
}

export const BackgroundPresetCard: React.FC<Props> = ({ preset, isSelected, onSelect }) => {
  return (
    <div
      onClick={() => onSelect(preset)}
      className="flex flex-col items-center gap-1.5 cursor-pointer select-none group"
    >
      <div
        className={`w-full h-12 sm:h-14 rounded-xl border-2 transition-all flex items-center justify-center ${
          isSelected
            ? "border-[#3B82F6] shadow-[0_0_10px_rgba(59,130,246,0.5)] translate-y-[-1px]"
            : "border-[#252A34] group-hover:border-[#384152]"
        }`}
        style={{
          background: preset.cssValue,
        }}
      >
        {preset.type === "blur" && (
          <span className="font-mono text-[9px] text-white/80 font-bold bg-black/40 px-2 py-0.5 rounded-md">
            BLUR
          </span>
        )}
        {preset.type === "gameplay" && (
          <span className="font-mono text-[9px] text-[#D5EB45] font-bold bg-black/60 px-2 py-0.5 rounded-md">
            GAMEPLAY
          </span>
        )}
      </div>
      <span
        className={`font-sans text-xs transition-colors ${
          isSelected ? "text-[#3B82F6] font-bold" : "text-neutral-400 group-hover:text-neutral-200"
        }`}
      >
        {preset.name}
      </span>
    </div>
  );
};

