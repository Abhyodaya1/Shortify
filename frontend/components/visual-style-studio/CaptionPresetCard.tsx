"use client";

import React from "react";
import { CaptionPreset } from "./types";

interface Props {
  preset: CaptionPreset;
  isSelected: boolean;
  onSelect: (preset: CaptionPreset) => void;
}

export const CaptionPresetCard: React.FC<Props> = ({ preset, isSelected, onSelect }) => {
  return (
    <div
      onClick={() => onSelect(preset)}
      className={`relative p-3.5 sm:p-4 rounded-xl border-2 transition-all cursor-pointer flex flex-col justify-between select-none min-h-[96px] ${
        isSelected
          ? "bg-[#181B20] border-[#3B82F6] shadow-[0_0_12px_rgba(59,130,246,0.35)] translate-y-[-1px]"
          : "bg-[#121418] border-[#222730] hover:border-[#384152] hover:bg-[#161920]"
      }`}
    >
      {/* Visual WordArt Typography Render */}
      <div className="flex items-center justify-center py-1">
        {preset.id === "bold_impact" && (
          <span className="font-headline font-black text-lg tracking-wider text-white uppercase drop-shadow-[0_2px_0_#000]">
            BOLD <span className="text-[#FFE600] underline decoration-[#FFE600] decoration-2">IMPACT</span>
          </span>
        )}

        {preset.id === "neon_glow" && (
          <span
            className="font-headline font-black text-lg tracking-wider text-[#00FFFF] uppercase"
            style={{
              WebkitTextStroke: "1px #000000",
              textShadow: "0 0 6px rgba(0,255,255,0.7), 1px 1px 0 #000",
            }}
          >
            NEON <span className="text-white">GLOW</span>
          </span>
        )}

        {preset.id === "3d_depth" && (
          <span
            className="font-headline font-black text-lg tracking-wider text-white uppercase"
            style={{
              WebkitTextStroke: "1px #000000",
              textShadow: "1px 1px 0 #000, 2px 2px 0 #000, 3px 3px 0 #D5EB45",
            }}
          >
            3D DEPTH
          </span>
        )}

        {preset.id === "cinematic" && (
          <span
            className="font-sans font-bold text-base tracking-widest text-[#F8FAFC] uppercase"
            style={{
              WebkitTextStroke: "0.8px #000000",
              textShadow: "0 2px 4px rgba(0,0,0,0.8)",
            }}
          >
            CINEMATIC
          </span>
        )}

        {preset.id === "gradient_wordart" && (
          <span
            className="font-headline font-black text-lg tracking-wider uppercase bg-gradient-to-r from-[#FFE600] to-[#FF6B00] bg-clip-text text-transparent"
            style={{
              WebkitTextStroke: "0.8px #000000",
              filter: "drop-shadow(0 2px 0 #000)",
            }}
          >
            GRADIENT POP
          </span>
        )}

        {preset.id === "minimal_modern" && (
          <span
            className="font-sans font-black text-base tracking-wide text-white uppercase"
            style={{
              WebkitTextStroke: "0.8px #000000",
              textShadow: "0 1px 2px #000",
            }}
          >
            MINIMAL <span className="text-[#38BDF8]">AZURE</span>
          </span>
        )}

        {preset.id === "karaoke_highlight" && (
          <span
            className="font-sans font-black text-base tracking-wider text-neutral-200 uppercase"
            style={{ WebkitTextStroke: "0.8px #000000" }}
          >
            KARAOKE <span className="text-[#D5EB45] drop-shadow-[0_1px_0_#000]">SYNC</span>
          </span>
        )}

        {preset.id === "comic_pop" && (
          <span
            className="font-headline font-black text-lg tracking-wider text-[#FFE600] uppercase transform -rotate-2"
            style={{
              WebkitTextStroke: "1px #000000",
              textShadow: "2px 2px 0 #000, 3px 3px 0 #FF2A85",
            }}
          >
            COMIC POP!
          </span>
        )}

        {preset.id === "typewriter" && (
          <span
            className="font-mono font-bold text-sm tracking-wider text-[#22C55E]"
            style={{
              WebkitTextStroke: "0.6px #000000",
              textShadow: "0 0 4px rgba(34,197,94,0.4)",
            }}
          >
            &gt; TYPEWRITER_
          </span>
        )}

        {preset.id === "creator_hormozi" && (
          <span className="font-headline font-black text-lg tracking-wider text-white uppercase drop-shadow-[0_2px_0_#000]">
            HORMOZI <span className="text-[#D5EB45] px-1 bg-black/80 border border-[#D5EB45]">POP</span>
          </span>
        )}
      </div>

      {/* Footer Info & Selected Badge */}
      <div className="flex items-center justify-between pt-1 border-t border-[#222730]/60 mt-1">
        <span className="font-sans text-[11px] text-neutral-400 truncate">
          {preset.description}
        </span>
        {isSelected && (
          <span className="font-mono text-[9px] px-1.5 py-0.5 rounded-md bg-[#00E297]/15 border border-[#00E297]/40 text-[#00E297] font-bold">
            Selected
          </span>
        )}
      </div>
    </div>
  );
};

