"use client";

import React from "react";
import { VideoLayoutPreset } from "./types";

interface Props {
  preset: VideoLayoutPreset;
  isSelected: boolean;
  onSelect: (preset: VideoLayoutPreset) => void;
}

export const LayoutPresetCard: React.FC<Props> = ({ preset, isSelected, onSelect }) => {
  return (
    <div
      onClick={() => onSelect(preset)}
      className={`group flex flex-col items-center gap-2 cursor-pointer select-none transition-all`}
    >
      {/* Miniature 9:16 Canvas Frame */}
      <div
        className={`relative w-28 sm:w-32 aspect-[9/16] rounded-xl border-2 p-1.5 transition-all flex flex-col justify-between overflow-hidden ${
          isSelected
            ? "border-[#3B82F6] bg-[#181B20] shadow-[0_0_12px_rgba(59,130,246,0.4)] translate-y-[-2px]"
            : "border-[#252A34] bg-[#111317] hover:border-[#384152] hover:bg-[#14171D]"
        }`}
      >
        {/* LAYOUT 1: Full Screen */}
        {preset.type === "full_screen" && (
          <div className="w-full h-full rounded-lg bg-[#8A8F98] flex items-center justify-center">
            <span className="font-mono text-[9px] text-[#111] font-bold">9:16 FULL</span>
          </div>
        )}

        {/* LAYOUT 2: 50/50 Split */}
        {preset.type === "split_50_50" && (
          <div className="w-full h-full flex flex-col gap-1">
            <div className="w-full h-1/2 rounded-md bg-[#8A8F98] flex items-center justify-center">
              <span className="font-mono text-[8px] text-[#111] font-bold">SPEAKER</span>
            </div>
            <div className="w-full h-1/2 rounded-md bg-[#3D424D] flex items-center justify-center">
              <span className="font-mono text-[8px] text-[#AAA] font-bold">B-ROLL</span>
            </div>
          </div>
        )}

        {/* LAYOUT 3: 60/40 Split */}
        {preset.type === "split_60_40" && (
          <div className="w-full h-full flex flex-col gap-1">
            <div className="w-full h-[60%] rounded-md bg-[#8A8F98] flex items-center justify-center">
              <span className="font-mono text-[8px] text-[#111] font-bold">SPEAKER</span>
            </div>
            <div className="w-full h-[40%] rounded-md bg-[#3D424D] flex items-center justify-center">
              <span className="font-mono text-[8px] text-[#AAA] font-bold">GAMEPLAY</span>
            </div>
          </div>
        )}

        {/* LAYOUT 4: Floating */}
        {preset.type === "floating" && (
          <div className="w-full h-full rounded-lg bg-[#1D212A] flex items-center justify-center p-2 relative">
            <div className="w-[84%] h-[58%] rounded-lg bg-[#8A8F98] shadow-md border border-white/20 flex items-center justify-center">
              <span className="font-mono text-[8px] text-[#111] font-bold">FLOAT</span>
            </div>
          </div>
        )}

        {/* LAYOUT 5: Blurred Background */}
        {preset.type === "blurred_bg" && (
          <div className="w-full h-full rounded-lg bg-[#2D333F]/80 flex items-center justify-center relative p-1.5 backdrop-blur-xs">
            <div className="w-[88%] h-[50%] rounded-md bg-[#8A8F98] shadow-md border border-white/30 flex items-center justify-center">
              <span className="font-mono text-[8px] text-[#111] font-bold">16:9 MAIN</span>
            </div>
          </div>
        )}

        {/* LAYOUT 6: Card Frame */}
        {preset.type === "card_frame" && (
          <div className="w-full h-full rounded-lg bg-[#14161B] flex flex-col items-center justify-center p-1.5">
            <div className="w-full h-[70%] rounded-xl bg-[#8A8F98] border-2 border-black/40 shadow-lg flex items-center justify-center">
              <span className="font-mono text-[8px] text-[#111] font-bold">FRAME</span>
            </div>
          </div>
        )}

        {/* LAYOUT 7: Stacked */}
        {preset.type === "stacked" && (
          <div className="w-full h-full flex flex-col gap-1">
            <div className="w-full h-[48%] rounded-md bg-[#8A8F98] flex items-center justify-center">
              <span className="font-mono text-[8px] text-[#111] font-bold">SPEAKER</span>
            </div>
            <div className="w-full h-[52%] rounded-md bg-[#2B303A] flex items-center justify-center">
              <span className="font-mono text-[8px] text-[#999] font-bold">FOOTAGE</span>
            </div>
          </div>
        )}

        {/* LAYOUT 8: Picture in Picture */}
        {preset.type === "pip" && (
          <div className="w-full h-full rounded-lg bg-[#3D424D] relative flex items-center justify-center p-1">
            <span className="font-mono text-[8px] text-[#999] font-bold">MAIN BG</span>
            <div className="absolute bottom-2 right-2 w-10 h-14 rounded-md bg-[#8A8F98] border border-white shadow-md flex items-center justify-center">
              <span className="font-mono text-[7px] text-[#111] font-bold">PIP</span>
            </div>
          </div>
        )}

        {/* Selection Dot */}
        {isSelected && (
          <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#3B82F6] shadow-[0_0_6px_#3B82F6]"></div>
        )}
      </div>

      {/* Label under card */}
      <span
        className={`font-sans text-xs font-medium text-center transition-colors ${
          isSelected ? "text-[#3B82F6] font-bold" : "text-neutral-400 group-hover:text-neutral-200"
        }`}
      >
        {preset.name}
      </span>
    </div>
  );
};

